/**
 * Image Proxy Route
 *
 * Solves CORS issues by fetching images server-side and forwarding them.
 * Usage: GET /api/image-proxy?url=https://example.com/image.jpg
 *
 * Public (shared boards use it without login), so it only fetches public
 * addresses, follows at most 3 redirects, and only returns non-SVG images up to 5 MB.
 */

import { lookup } from 'node:dns/promises';
import { BlockList, isIP } from 'node:net';
import { NextRequest, NextResponse } from 'next/server';

const MAX_BYTES = 5 * 1024 * 1024;
const MAX_REDIRECTS = 3;

// Private, loopback, link-local and other internal ranges
const blockedAddresses = new BlockList();
blockedAddresses.addSubnet('0.0.0.0', 8, 'ipv4');
blockedAddresses.addSubnet('127.0.0.0', 8, 'ipv4');
blockedAddresses.addSubnet('10.0.0.0', 8, 'ipv4');
blockedAddresses.addSubnet('172.16.0.0', 12, 'ipv4');
blockedAddresses.addSubnet('192.168.0.0', 16, 'ipv4');
blockedAddresses.addSubnet('169.254.0.0', 16, 'ipv4');
blockedAddresses.addSubnet('100.64.0.0', 10, 'ipv4'); // carrier-grade NAT
blockedAddresses.addSubnet('192.0.0.0', 24, 'ipv4');
blockedAddresses.addSubnet('198.18.0.0', 15, 'ipv4');
blockedAddresses.addSubnet('224.0.0.0', 3, 'ipv4'); // multicast + reserved
blockedAddresses.addAddress('::', 'ipv6');
blockedAddresses.addSubnet('64:ff9b::', 96, 'ipv6'); // NAT64
blockedAddresses.addSubnet('2002::', 16, 'ipv6'); // 6to4
blockedAddresses.addAddress('::1', 'ipv6');
blockedAddresses.addSubnet('fc00::', 7, 'ipv6');
blockedAddresses.addSubnet('fe80::', 10, 'ipv6');

async function isPublicHost(hostname: string): Promise<boolean> {
  const host = hostname.replace(/^\[|\]$/g, '');
  const addresses = isIP(host)
    ? [host]
    : (await lookup(host, { all: true })).map((a) => a.address);
  return addresses.every(
    (address) => !blockedAddresses.check(address, isIP(address) === 6 ? 'ipv6' : 'ipv4')
  );
}

function error(message: string, status: number) {
  return NextResponse.json({ error: message }, { status });
}

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const imageUrl = searchParams.get('url');

  if (!imageUrl) {
    return error('Missing url parameter', 400);
  }

  try {
    let url = new URL(imageUrl);
    let response: Response;

    // Follow redirects manually so every hop gets the address check
    for (let hop = 0; ; hop++) {
      // Only allow http/https protocols
      if (!['http:', 'https:'].includes(url.protocol)) {
        return error('Invalid URL protocol', 400);
      }
      if (!(await isPublicHost(url.hostname))) {
        return error('Address not allowed', 403);
      }

      // Fetch the image with browser-like headers (needed for CDNs like bstatic.com)
      response = await fetch(url.href, {
        redirect: 'manual',
        headers: {
          'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
          'Accept': 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8',
          'Referer': url.origin + '/',
        },
      });

      const location = response.headers.get('location');
      if (response.status < 300 || response.status >= 400 || !location) break;
      if (hop === MAX_REDIRECTS) {
        return error('Too many redirects', 502);
      }
      url = new URL(location, url);
    }

    if (!response.ok) {
      return error(`Failed to fetch image: ${response.status}`, response.status);
    }

    const contentType = (response.headers.get('content-type') || '').toLowerCase();
    if (!contentType.startsWith('image/') || contentType.startsWith('image/svg')) {
      return error('Not an image', 415);
    }

    if (Number(response.headers.get('content-length')) > MAX_BYTES) {
      return error('Image too large', 413);
    }

    // Read the body, aborting once it exceeds the size cap
    const chunks: Uint8Array<ArrayBuffer>[] = [];
    let size = 0;
    const reader = response.body?.getReader();
    while (reader) {
      const { done, value } = await reader.read();
      if (done) break;
      size += value.byteLength;
      if (size > MAX_BYTES) {
        await reader.cancel();
        return error('Image too large', 413);
      }
      chunks.push(value);
    }

    return new NextResponse(new Blob(chunks), {
      status: 200,
      headers: {
        'Content-Type': contentType,
        'Cache-Control': 'public, max-age=86400', // Cache for 24 hours
      },
    });
  } catch (err) {
    console.error('[Image Proxy] Error:', err);
    return error('Failed to proxy image', 500);
  }
}

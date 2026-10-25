import { beforeEach, describe, expect, it, vi } from 'vitest';
import { NextRequest } from 'next/server';
import { lookup } from 'node:dns/promises';
import { GET } from './route';

vi.mock('node:dns/promises', () => ({ lookup: vi.fn() }));

const mockLookup = vi.mocked(lookup) as unknown as ReturnType<typeof vi.fn>;
const mockFetch = vi.fn();

// Hostname -> resolved address
const dns: Record<string, string> = {
  'images.example.com': '93.184.216.34',
  'cdn.example.com': '93.184.216.35',
  'internal.example.com': '10.0.0.5',
};

function proxy(url: string) {
  return GET(new NextRequest(`http://localhost/api/image-proxy?url=${encodeURIComponent(url)}`));
}

function image(body: BodyInit = 'png-bytes', headers: Record<string, string> = {}) {
  return new Response(body, { status: 200, headers: { 'content-type': 'image/png', ...headers } });
}

function redirect(location: string) {
  return new Response(null, { status: 302, headers: { location } });
}

beforeEach(() => {
  mockLookup.mockReset();
  mockLookup.mockImplementation(async (hostname: string) => {
    const address = dns[hostname];
    if (!address) throw new Error('ENOTFOUND');
    return [{ address, family: 4 }];
  });
  mockFetch.mockReset();
  vi.stubGlobal('fetch', mockFetch);
});

describe('image proxy', () => {
  it('passes through a normal image', async () => {
    mockFetch.mockResolvedValueOnce(image('png-bytes'));

    const res = await proxy('https://images.example.com/a.png');

    expect(res.status).toBe(200);
    expect(res.headers.get('content-type')).toBe('image/png');
    expect(res.headers.get('access-control-allow-origin')).toBeNull();
    expect(await res.text()).toBe('png-bytes');
  });

  it.each([
    'http://127.0.0.1/a.png',
    'http://10.1.2.3/a.png',
    'http://172.16.0.1/a.png',
    'http://192.168.1.1/a.png',
    'http://169.254.169.254/latest/meta-data',
    'http://0.0.0.0/a.png',
    'http://[::1]/a.png',
    'http://[fd00::1]/a.png',
    'http://[fe80::1]/a.png',
    'http://[::ffff:127.0.0.1]/a.png',
    'http://100.64.0.1/a.png',
    'http://198.18.0.1/a.png',
    'http://224.0.0.1/a.png',
    'http://[64:ff9b::a00:1]/a.png',
    'http://[2002:a00:1::]/a.png',
    'http://internal.example.com/a.png',
  ])('blocks internal address %s', async (url) => {
    const res = await proxy(url);

    expect(res.status).toBe(403);
    expect(mockFetch).not.toHaveBeenCalled();
  });

  it('follows a redirect to a public host', async () => {
    mockFetch
      .mockResolvedValueOnce(redirect('https://cdn.example.com/b.png'))
      .mockResolvedValueOnce(image());

    const res = await proxy('https://images.example.com/a.png');

    expect(res.status).toBe(200);
    expect(mockFetch).toHaveBeenCalledTimes(2);
    expect(mockFetch.mock.calls[1][0]).toBe('https://cdn.example.com/b.png');
  });

  it('blocks a redirect to an internal address', async () => {
    mockFetch.mockResolvedValueOnce(redirect('http://169.254.169.254/latest/meta-data'));

    const res = await proxy('https://images.example.com/a.png');

    expect(res.status).toBe(403);
    expect(mockFetch).toHaveBeenCalledTimes(1);
  });

  it('gives up after 3 redirects', async () => {
    mockFetch.mockImplementation(async () => redirect('https://cdn.example.com/loop.png'));

    const res = await proxy('https://images.example.com/a.png');

    expect(res.status).toBe(502);
    expect(mockFetch).toHaveBeenCalledTimes(4);
  });

  it('rejects non-image content', async () => {
    mockFetch.mockResolvedValueOnce(image('<html>', { 'content-type': 'text/html' }));

    const res = await proxy('https://images.example.com/a.png');

    expect(res.status).toBe(415);
  });

  it('rejects SVG', async () => {
    mockFetch.mockResolvedValueOnce(image('<svg/>', { 'content-type': 'image/svg+xml' }));

    const res = await proxy('https://images.example.com/a.svg');

    expect(res.status).toBe(415);
  });

  it('rejects an image larger than 5 MB', async () => {
    mockFetch.mockResolvedValueOnce(image(new Uint8Array(5 * 1024 * 1024 + 1)));

    const res = await proxy('https://images.example.com/huge.png');

    expect(res.status).toBe(413);
  });

  it('rejects early when content-length is over 5 MB', async () => {
    mockFetch.mockResolvedValueOnce(image('small', { 'content-length': String(10 * 1024 * 1024) }));

    const res = await proxy('https://images.example.com/huge.png');

    expect(res.status).toBe(413);
  });
});

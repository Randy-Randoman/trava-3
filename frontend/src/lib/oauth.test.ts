import { describe, expect, it } from 'vitest';
import { hostOf, safeNextPath } from './oauth';

describe('hostOf', () => {
  it('returns the host of a URL', () => {
    expect(hostOf('https://claude.ai/api/mcp/auth_callback?x=1')).toBe('claude.ai');
    expect(hostOf('http://localhost:33418/callback')).toBe('localhost:33418');
  });

  it('returns null for an empty or unparsable URL', () => {
    expect(hostOf('')).toBeNull();
    expect(hostOf('not a url')).toBeNull();
  });
});

describe('safeNextPath', () => {
  it('keeps a same-site path with its query', () => {
    expect(safeNextPath('/oauth/consent?authorization_id=abc')).toBe('/oauth/consent?authorization_id=abc');
  });

  it('falls back to the dashboard for anything that could leave the site', () => {
    expect(safeNextPath(null)).toBe('/dashboard');
    expect(safeNextPath('https://evil.test')).toBe('/dashboard');
    expect(safeNextPath('//evil.test')).toBe('/dashboard');
    expect(safeNextPath('/\\evil.test')).toBe('/dashboard');
  });
});

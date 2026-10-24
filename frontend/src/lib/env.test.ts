import { afterEach, describe, expect, it, vi } from 'vitest';
import { env } from './env';

afterEach(() => vi.unstubAllEnvs());

describe('env', () => {
  it('returns the variable when set', () => {
    vi.stubEnv('NEXT_PUBLIC_BACKEND_URL', 'http://api.test');
    expect(env.backendUrl()).toBe('http://api.test');
  });

  it('throws naming the variable when missing', () => {
    vi.stubEnv('NEXT_PUBLIC_SUPABASE_ANON_KEY', '');
    expect(() => env.supabaseAnonKey()).toThrow('NEXT_PUBLIC_SUPABASE_ANON_KEY');
  });
});

import { afterEach, describe, expect, it, vi } from 'vitest';

vi.mock('./supabase/client', () => ({
  supabase: { auth: { getSession: async () => ({ data: { session: null } }) } },
}));
vi.mock('./env', () => ({ env: { backendUrl: () => 'http://api' } }));

import { CanvasConflictError, saveCanvasState } from './api';

afterEach(() => vi.unstubAllGlobals());

describe('saveCanvasState', () => {
  it('sends base_version with the canvas', async () => {
    const fetchMock = vi.fn(async () => new Response(JSON.stringify({ last_modified: 'v2' })));
    vi.stubGlobal('fetch', fetchMock);

    const saved = await saveCanvasState('t1', [], {}, 'v1');

    const body = JSON.parse((fetchMock.mock.calls[0] as unknown as [string, RequestInit])[1].body as string);
    expect(body.base_version).toBe('v1');
    expect(saved.last_modified).toBe('v2');
  });

  it('throws CanvasConflictError on 409', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => new Response('{"detail":{}}', { status: 409 })));

    await expect(saveCanvasState('t1', [], {}, 'stale')).rejects.toBeInstanceOf(CanvasConflictError);
  });
});

import { describe, expect, it } from 'vitest';
import { parseSse } from './sse';

describe('parseSse', () => {
  it('reassembles an event split across three chunks', () => {
    let r = parseSse('', 'data: {"type":"te');
    expect(r.events).toEqual([]);
    r = parseSse(r.rest, 'xt","content":"hi');
    expect(r.events).toEqual([]);
    r = parseSse(r.rest, '"}\n\n');
    expect(r.events).toEqual([{ type: 'text', content: 'hi' }]);
    expect(r.rest).toBe('');
  });

  it('returns several events from one chunk', () => {
    const r = parseSse('', 'data: {"type":"status","content":"a"}\n\ndata: {"type":"done"}\n\n');
    expect(r.events).toEqual([{ type: 'status', content: 'a' }, { type: 'done' }]);
  });

  it('keeps a trailing partial line for the next chunk', () => {
    const r = parseSse('', 'data: {"type":"done"}\n\ndata: {"ty');
    expect(r.events).toEqual([{ type: 'done' }]);
    expect(r.rest).toBe('data: {"ty');
  });
});

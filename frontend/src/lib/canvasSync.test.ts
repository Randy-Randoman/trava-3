import { describe, expect, it } from 'vitest';
import { shouldReload } from './canvasSync';

describe('shouldReload', () => {
  const known = '2026-01-01T10:00:00.123456+00:00';

  it('reloads when the event version is newer', () => {
    expect(shouldReload('2026-01-01T10:00:05.000000+00:00', known)).toBe(true);
  });

  it('ignores the echo of our own save', () => {
    expect(shouldReload(known, known)).toBe(false);
  });

  it('ignores an older version', () => {
    expect(shouldReload('2026-01-01T09:59:59.999999+00:00', known)).toBe(false);
  });

  it('treats Realtime and PostgREST formats of the same instant as equal', () => {
    expect(shouldReload('2026-01-01 10:00:00.123456+00', known)).toBe(false);
  });

  it('reloads on a write within the same millisecond (microsecond precision)', () => {
    expect(shouldReload('2026-01-01 10:00:00.123457+00', known)).toBe(true);
  });

  it('compares across time zone offsets and fraction lengths', () => {
    expect(shouldReload('2026-01-01T12:00:00.1234560+02:00', known)).toBe(false);
    expect(shouldReload('2026-01-01T10:00:00.12+00:00', '2026-01-01T10:00:00.120000Z')).toBe(false);
    expect(shouldReload('2026-01-01T10:00:00+00:00', '2026-01-01T09:00:00Z')).toBe(true);
  });

  it('reloads when either version is unknown or unparseable', () => {
    expect(shouldReload(known, null)).toBe(true);
    expect(shouldReload(undefined, known)).toBe(true);
    expect(shouldReload('garbage', known)).toBe(true);
  });
});

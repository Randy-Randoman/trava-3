/**
 * Live board sync: should a Realtime change event reload the canvas?
 *
 * Versions are canvas_states.last_modified timestamps. PostgREST sends
 * `2026-01-01T10:00:00.123456+00:00`, Realtime may send `2026-01-01 10:00:00.123456+00`,
 * so compare as instants, at Postgres' microsecond precision: JS Date stops at
 * milliseconds and would mistake a second write in the same millisecond for our own save.
 */

// Microseconds since the epoch, or NaN if unparseable
function toMicros(ts: string): number {
  const m = ts.match(/^(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2}:\d{2})(?:\.(\d+))?(Z|[+-]\d{2}(?::\d{2})?)$/)
  if (!m) return NaN
  const [, date, time, fraction = '', zone] = m
  const offset = zone === 'Z' ? 'Z' : zone.length === 3 ? `${zone}:00` : zone
  const micros = Number(fraction.padEnd(6, '0').slice(0, 6))
  return Date.parse(`${date}T${time}${offset}`) * 1000 + micros
}

// Reload unless the event is provably our own save or older; when unsure, reload
export function shouldReload(eventVersion: string | null | undefined, knownVersion: string | null): boolean {
  if (!eventVersion || !knownVersion) return true
  const event = toMicros(eventVersion)
  const known = toMicros(knownVersion)
  if (Number.isNaN(event) || Number.isNaN(known)) return true
  return event > known
}

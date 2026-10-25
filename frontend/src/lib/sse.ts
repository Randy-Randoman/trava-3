/**
 * Parse Server-Sent Events from a stream that arrives in arbitrary chunks.
 * Only complete lines are parsed; a trailing partial line is returned as
 * `rest` and must be passed back in with the next chunk.
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function parseSse(rest: string, chunk: string): { events: any[]; rest: string } {
  const lines = (rest + chunk).split('\n')
  const remainder = lines.pop() ?? ''
  const events = lines
    .filter((line) => line.startsWith('data: '))
    .map((line) => JSON.parse(line.slice(6)))
  return { events, rest: remainder }
}

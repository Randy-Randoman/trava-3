-- Live board updates (#57): stream canvas_states changes to open boards via Supabase Realtime.
-- The owner-only SELECT policy (migration 002) limits events to the board's owner.
ALTER PUBLICATION supabase_realtime ADD TABLE public.canvas_states;

-- Add board_items column to trips table
-- Tracks what the agent has placed on the Excalidraw canvas
ALTER TABLE trips ADD COLUMN IF NOT EXISTS board_items JSONB DEFAULT '[]'::jsonb;

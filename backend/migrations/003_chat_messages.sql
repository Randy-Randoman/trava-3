-- TRAVA 2.0 Chat Messages Table (Wave 3)
-- Run this AFTER 002_rls_policies.sql in Supabase SQL Editor
-- ================================================
-- Adds persistent chat message storage with context caching support

-- ================================================
-- Table: chat_messages
-- Stores chat conversation history for each trip
-- ================================================
CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    trip_id UUID NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'model')), -- CRITICAL: Gemini uses 'user' and 'model'
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for fast history retrieval (ordered by time)
CREATE INDEX IF NOT EXISTS idx_chat_messages_trip_id_created_at
    ON chat_messages(trip_id, created_at);

-- ================================================
-- Add cache_name to trips table
-- Stores Gemini context cache reference for token optimization
-- ================================================
ALTER TABLE trips ADD COLUMN IF NOT EXISTS cache_name TEXT;

-- ================================================
-- RLS Policies for chat_messages
-- ================================================
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;

-- Users can view messages for their own trips
CREATE POLICY "Users can view own chat messages"
    ON chat_messages FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM trips
            WHERE trips.id = chat_messages.trip_id
            AND trips.user_id = auth.uid()
        )
    );

-- Users can insert messages for their own trips
CREATE POLICY "Users can insert chat messages for own trips"
    ON chat_messages FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM trips
            WHERE trips.id = chat_messages.trip_id
            AND trips.user_id = auth.uid()
        )
    );

-- Users can delete messages for their own trips
CREATE POLICY "Users can delete own chat messages"
    ON chat_messages FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM trips
            WHERE trips.id = chat_messages.trip_id
            AND trips.user_id = auth.uid()
        )
    );

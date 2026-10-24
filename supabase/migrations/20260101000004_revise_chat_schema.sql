-- TRAVA 2.0 Chat Schema Revision (Wave 3 - Revised)
-- Run this to migrate from single-table to two-table architecture
-- ================================================
-- Revises chat persistence to use two-table design for better performance

-- ================================================
-- Step 1: Drop the old single-table schema
-- ================================================
DROP POLICY IF EXISTS "Users can delete own chat messages" ON chat_messages;
DROP POLICY IF EXISTS "Users can insert chat messages for own trips" ON chat_messages;
DROP POLICY IF EXISTS "Users can view own chat messages" ON chat_messages;

DROP INDEX IF EXISTS idx_chat_messages_trip_id_created_at;
DROP TABLE IF EXISTS chat_messages;

-- Remove cache_name from trips (will be in conversations instead)
ALTER TABLE trips DROP COLUMN IF EXISTS cache_name;

-- ================================================
-- Step 2: Create conversations table
-- Stores conversation metadata (for sidebar, search, analytics)
-- ================================================
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    trip_id UUID NOT NULL UNIQUE REFERENCES trips(id) ON DELETE CASCADE,
    title TEXT,
    cache_name TEXT, -- Gemini context cache reference for token optimization
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for fast conversation lookups by trip
CREATE INDEX IF NOT EXISTS idx_conversations_trip_id ON conversations(trip_id);

-- ================================================
-- Step 3: Create messages table
-- Stores individual chat messages (optimized for RAG/Vector search)
-- ================================================
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'model')), -- CRITICAL: Gemini uses 'user' and 'model'
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for fast message history retrieval (ordered by time)
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id_created_at
    ON messages(conversation_id, created_at);

-- ================================================
-- Step 4: Trigger - Auto-update updated_at on conversations
-- ================================================
DROP TRIGGER IF EXISTS update_conversations_updated_at ON conversations;
CREATE TRIGGER update_conversations_updated_at
    BEFORE UPDATE ON conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ================================================
-- Step 5: RLS Policies for conversations
-- ================================================
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;

-- Users can view their own conversations
CREATE POLICY "Users can view own conversations"
    ON conversations FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM trips
            WHERE trips.id = conversations.trip_id
            AND trips.user_id = auth.uid()
        )
    );

-- Users can insert conversations for their own trips
CREATE POLICY "Users can insert conversations for own trips"
    ON conversations FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM trips
            WHERE trips.id = conversations.trip_id
            AND trips.user_id = auth.uid()
        )
    );

-- Users can update their own conversations
CREATE POLICY "Users can update own conversations"
    ON conversations FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM trips
            WHERE trips.id = conversations.trip_id
            AND trips.user_id = auth.uid()
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM trips
            WHERE trips.id = conversations.trip_id
            AND trips.user_id = auth.uid()
        )
    );

-- Users can delete their own conversations
CREATE POLICY "Users can delete own conversations"
    ON conversations FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM trips
            WHERE trips.id = conversations.trip_id
            AND trips.user_id = auth.uid()
        )
    );

-- ================================================
-- Step 6: RLS Policies for messages
-- ================================================
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- Users can view messages for their own conversations
CREATE POLICY "Users can view own messages"
    ON messages FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM conversations
            JOIN trips ON trips.id = conversations.trip_id
            WHERE conversations.id = messages.conversation_id
            AND trips.user_id = auth.uid()
        )
    );

-- Users can insert messages for their own conversations
CREATE POLICY "Users can insert messages for own conversations"
    ON messages FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM conversations
            JOIN trips ON trips.id = conversations.trip_id
            WHERE conversations.id = messages.conversation_id
            AND trips.user_id = auth.uid()
        )
    );

-- Users can delete their own messages
CREATE POLICY "Users can delete own messages"
    ON messages FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM conversations
            JOIN trips ON trips.id = conversations.trip_id
            WHERE conversations.id = messages.conversation_id
            AND trips.user_id = auth.uid()
        )
    );

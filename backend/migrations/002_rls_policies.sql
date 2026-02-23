-- TRAVA 2.0 Row Level Security Policies (Wave 2)
-- Run this AFTER 001_initial_schema.sql in Supabase SQL Editor
-- ================================================

-- ================================================
-- Enable RLS on all tables
-- ================================================
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE trips ENABLE ROW LEVEL SECURITY;
ALTER TABLE canvas_states ENABLE ROW LEVEL SECURITY;

-- ================================================
-- Profiles Policies
-- ================================================

-- Users can view their own profile
CREATE POLICY "Users can view own profile"
    ON profiles FOR SELECT
    USING (auth.uid() = id);

-- Users can update their own profile
CREATE POLICY "Users can update own profile"
    ON profiles FOR UPDATE
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

-- Users can insert their own profile (handled by trigger, but just in case)
CREATE POLICY "Users can insert own profile"
    ON profiles FOR INSERT
    WITH CHECK (auth.uid() = id);

-- ================================================
-- Trips Policies
-- ================================================

-- Users can view their own trips
CREATE POLICY "Users can view own trips"
    ON trips FOR SELECT
    USING (auth.uid() = user_id);

-- Users can create their own trips
CREATE POLICY "Users can create own trips"
    ON trips FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Users can update their own trips
CREATE POLICY "Users can update own trips"
    ON trips FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Users can delete their own trips
CREATE POLICY "Users can delete own trips"
    ON trips FOR DELETE
    USING (auth.uid() = user_id);

-- Anyone with a valid share_token can view the trip (for sharing feature)
CREATE POLICY "Anyone can view shared trips"
    ON trips FOR SELECT
    USING (share_token IS NOT NULL);

-- ================================================
-- Canvas States Policies
-- ================================================

-- Users can view canvas states for their own trips
CREATE POLICY "Users can view own canvas states"
    ON canvas_states FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM trips
            WHERE trips.id = canvas_states.trip_id
            AND trips.user_id = auth.uid()
        )
    );

-- Users can update canvas states for their own trips
CREATE POLICY "Users can update own canvas states"
    ON canvas_states FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM trips
            WHERE trips.id = canvas_states.trip_id
            AND trips.user_id = auth.uid()
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM trips
            WHERE trips.id = canvas_states.trip_id
            AND trips.user_id = auth.uid()
        )
    );

-- Canvas states are auto-created by trigger, but allow insert for trip owners
CREATE POLICY "Users can insert canvas states for own trips"
    ON canvas_states FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM trips
            WHERE trips.id = canvas_states.trip_id
            AND trips.user_id = auth.uid()
        )
    );

-- Users can delete canvas states for their own trips
CREATE POLICY "Users can delete own canvas states"
    ON canvas_states FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM trips
            WHERE trips.id = canvas_states.trip_id
            AND trips.user_id = auth.uid()
        )
    );

-- Anyone with access to a shared trip can view its canvas
CREATE POLICY "Anyone can view canvas for shared trips"
    ON canvas_states FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM trips
            WHERE trips.id = canvas_states.trip_id
            AND trips.share_token IS NOT NULL
        )
    );

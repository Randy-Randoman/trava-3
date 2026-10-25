-- TRAVA 2.0 Database Schema (Wave 2)
-- Run this in Supabase SQL Editor
-- ================================================

-- Enable UUID extension (usually enabled by default in Supabase)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ================================================
-- Table: profiles
-- Extends Supabase Auth with user profile data
-- ================================================
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    username TEXT UNIQUE,
    avatar_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for username lookups
CREATE INDEX IF NOT EXISTS idx_profiles_username ON profiles(username);

-- ================================================
-- Table: trips
-- Stores trip metadata
-- ================================================
CREATE TABLE IF NOT EXISTS trips (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    title TEXT NOT NULL DEFAULT 'Untitled Trip',
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'archived')),
    destination TEXT,
    start_date DATE,
    end_date DATE,
    budget DECIMAL(10, 2),
    currency TEXT DEFAULT 'USD',
    travelers INTEGER DEFAULT 1,
    vibe TEXT,
    share_token TEXT UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_trips_user_id ON trips(user_id);
CREATE INDEX IF NOT EXISTS idx_trips_status ON trips(status);
CREATE INDEX IF NOT EXISTS idx_trips_share_token ON trips(share_token);

-- ================================================
-- Table: canvas_states
-- Stores Excalidraw scene data as JSONB
-- ================================================
CREATE TABLE IF NOT EXISTS canvas_states (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    trip_id UUID NOT NULL UNIQUE REFERENCES trips(id) ON DELETE CASCADE,
    scene_elements JSONB DEFAULT '[]'::jsonb,
    scene_files JSONB DEFAULT '{}'::jsonb,
    scene_app_state JSONB DEFAULT '{}'::jsonb,
    last_modified TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for trip_id lookups
CREATE INDEX IF NOT EXISTS idx_canvas_states_trip_id ON canvas_states(trip_id);

-- ================================================
-- Function: Auto-update updated_at timestamp
-- ================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to profiles
DROP TRIGGER IF EXISTS update_profiles_updated_at ON profiles;
CREATE TRIGGER update_profiles_updated_at
    BEFORE UPDATE ON profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Apply trigger to trips
DROP TRIGGER IF EXISTS update_trips_updated_at ON trips;
CREATE TRIGGER update_trips_updated_at
    BEFORE UPDATE ON trips
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ================================================
-- Function: Auto-update last_modified timestamp
-- ================================================
CREATE OR REPLACE FUNCTION update_last_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_modified = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to canvas_states
DROP TRIGGER IF EXISTS update_canvas_states_last_modified ON canvas_states;
CREATE TRIGGER update_canvas_states_last_modified
    BEFORE UPDATE ON canvas_states
    FOR EACH ROW
    EXECUTE FUNCTION update_last_modified_column();

-- ================================================
-- Function: Auto-create profile on user signup
-- ================================================
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO profiles (id, username, avatar_url)
    VALUES (
        NEW.id,
        NEW.raw_user_meta_data->>'username',
        NEW.raw_user_meta_data->>'avatar_url'
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Apply trigger to auth.users
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION handle_new_user();

-- ================================================
-- Function: Auto-create canvas_state on trip creation
-- ================================================
CREATE OR REPLACE FUNCTION handle_new_trip()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO canvas_states (trip_id)
    VALUES (NEW.id);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to trips
DROP TRIGGER IF EXISTS on_trip_created ON trips;
CREATE TRIGGER on_trip_created
    AFTER INSERT ON trips
    FOR EACH ROW
    EXECUTE FUNCTION handle_new_trip();

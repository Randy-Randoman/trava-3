-- Add is_approved column to profiles
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS is_approved BOOLEAN DEFAULT false;

-- Approve all existing users
UPDATE profiles SET is_approved = true WHERE is_approved IS NULL OR is_approved = false;

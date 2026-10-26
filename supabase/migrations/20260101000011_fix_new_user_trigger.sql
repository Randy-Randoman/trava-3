-- Sign-up failed on fresh installs: Supabase Auth runs the auth.users trigger with its own
-- search_path, where the unqualified "profiles" in handle_new_user (migration 001) doesn't
-- resolve ("relation profiles does not exist" → "Database error saving new user").
-- Same function, with a fixed search_path and a schema-qualified table.

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
BEGIN
    INSERT INTO public.profiles (id, username, avatar_url)
    VALUES (
        NEW.id,
        NEW.raw_user_meta_data->>'username',
        NEW.raw_user_meta_data->>'avatar_url'
    );
    RETURN NEW;
END;
$$;

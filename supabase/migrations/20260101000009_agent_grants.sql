-- OAuth 2.1 for agents (#54): is a user's grant to an OAuth client still active?
-- The backend's require_agent calls this on every agent request, so revoking a
-- connected app takes effect at once, not when its access token expires.
-- Active = consent not revoked, client not deleted, and the token's session still exists.
-- plpgsql so the auth.oauth_* tables are only resolved when it runs.

CREATE FUNCTION public.agent_grant_active(p_user uuid, p_client uuid, p_session uuid)
RETURNS boolean
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = ''
AS $$
BEGIN
  RETURN EXISTS (
    SELECT 1
    FROM auth.oauth_consents g
    JOIN auth.oauth_clients c ON c.id = g.client_id AND c.deleted_at IS NULL
    JOIN auth.sessions s ON s.user_id = g.user_id AND s.oauth_client_id = g.client_id
    WHERE g.user_id = p_user
      AND g.client_id = p_client
      AND s.id = p_session
      AND g.revoked_at IS NULL
      AND (s.not_after IS NULL OR s.not_after > now())
  );
END;
$$;

REVOKE EXECUTE ON FUNCTION public.agent_grant_active(uuid, uuid, uuid) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.agent_grant_active(uuid, uuid, uuid) TO service_role;

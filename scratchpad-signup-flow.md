# Sign-Up Flow Implementation

## Flow

```
Sign Up → Email Confirmation → Auth Callback → Pending Approval → Dashboard
```

Individual users only. No onboarding. Email + password via Supabase Auth.

## What already exists

| File | What it does |
|------|-------------|
| `frontend/src/app/login/page.tsx` | Login page — email + password, Trava brutalist styling |
| `frontend/src/lib/auth/AuthContext.tsx` | `useAuth` hook — `signIn`, `signOut`, session/user state, `onAuthStateChange` |
| `frontend/src/lib/auth/index.ts` | Re-exports `AuthProvider`, `useAuth` |
| `frontend/src/components/auth/ProtectedRoute.tsx` | Redirects to `/login` if not authenticated |
| `frontend/src/lib/supabase/client.ts` | Supabase browser client |
| `backend/app/services/database.py` | Supabase service key client (bypasses RLS) |
| `backend/app/core/config.py` | Loads Supabase credentials |
| `backend/migrations/001_initial_schema.sql` | Profiles table with triggers |
| `backend/migrations/002_rls_policies.sql` | RLS policies tied to `auth.uid()` |

Auth is already enabled (`AUTH_ENABLED = true` in ProtectedRoute and home page).

## What needs to be built

### 1. Add `signUp` to AuthContext
In `frontend/src/lib/auth/AuthContext.tsx`:
- Add `signUp(email, password, fullName)` method that calls `supabase.auth.signUp()` with `full_name` in `options.data`
- Export it from the `useAuth` hook

### 2. `/signup` page
Create `frontend/src/app/signup/page.tsx`:
- Form: **Full Name**, **Email**, **Password**
- Use same brutalist styling as `/login` (border-4, shadow-brutal, adventure-orange button, etc.)
- On success: show "Check your email" confirmation message
- Link to `/login` at the bottom ("Already have an account? Sign in")

### 3. Add cross-links
- `/login` page: add "Don't have an account? Sign up" link pointing to `/signup`
- `/signup` page: add "Already have an account? Sign in" link pointing to `/login`

### 4. `/auth/callback` route
Create `frontend/src/app/auth/callback/route.ts`:
- Extract `code` from URL search params
- Call `supabase.auth.exchangeCodeForSession(code)`
- On success: redirect to `/dashboard`
- On failure: redirect to `/login`

Reference: BauShield's version at `/Users/hoeherp/development/playground/github/baushield/src/app/(auth)/auth/callback/route.ts`

### 5. `is_approved` migration
Create `backend/migrations/007_user_approval.sql`:
- Add `is_approved boolean DEFAULT false` column to `profiles` table
- Approval is manual for now (direct DB update: `UPDATE profiles SET is_approved = true WHERE id = '...'`)

### 6. `/pending-approval` page
Create `frontend/src/app/pending-approval/page.tsx`:
- "Your account is being reviewed" message
- "Check again" button (refreshes approval status)
- "Sign out" button
- Same brutalist styling as login/signup

Reference: BauShield's version at `/Users/hoeherp/development/playground/github/baushield/src/app/(auth)/pending-approval/page.tsx`

### 7. Approval check in ProtectedRoute
In `frontend/src/components/auth/ProtectedRoute.tsx`:
- After confirming user is authenticated, check `is_approved` on their profile
- If not approved: redirect to `/pending-approval`
- `/pending-approval` itself should NOT be wrapped in ProtectedRoute (or handle the loop)

### 8. Backend JWT validation
In FastAPI protected endpoints:
- Validate the Supabase JWT from the `Authorization: Bearer <token>` header
- Extract `user_id` from the token
- Check `is_approved` on the profile before allowing access

## Later (not part of this task)
- Trip sharing via invite links
- Multi-user board collaboration
- Social login (Google, Apple)

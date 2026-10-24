# Supabase setup

Trava uses Supabase for auth, Postgres, and storage. You'll create your own project — the free tier is plenty for local use.

## 1. Create a Supabase project

1. Sign up at [supabase.com](https://supabase.com) and create a new project.
2. Wait a minute for provisioning to finish.
3. In **Project Settings → API**, copy:
   - `Project URL` → goes into both `SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_URL`
   - `anon public` key → `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - `service_role` key → `SUPABASE_SERVICE_KEY` (keep this one private — never commit it)

Paste all four into your root `.env` file (copied from `.env.example`).

## 2. Run the migrations

Open the Supabase **SQL Editor** (in the left sidebar) and run each file from `backend/migrations/` in order:

1. `001_initial_schema.sql` — profiles, trips, canvas_states
2. `002_rls_policies.sql` — row-level security on the above
3. `003_chat_messages.sql` — chat history table
4. `004_revise_chat_schema.sql` — schema cleanup on chat_messages
5. `005_board_items.sql` — agent-managed board items
6. `006_canvas_images_bucket.sql` — storage bucket for canvas images (created automatically — no manual bucket setup)
7. `007_user_approval.sql` — legacy user-approval gate (removed again by the security cleanup migration)

Paste each file's contents into the SQL Editor, one at a time, and hit **Run**. Order matters — later migrations depend on earlier ones.

## 3. Configure auth

In **Authentication → Providers**, make sure **Email** is enabled. Set **Site URL** to `http://localhost:3000`. Optionally disable email confirmation while developing (**Authentication → Email**, turn off "Confirm email").

### Email delivery

Supabase's built-in email sender is rate-limited (~2 emails/hour on the free tier) — fine for solo testing, not for anything with multiple signups. For real use, configure a custom SMTP provider under **Authentication → Settings → SMTP**. Resend (`smtp.resend.com`, port 465, user `resend`, pass = your Resend API key) works well on a free tier; Mailgun / SES / Postmark work too. The credentials live in your Supabase dashboard, not in this repo.

## Known limitation

The RLS policies in `002_rls_policies.sql` assume Supabase Auth. Running against a plain PostgreSQL (no Supabase Auth) would require rewriting those policies and the auth middleware — not currently supported.

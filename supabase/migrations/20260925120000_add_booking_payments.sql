-- Online deposits (Paystack + Flutterwave) on the bookings table.
-- Re-runnable: every statement is guarded, so applying it twice is a no-op.
--
-- Until this runs, bookings still save and payments still work — the backend
-- retries the insert without these columns, and payment state is always
-- re-readable from the gateway. The columns are what let a confirmed deposit
-- survive without asking the gateway again.

alter table public.bookings add column if not exists "paymentStatus" text default 'unpaid';
alter table public.bookings add column if not exists "paymentProvider" text;
alter table public.bookings add column if not exists "paymentMethod" text;
alter table public.bookings add column if not exists "paymentRef" text;
alter table public.bookings add column if not exists "amountPaid" numeric default 0;
alter table public.bookings add column if not exists "currency" text;
alter table public.bookings add column if not exists "balanceDueGHS" numeric default 0;
alter table public.bookings add column if not exists "paidAt" text;
alter table public.bookings add column if not exists "paymentMeta" jsonb;

-- The backend marks a deposit paid with a PATCH keyed on the booking reference.
-- This policy is what allows that, and it matches the table's existing posture
-- (bookings are already world-readable and world-insertable by reference).
--
-- Prefer the tighter option: set SUPABASE_SERVICE_ROLE_KEY in Vercel, then run
--   drop policy if exists "public update bookings" on public.bookings;
-- The service role bypasses RLS, so the backend keeps working with the anon key
-- unable to modify anything.
drop policy if exists "public update bookings" on public.bookings;
create policy "public update bookings" on public.bookings
  for update using (true) with check (true);

-- An abandoned checkout leaves a row in 'awaiting_payment'. This makes those
-- easy to find for a follow-up call.
create index if not exists bookings_payment_status_idx on public.bookings ("paymentStatus");

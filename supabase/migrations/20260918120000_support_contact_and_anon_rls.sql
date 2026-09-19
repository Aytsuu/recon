-- Support contact fields (Context Agent registry hydrate) + temporary local anon RLS.
-- Replace permissive anon policies with user-scoped policies before production.

alter table public.support_case
  add column if not exists support_email text,
  add column if not exists support_phone text,
  add column if not exists support_url text;

-- Temporary local-development policies (anon role can CRUD all rows).
create policy "local_anon_all_support_case"
  on public.support_case
  for all
  to anon
  using (true)
  with check (true);

create policy "local_anon_all_case_clarification"
  on public.case_clarification
  for all
  to anon
  using (true)
  with check (true);

create policy "local_anon_all_support_draft"
  on public.support_draft
  for all
  to anon
  using (true)
  with check (true);

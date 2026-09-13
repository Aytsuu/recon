-- Migration: support_cases
-- Adds three tables that back the RECON support-case feature:
--   support_case          – the top-level case record
--   case_clarification    – focused questions attached to a case
--   support_draft         – the editable draft attached to a case
-- RLS is enabled on all three tables.  User-specific policies are deferred.

-- ---------------------------------------------------------------------------
-- support_case
-- ---------------------------------------------------------------------------
create table public.support_case (
  id                    bigint generated always as identity primary key,
  input_mode            text        not null,
  status                text        not null default 'input_ready',
  case_text             text,
  language_code         text,
  provider_name         text,
  service_name          text,
  issue_category        text,
  problem_summary       text,
  attempted_resolutions text[]      not null default '{}',
  desired_outcome       text,
  created_at            timestamptz not null default now(),
  updated_at            timestamptz not null default now(),

  constraint support_case_input_mode_check
    check (input_mode in ('typed', 'voice')),

  constraint support_case_status_check
    check (status in (
      'transcribing',
      'input_ready',
      'clarifying',
      'ready_for_draft',
      'draft_ready',
      'failed'
    )),

  -- Non-null case_text must not be whitespace only.
  constraint support_case_case_text_not_blank
    check (case_text is null or length(trim(case_text)) > 0),

  -- A typed case must have case_text.
  constraint support_case_typed_requires_text
    check (input_mode <> 'typed' or case_text is not null),

  -- Only a voice case can be in the transcribing state.
  constraint support_case_transcribing_only_voice
    check (status <> 'transcribing' or input_mode = 'voice')
);

-- List index for chronological ordering (primary query pattern).
create index support_case_created_at_idx
  on public.support_case (created_at desc);

alter table public.support_case enable row level security;

-- ---------------------------------------------------------------------------
-- case_clarification
-- ---------------------------------------------------------------------------
create table public.case_clarification (
  id          bigint      generated always as identity primary key,
  case_id     bigint      not null references public.support_case (id) on delete cascade,
  field_key   text        not null,
  question    text        not null,
  answer      text,
  status      text        not null default 'pending',
  position    smallint    not null,
  created_at  timestamptz not null default now(),
  answered_at timestamptz,

  constraint case_clarification_field_key_check
    check (field_key in ('provider_name', 'problem_summary', 'desired_outcome')),

  constraint case_clarification_status_check
    check (status in ('pending', 'answered', 'skipped')),

  constraint case_clarification_position_positive
    check (position > 0),

  -- Each field_key appears at most once per case.
  constraint case_clarification_case_field_unique
    unique (case_id, field_key),

  -- Each position is unique within a case.
  constraint case_clarification_case_position_unique
    unique (case_id, position),

  -- Pending/skipped: no answer and no answered_at.
  constraint case_clarification_pending_skipped_no_answer
    check (
      status = 'answered'
      or (answer is null and answered_at is null)
    ),

  -- Answered: non-blank answer and answered_at are both required.
  constraint case_clarification_answered_requires_answer
    check (
      status <> 'answered'
      or (
        answer is not null
        and length(trim(answer)) > 0
        and answered_at is not null
      )
    )
);

alter table public.case_clarification enable row level security;

-- ---------------------------------------------------------------------------
-- support_draft
-- ---------------------------------------------------------------------------
create table public.support_draft (
  id            bigint      generated always as identity primary key,
  case_id       bigint      not null unique references public.support_case (id) on delete cascade,
  subject       text        not null,
  body          text        not null,
  language_code text,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now(),

  constraint support_draft_subject_not_blank
    check (length(trim(subject)) > 0),

  constraint support_draft_body_not_blank
    check (length(trim(body)) > 0)
);

alter table public.support_draft enable row level security;

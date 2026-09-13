-- Development fixtures for the RECON support-case feature.
-- Provides three representative cases that Person A's server-side
-- repository can use for integration smoke-tests and that Person B's
-- Astro UI can display through fixture mode or the real API.
--
-- Cases:
--   id = 1  input_ready  typed  – a clean case waiting for extraction
--   id = 2  clarifying   typed  – a case with one pending clarification
--   id = 3  draft_ready  typed  – a completed case with a draft

-- ---------------------------------------------------------------------------
-- Case 1 – input_ready (typed)
-- ---------------------------------------------------------------------------
insert into public.support_case (
  input_mode, status, case_text,
  language_code, provider_name, service_name
) values (
  'typed', 'input_ready',
  'My internet keeps disconnecting every few hours. I have already restarted the router twice.',
  'en', 'Converge ICT', 'Residential fiber internet'
);

-- ---------------------------------------------------------------------------
-- Case 2 – clarifying (typed, one pending question)
-- ---------------------------------------------------------------------------
insert into public.support_case (
  input_mode, status, case_text,
  language_code, provider_name, service_name,
  issue_category, problem_summary, attempted_resolutions
) values (
  'typed', 'clarifying',
  'My bill shows unexpected charges for last month.',
  'en', 'Globe Telecom', 'Postpaid mobile plan',
  'billing', 'Unexpected charges on monthly bill.', ARRAY['Checked the bill breakdown online']
);

insert into public.case_clarification (
  case_id, field_key, question, status, position
) values (
  2, 'desired_outcome',
  'What resolution are you expecting — a refund, a billing adjustment, or an explanation of the charges?',
  'pending', 1
);

-- ---------------------------------------------------------------------------
-- Case 3 – draft_ready (typed, all fields, with a draft)
-- ---------------------------------------------------------------------------
insert into public.support_case (
  input_mode, status, case_text,
  language_code, provider_name, service_name,
  issue_category, problem_summary, attempted_resolutions, desired_outcome
) values (
  'typed', 'draft_ready',
  'My fiber connection has been dropping for three days. I have restarted the ONT and the router but the issue persists.',
  'en', 'PLDT Home', 'Home Fiber Broadband',
  'internet_connectivity',
  'Persistent fiber connection drops over three days.',
  ARRAY['Restarted the ONT', 'Restarted the router'],
  'Restore stable 24/7 fiber connection or dispatch a technician.'
);

insert into public.support_draft (
  case_id,
  subject,
  body,
  language_code
) values (
  3,
  'Persistent Fiber Connection Drops – Requesting Technician Dispatch',
  E'Dear PLDT Home Support,\n\nI am writing to report an ongoing internet connectivity issue with my Home Fiber Broadband service that has persisted for three consecutive days.\n\n**Problem:** My fiber connection drops repeatedly throughout the day, making normal work and communication impossible.\n\n**Steps already taken:**\n- Restarted the Optical Network Terminal (ONT)\n- Restarted the router\n\nDespite these steps the disconnections continue. I am requesting either a remote line check or the dispatch of a field technician to diagnose and resolve the issue permanently.\n\nPlease let me know the next steps and an estimated resolution timeline.\n\nThank you for your prompt attention.',
  'en'
);

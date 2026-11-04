-- Tagging columns for problems_log (classification plan, doc 09 section 8).
--
-- The server writes a row as soon as a problem is solved (untagged), then a background
-- tagger fills in the tags. These columns record HOW each tag was made, so tags can be
-- audited and the doubtful ones reviewed:
--   tag_source    'engine_card' = topic taken from the formula card that solved it (trusted)
--                 'llm'         = topic chosen by the model (no card matched)
--   needs_review  the model disagreed with the card, answered Other, or gave an invalid pair
--   review_reason short machine-written reason (never student text)
--   matched_card  the formula card id when the engine solved it through exactly one card,
--                 so card-vs-model cross-checks stay possible later

alter table public.problems_log
  add column tag_source    text check (tag_source in ('engine_card', 'llm')),
  add column needs_review  boolean not null default false,
  add column review_reason text,
  add column matched_card  text;

-- A row is either untagged (no topic, no source) or tagged with both.
alter table public.problems_log
  add constraint problems_log_tag_source_with_topic
    check ((tag_source is null) = (topic is null));

-- The review queue reads only flagged rows, newest first.
create index problems_log_review_idx on public.problems_log (created_at desc) where needs_review;

-- Guests stay in auth.users (and profiles) forever unless removed. Delete guest older
-- than 7 days; their guest_usage rows go with them (on delete cascade).
create extension if not exists pg_cron;

select cron.schedule('delete-old-guest', '0 3 * * *', $$
  delete from auth.users where is_anonymous and created_at < now() - interval '7 days'
$$);
select cron.schedule('trim-guest-daily-usage', '0 3 * * *', $$
  delete from public.guest_daily_usage where day < (now() at time zone 'utc')::date - 30
$$);
-- Edge Function 연결 — 함수 두 개를 배포하고 비밀값을 넣은 다음, SQL Editor 에서 한 번 실행한다(README 의 '결제·푸시' 순서).
--  ① 푸시: 공지·일정·출석·댓글이 새로 들어오면 DB 가 push 함수를 부른다(pg_net — Supabase Database Webhooks 와 같은 방식)
--  ② 환불 정리: 매일 새벽 verify-purchase 를 불러 Google Play 에서 환불·취소된 결제만큼 이용 기간을 되돌린다(pg_cron)
-- 바꿀 값: <PROJECT-REF>(Project Settings → General → Reference ID) · <PUSH_SECRET>·<CRON_SECRET>(함수 비밀값과 같게) · <ANON_KEY>(Project Settings → API)
create extension if not exists pg_net;
create or replace function private.call_push() returns trigger language plpgsql security definer set search_path = public, private as $$
begin
  perform net.http_post(
    url := 'https://<PROJECT-REF>.supabase.co/functions/v1/push',
    headers := jsonb_build_object('Content-Type', 'application/json', 'x-push-secret', '<PUSH_SECRET>'),
    body := jsonb_build_object('type', 'INSERT', 'table', tg_table_name, 'record', to_jsonb(new)));
  return new;
end $$;
drop trigger if exists push_notices on notices;       create trigger push_notices    after insert on notices    for each row execute function private.call_push();
drop trigger if exists push_sched on sched;           create trigger push_sched      after insert on sched      for each row execute function private.call_push();
drop trigger if exists push_attendance on attendance; create trigger push_attendance after insert on attendance for each row execute function private.call_push();
drop trigger if exists push_comments on comments;     create trigger push_comments   after insert on comments   for each row execute function private.call_push();

-- ② 환불·취소 정리 — 매일 04:10(KST). Database → Extensions 에서 pg_cron · pg_net 을 켠 뒤 실행
create extension if not exists pg_cron;
select cron.schedule('pcs-voided-purchases', '10 19 * * *', $$
  select net.http_post(
    url := 'https://<PROJECT-REF>.supabase.co/functions/v1/verify-purchase',
    headers := jsonb_build_object('Content-Type', 'application/json', 'Authorization', 'Bearer <ANON_KEY>', 'x-cron-secret', '<CRON_SECRET>'),
    body := '{"action":"voided"}'::jsonb)
$$);

-- Edge Function 연결 — 함수 두 개를 배포하고 비밀값을 넣은 다음, SQL Editor 에서 한 번 실행한다(README 의 '결제·푸시' 순서).
--  ① 푸시: 공지·일정·출석·댓글(+도움이 필요해 보이는 글)이 새로 들어오면 DB 가 push 함수를 부른다(pg_net — Supabase Database Webhooks 와 같은 방식)
--  ①-3 보호자 주간 요약: 일요일 저녁 7시(KST) push 함수가 보호자마다 '이번 주' 한 줄을 보낸다(pg_cron · 밤 22~07시에는 보내지 않음)
--  ①-4 과제 알림: 새 과제 → 대상 학생 폰 · 매일 저녁 7시(KST) 내일 마감인데 아직 안 낸 학생에게 한 번
--  ② 환불 정리: 매일 새벽 verify-purchase 를 불러 Google Play 에서 환불·취소된 결제만큼 이용 기간을 되돌린다(pg_cron)
-- 바꿀 값: <PROJECT-REF>(Project Settings → General → Reference ID) · <PUSH_SECRET>·<CRON_SECRET>(함수 비밀값과 같게) · <ANON_KEY>(Project Settings → API)
create extension if not exists pg_net;
create extension if not exists pg_cron;
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
drop trigger if exists push_assignments on assignments; create trigger push_assignments after insert on assignments for each row execute function private.call_push();   -- 새 과제 → 대상 학생(2026-10-07)
-- 도움이 필요해 보이는 글 → 원장 폰('먼저 살펴볼 글', 잠금화면에는 내용을 싣지 않는다)
drop trigger if exists push_care_posts on posts;       create trigger push_care_posts after insert on posts      for each row when (new.care) execute function private.call_push();
-- 고쳐 쓰다가 도움이 필요해 보이게 된 글도(처음 한 번만 — care 가 false→true 로 바뀔 때)
-- '친구가 걱정돼요' 신고 → 원장 폰(1건이어도 · 글은 가리지 않는다)
drop trigger if exists push_worry on reports;          create trigger push_worry      after insert on reports for each row when (new.reason = 'worry') execute function private.call_push();
drop trigger if exists push_care_edit on posts;        create trigger push_care_edit  after update on posts for each row when (new.care and not old.care) execute function private.call_push();

-- ①-2 밤(22~07시)에 미룬 학생 댓글 알림 → 아침 07:00(KST)에 한 번 '밤사이 새 댓글이 있어요'
select cron.schedule('pcs-push-morning', '0 22 * * *', $$
  select net.http_post(
    url := 'https://<PROJECT-REF>.supabase.co/functions/v1/push',
    headers := jsonb_build_object('Content-Type', 'application/json', 'x-push-secret', '<PUSH_SECRET>'),
    body := '{"action":"morning"}'::jsonb)
$$);

-- ①-3 보호자 주간 요약 — 매주 일요일 19:00(KST) = 일요일 10:00(UTC). 받을 사람·숫자는 DB 함수 weekly_digest()(서비스 키 전용)
select cron.schedule('pcs-push-weekly', '0 10 * * 0', $$
  select net.http_post(
    url := 'https://<PROJECT-REF>.supabase.co/functions/v1/push',
    headers := jsonb_build_object('Content-Type', 'application/json', 'x-push-secret', '<PUSH_SECRET>'),
    body := '{"action":"weekly"}'::jsonb)
$$);

-- ② 환불·취소 정리 — 매일 04:10(KST). Database → Extensions 에서 pg_cron · pg_net 을 켠 뒤 실행
select cron.schedule('pcs-voided-purchases', '10 19 * * *', $$
  select net.http_post(
    url := 'https://<PROJECT-REF>.supabase.co/functions/v1/verify-purchase',
    headers := jsonb_build_object('Content-Type', 'application/json', 'Authorization', 'Bearer <ANON_KEY>', 'x-cron-secret', '<CRON_SECRET>'),
    body := '{"action":"voided"}'::jsonb)
$$);

-- ①-4 과제 마감 전날 알림 — 매일 19:00(KST) = 10:00(UTC). 내일 마감인데 아직 안 낸 학생 폰에 한 번(asg_due_targets, 서비스 키 전용)
select cron.schedule('pcs-push-asgdue', '0 10 * * *', $$
  select net.http_post(
    url := 'https://<PROJECT-REF>.supabase.co/functions/v1/push',
    headers := jsonb_build_object('Content-Type', 'application/json', 'x-push-secret', '<PUSH_SECRET>'),
    body := '{"action":"asgdue"}'::jsonb)
$$);

-- 약지도 가족 알림 — 15분마다 놓침 확인(Edge Function yak-family-check 부르기). Main 이 함수 배포·비밀 등록 «뒤에» 한 번 돌린다.
-- 필요: pg_cron · pg_net 확장(Supabase 대시보드 → Database → Extensions 에서 켬).
-- <프로젝트 주소> 와 <FAMILY_CRON_SECRET 값> 두 자리만 바꿔서 돌린다 — 이 파일에 값을 적어 저장소에 올리지 않는다.
-- 여러 번 돌려도 같다(같은 이름 작업을 다시 걸면 바뀜).
select cron.schedule(
  'yak-family-check',
  '*/15 * * * *',
  $$ select net.http_post(
       url := '<프로젝트 주소>/functions/v1/yak-family-check',
       headers := jsonb_build_object('Content-Type', 'application/json', 'x-cron-secret', '<FAMILY_CRON_SECRET 값>'),
       body := '{}'::jsonb,
       timeout_milliseconds := 20000) $$
);
-- 보낸 기록 30일 지난 것 정리(매일 04:10 서울 = 19:10 UTC)
select cron.schedule('yak-family-sent-trim', '10 19 * * *', $$ delete from public.yak_family_sent where day < (now() at time zone 'Asia/Seoul')::date - 30 $$);

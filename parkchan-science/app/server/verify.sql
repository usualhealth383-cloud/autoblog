-- 서버 설정 점검 — SQL Editor 에 통째로 붙여 넣고 Run. 읽기만 한다(아무것도 바꾸지 않음).
-- 결과 표의 ok 칸이 모두 ✓ 여야 출시. ✗ 줄의 '할 일'을 README 「순서」 번호대로 하면 된다.
-- 앱 쪽(손님 키로 막혀야 하는 것)은 python3 tools/live_check.py 가 본다.
with
cfg as (select k from private.config),
-- pg_cron 을 아직 안 켰으면 cron.job 이 없다 — 그때도 오류 없이 ✗ 로 보이게 돌려 읽는다
jobs as (select x::text as jobname from unnest(case when to_regclass('cron.job') is null then '{}'::xml[]
          else xpath('//jobname/text()', query_to_xml('select jobname from cron.job', false, true, '')) end) x),
owners as (select p.id, u.email_confirmed_at from profiles p join auth.users u on u.id = p.id where p.role = 'owner'),
checks(n, name, ok, todo) as (
  select 1, 'pg_cron 켜짐', exists (select 1 from pg_extension where extname = 'pg_cron'), 'Database → Extensions → pg_cron 켜고 schema.sql 다시 Run'
  union all select 2, '새벽 정리 예약(pcs-purge-old)', exists (select 1 from jobs where jobname = 'pcs-purge-old'), 'pg_cron 켠 뒤 schema.sql 다시 Run(개인정보 보관 기간 약속)'
  union all select 3, 'public 표 모두 RLS 켜짐', not exists (select 1 from pg_class c join pg_namespace s on s.oid = c.relnamespace where s.nspname = 'public' and c.relkind = 'r' and not c.relrowsecurity), 'schema.sql 다시 Run — 그래도 ✗ 면 작업자에게'
  union all select 4, '누구나 읽는 정책은 반 이름(classes)·오류 기록 쓰기뿐', not exists (select 1 from pg_policies where schemaname = 'public' and roles && '{public,anon}'::name[] and not (tablename = 'classes' and cmd = 'SELECT') and not (tablename = 'client_errors' and cmd = 'INSERT')), '작업자에게(손으로 정책을 더했는지)'
  union all select 5, 'security definer 함수 모두 search_path 고정', not exists (select 1 from pg_proc p join pg_namespace s on s.oid = p.pronamespace where s.nspname in ('public', 'private') and p.prosecdef and not exists (select 1 from unnest(coalesce(p.proconfig, '{}')) x where x like 'search_path=%')), '작업자에게'
  union all select 6, '출석 씨앗 있음', exists (select 1 from cfg where k = 'attend_secret'), 'schema.sql 다시 Run'
  union all select 7, '원장 이메일 넣음([설정] 첫 줄)', exists (select 1 from cfg where k = 'owner_email'), 'schema.sql 맨 아래 [설정] 두 줄'
  union all select 8, '원장 계정 1개 · 메일 인증 끝남', (select count(*) = 1 and bool_and(email_confirmed_at is not null) from owners), '앱에서 원장 이메일로 가입 → 메일 링크 → [설정] 둘째 줄'
  union all select 9, '원장 계정을 id 로 고정(owner_uid)', exists (select 1 from private.config c join owners o on o.id::text = c.v where c.k = 'owner_uid'), 'README 5번 ▼ 한 줄'
  union all select 10, '반 1개 이상', exists (select 1 from classes), '원장 화면 → 반·학생 관리에서 반 만들기'
  union all select 11, '시연용 코드(MON123·TUE456·WED789) 정리', not exists (select 1 from students where code in ('MON123', 'TUE456', 'WED789')), '실제 학생 등록 뒤 원장 화면에서 시연 학생 지우기(아직 시연 중이면 그대로 둬도 됨)'
  union all select 12, '(푸시) pg_net 켜짐', exists (select 1 from pg_extension where extname = 'pg_net'), '앱 스토어 출시 때 — README 「결제 · 푸시 알림」 B'
  union all select 13, '(푸시) 예약 3개(morning·weekly·asgdue)', (select count(*) = 3 from jobs where jobname in ('pcs-push-morning', 'pcs-push-weekly', 'pcs-push-asgdue')), '앱 스토어 출시 때 — functions.sql ① 부분'
  union all select 14, '(결제) 환불 정리 예약', exists (select 1 from jobs where jobname = 'pcs-voided-purchases'), '스토어 결제를 켤 때 — functions.sql ② 부분'
)
select n, case when ok then '✓' else '✗' end as ok, name, case when ok then '' else todo end as "할 일" from checks order by n;

-- ════════════════════════════════════════════════════════════════════════════════
-- 메디나눔 — 약지도(app 'yakjido') 더하기 (2026-10-13 · 약지도 세션)
--
-- 바탕: 메디나눔_합치기_1013 a·b·c·d (네 앱 공용, gildongmu · uszalzczpmyifzbamjno · 서울) 가 이미 올라가 있어야 한다.
-- 무엇:
--   1) app 확인 넓히기 — records · inquiries · subscriptions · trial_devices · comm_posts 의 app 을
--      ('kids','gildongmu','clinicscore','gyeote','yakjido') 로. 이미 그 꼴이면 건너뛴다. 있는 줄은 그대로 통과한다.
--   2) 구독 함수 셋 · delete_own_account(p_app) 의 앱 목록에 'yakjido' — 본문은 10-13 서버에 있는 정의 그대로(앱 목록만 다름).
--   3) 약지도 「부모님께 보내기」 표 yak_shares — 로그인 없이 받는 사람이 여는 7일짜리 약 목록.
--      RLS 켜고 정책 없음 + anon·authenticated 권한 거둠 = 어떤 키로도 표를 직접 못 연다.
--      Edge Function yak-share 만 DB 연결(SUPABASE_DB_URL)로 읽고 쓴다. 이름·전화·위치·user_id 칸 없음.
-- ⚠️ 네 앱 세션에: 이 파일 뒤로는 app 목록이 «다섯». 1013_d 처럼 «정확히 네 앱» 으로 다시 거는 SQL 을 돌리면
--    약지도 줄이 있을 때 실패(트랜잭션 전체 취소)하고, 없을 때는 약지도가 다시 막힌다 — 목록에 'yakjido' 를 넣어 주세요.
--    store-webhook(_도구/서버_함수/store-webhook/index.ts 32행)의 네 앱 배열에도 "yakjido" 를 더해야 약지도 결제가 붙는다.
-- 여러 번 돌려도 같다. 표를 없애거나 기록 줄을 비우는 문장은 없다(delete 는 함수 «본문» 안에만).
-- ⛔ 비밀 키 없음.
-- ════════════════════════════════════════════════════════════════════════════════

begin;

-- 1) app 확인 넓히기 ─────────────────────────────────────────────────────────────
do $$
declare
  t text; c record;
  want constant text := $w$CHECK ((app = ANY (ARRAY['kids'::text, 'gildongmu'::text, 'clinicscore'::text, 'gyeote'::text, 'yakjido'::text])))$w$;
begin
  foreach t in array array['records','inquiries','subscriptions','trial_devices','comm_posts'] loop
    if exists (select 1 from pg_constraint k
                where k.conrelid = format('public.%I', t)::regclass and k.conname = t || '_app_check'
                  and pg_get_constraintdef(k.oid) = want)
       and not exists (select 1 from pg_constraint k join pg_attribute a on a.attrelid = k.conrelid and a.attname = 'app'
                        where k.conrelid = format('public.%I', t)::regclass and k.contype = 'c'
                          and k.conkey = array[a.attnum]::int2[] and k.conname <> t || '_app_check') then
      continue;   -- 이미 다섯 앱 꼴
    end if;
    for c in select k.conname from pg_constraint k join pg_attribute a on a.attrelid = k.conrelid and a.attname = 'app'
              where k.conrelid = format('public.%I', t)::regclass and k.contype = 'c' and k.conkey = array[a.attnum]::int2[] loop
      execute format('alter table public.%I drop constraint %I', t, c.conname);
    end loop;
    execute format($f$alter table public.%I add constraint %I check (app in ('kids','gildongmu','clinicscore','gyeote','yakjido'))$f$,
                   t, t || '_app_check');
  end loop;
end $$;

-- 2) 함수 넷 — 서버에 있는 정의 그대로, 앱 목록만 다섯 ───────────────────────────────
CREATE OR REPLACE FUNCTION public.start_trial(p_app text, p_device text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare v_uid uuid := auth.uid(); u record;
begin
  if v_uid is null then return jsonb_build_object('ok', false, 'why', 'login'); end if;
  if p_app is null or p_app not in ('kids','gildongmu','clinicscore','gyeote','yakjido') then
    return jsonb_build_object('ok', false, 'why', 'app');
  end if;
  select email_confirmed_at, phone_confirmed_at into u from auth.users where id = v_uid;
  if u.email_confirmed_at is null and u.phone_confirmed_at is null then
    return jsonb_build_object('ok', false, 'why', 'verify');
  end if;
  if exists (select 1 from public.subscriptions s where s.user_id = v_uid and s.app = p_app) then
    return jsonb_build_object('ok', false, 'why', 'used_account');
  end if;
  if p_device is null or length(p_device) < 16 or length(p_device) > 128 then
    return jsonb_build_object('ok', false, 'why', 'device');
  end if;
  if exists (select 1 from public.trial_devices t where t.device_hash = p_device and t.app = p_app) then
    return jsonb_build_object('ok', false, 'why', 'used_device');
  end if;
  insert into public.trial_devices (device_hash, app, user_id) values (p_device, p_app, v_uid);
  insert into public.subscriptions (user_id, app, status, source, until, converts_at, plan)
    values (v_uid, p_app, 'trial', 'trial', now() + interval '7 days', now() + interval '7 days', 'month');
  return jsonb_build_object('ok', true, 'until', now() + interval '7 days');
end $function$;

CREATE OR REPLACE FUNCTION public.subscription_status(p_app text)
 RETURNS TABLE(status text, plan text, source text, until timestamp with time zone, started_at timestamp with time zone, converts_at timestamp with time zone, cancel_at_period_end boolean, pay_ready boolean)
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare v_uid uuid := auth.uid();
begin
  if v_uid is null then return; end if;
  if p_app is null or p_app not in ('kids','gildongmu','clinicscore','gyeote','yakjido') then return; end if;
  update public.subscriptions s set status = 'expired', updated_at = now()
    where s.user_id = v_uid and s.app = p_app and s.status in ('trial','active') and s.until is not null and s.until < now()
      and not (s.pay_ready and not s.cancel_at_period_end);
  return query select s.status, s.plan, s.source, s.until, s.started_at, s.converts_at, s.cancel_at_period_end, s.pay_ready
    from public.subscriptions s where s.user_id = v_uid and s.app = p_app;
end $function$;

CREATE OR REPLACE FUNCTION public.cancel_subscription(p_app text, p_cancel boolean DEFAULT true)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare v_uid uuid := auth.uid();
begin
  if v_uid is null then raise exception 'not signed in'; end if;
  if p_app is null or p_app not in ('kids','gildongmu','clinicscore','gyeote','yakjido') then raise exception 'bad app'; end if;
  update public.subscriptions s set cancel_at_period_end = coalesce(p_cancel, true), updated_at = now()
    where s.user_id = v_uid and s.app = p_app;
end $function$;

CREATE OR REPLACE FUNCTION public.delete_own_account(p_app text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare v_uid uuid := auth.uid(); v_left boolean;
begin
  if v_uid is null then raise exception 'not signed in'; end if;
  if p_app is null or p_app not in ('kids','gildongmu','clinicscore','gyeote','yakjido') then raise exception 'bad app'; end if;

  delete from public.records       r where r.user_id = v_uid and r.app = p_app;
  delete from public.inquiries     i where i.user_id = v_uid and i.app = p_app;
  delete from public.subscriptions s where s.user_id = v_uid and s.app = p_app;
  update public.trial_devices t set user_id = null where t.user_id = v_uid and t.app = p_app;   -- 기기 해시만 남긴다(체험 되풀이 막기)
  -- 이야기 나누기: 그 앱 글에 단 내 공감·댓글, 그 앱의 내 글(글에 달린 남의 댓글·공감·신고는 cascade)
  delete from public.comm_hearts   h using public.comm_posts p where h.post_id = p.id and p.app = p_app and h.uid = v_uid;
  delete from public.comm_comments c using public.comm_posts p where c.post_id = p.id and p.app = p_app and c.uid = v_uid;
  delete from public.comm_posts    p where p.uid = v_uid and p.app = p_app;

  if p_app = 'gildongmu' then
    delete from public.verify v where v.user_id = v_uid;
  elsif p_app = 'clinicscore' then
    delete from public.student_verify sv where sv.user_id = v_uid;
  end if;
  if p_app in ('gildongmu', 'clinicscore') then
    begin
      delete from storage.objects o
       where o.bucket_id = case when p_app = 'gildongmu' then 'verify-docs' else 'student-docs' end
         and (o.owner = v_uid or o.name like v_uid::text || '/%');
    exception when others then null;   -- Supabase 는 SQL 로 storage 삭제를 막는다 — 앱이 Storage API 로 먼저 지운다
    end;
  end if;

  v_left := exists (select 1 from public.records r        where r.user_id = v_uid)
         or exists (select 1 from public.subscriptions s  where s.user_id = v_uid)
         or exists (select 1 from public.inquiries i      where i.user_id = v_uid)
         or exists (select 1 from public.verify v         where v.user_id = v_uid)
         or exists (select 1 from public.student_verify x where x.user_id = v_uid)
         or exists (select 1 from public.comm_posts p     where p.uid = v_uid)
         or exists (select 1 from public.comm_comments c  where c.uid = v_uid);
  if not v_left then
    delete from auth.users u where u.id = v_uid;   -- 남은 공감·신고·차단·기기 표식은 cascade / set null
  end if;
  return jsonb_build_object('ok', true, 'app', p_app, 'account_deleted', not v_left);
end $function$;

-- 3) 약지도 「부모님께 보내기」 ──────────────────────────────────────────────────────
create table if not exists public.yak_shares (
  id          uuid primary key default gen_random_uuid(),
  code        text not null unique check (char_length(code) between 20 and 40),   -- 128비트 무작위(주소에 쓰는 글자)
  items       jsonb not null check (jsonb_typeof(items) = 'array' and jsonb_array_length(items) between 1 and 10),
  label       text check (label is null or char_length(label) <= 20),              -- 받는 분 호칭(엄마·아빠 등, 선택)
  note        text check (note is null or char_length(note) <= 100),               -- 한 줄 메모(선택)
  consent_at  timestamptz not null,                                                 -- 민감정보 처리 동의 시각
  created_at  timestamptz not null default now(),
  expires_at  timestamptz not null default now() + interval '7 days',
  bought_at   timestamptz                                                           -- 받은 분이 「샀어요」를 누른 때
);
create index if not exists yak_shares_expires_idx on public.yak_shares (expires_at);
alter table public.yak_shares enable row level security;   -- 정책 없음 = 어떤 키로도 표를 직접 못 연다
revoke all on table public.yak_shares from anon, authenticated;
-- 만료분 지우기는 함수(yak-share)가 새로 만들 때마다 함께 한다(이 프로젝트에 확장을 더하지 않으려고).

commit;

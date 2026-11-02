-- ════════════════════════════════════════════════════════════════════════════
-- 메디나눔 공용 푸시(11-03 현욱님 「약지도 알림처럼 다른 앱들도」 · 요청서 docs/requests/20261103_100점_검수_라운드2.md A)
--   mn_push_subs  — 다섯 앱 공용 알림 받을 곳(기기). app 칸으로 앱마다 따로 · lang·tz 는 기기 말·시간대
--   mn_push_sent  — 보낸 기록(같은 일을 두 번 보내지 않게): user · app · kind · day · slot
--   함수 mn_push_save / mn_push_drop — 앱이 로그인한 채로 부른다(auth.uid())
--   약지도 yak_push_subs 줄은 app='yakjido' 로 옮겨 담는다(지우지 않음 — yak-family-check 가 mn-push-check 로 바뀔 때까지 둘 다 산다)
-- 추가형: 표를 없애거나 기록을 비우는 문장 없음(delete 는 함수 본문 안 정리뿐). 여러 번 돌려도 같다. ⛔ 비밀 키 없음.
-- ════════════════════════════════════════════════════════════════════════════

create table if not exists public.mn_push_subs (
  endpoint    text primary key check (endpoint ~ '^https://' and char_length(endpoint) <= 1000),
  user_id     uuid not null references auth.users(id) on delete cascade,
  app         text not null check (app in ('kids', 'gildongmu', 'clinicscore', 'gyeote', 'yakjido')),
  p256dh      text not null check (char_length(p256dh) <= 200),
  auth        text not null check (char_length(auth) <= 100),
  lang        text not null default 'ko' check (lang in ('ko', 'en', 'es', 'ja', 'zh')),
  tz          text not null default 'Asia/Seoul' check (char_length(tz) <= 60),
  created_at  timestamptz not null default now(),
  last_ok     timestamptz
);
create index if not exists mn_push_subs_user_app on public.mn_push_subs (user_id, app);

create table if not exists public.mn_push_sent (
  user_id  uuid not null references auth.users(id) on delete cascade,
  app      text not null,
  kind     text not null check (char_length(kind) <= 80),
  day      date not null,
  slot     text not null check (char_length(slot) <= 20),
  sent_at  timestamptz not null default now(),
  primary key (user_id, app, kind, day, slot)
);

alter table public.mn_push_subs enable row level security;
alter table public.mn_push_sent enable row level security;
revoke all on public.mn_push_subs, public.mn_push_sent from anon, authenticated;

-- 약지도 기존 구독 옮겨 담기(있으면 그대로)
insert into public.mn_push_subs (endpoint, user_id, app, p256dh, auth, created_at, last_ok)
select s.endpoint, s.user_id, 'yakjido', s.p256dh, s.auth, s.created_at, s.last_ok from public.yak_push_subs s
on conflict (endpoint) do nothing;

-- 기기 알림 받을 곳 저장(한 사람·한 앱 기기 5대까지)
create or replace function public.mn_push_save(p_app text, p_endpoint text, p_p256dh text, p_auth text, p_lang text, p_tz text)
returns boolean language plpgsql security definer set search_path = public as $$
declare v_uid uuid := auth.uid();
begin
  if v_uid is null then raise exception 'login required' using errcode = '28000'; end if;
  insert into public.mn_push_subs (endpoint, user_id, app, p256dh, auth, lang, tz)
  values (p_endpoint, v_uid, p_app, p_p256dh, p_auth, coalesce(nullif(p_lang, ''), 'ko'), coalesce(nullif(p_tz, ''), 'Asia/Seoul'))
  on conflict (endpoint) do update set user_id = excluded.user_id, app = excluded.app, p256dh = excluded.p256dh, auth = excluded.auth,
    lang = excluded.lang, tz = excluded.tz, created_at = now();
  delete from public.mn_push_subs s where s.user_id = v_uid and s.app = p_app and s.endpoint not in
    (select s2.endpoint from public.mn_push_subs s2 where s2.user_id = v_uid and s2.app = p_app order by s2.created_at desc limit 5);
  return true;
end $$;

create or replace function public.mn_push_drop(p_endpoint text)
returns boolean language plpgsql security definer set search_path = public as $$
declare v_n int;
begin
  delete from public.mn_push_subs s where s.endpoint = p_endpoint and s.user_id = auth.uid();
  get diagnostics v_n = row_count; return v_n > 0;
end $$;

revoke all on function public.mn_push_save(text, text, text, text, text, text), public.mn_push_drop(text) from public, anon;
grant execute on function public.mn_push_save(text, text, text, text, text, text), public.mn_push_drop(text) to authenticated;

-- ════════════════════════════════════════════════════════════════════════════
-- 약지도 가족 알림(11-02 현욱님 「지금 만든다 · 가족 최대 3명 · 약 이름 뺌」) — 메디나눔 공용 서버(gildongmu)
-- 설계: yakjido/가족알림_설계.md
--   표 셋: yak_family_links(본인 ↔ 가족, 초대 코드 6자리 24시간) · yak_push_subs(알림 받을 기기) · yak_family_sent(보낸 기록)
--          + yak_family_tries(코드 넣기 횟수 — 맞히기 막기)
--   쓰기는 «함수로만»(security definer, auth.uid() 기준). 표는 RLS 켜고 정책 없음 + anon·authenticated 권한 거둠
--   = 어떤 키로도 표를 직접 못 연다. 놓침 확인은 Edge Function yak-family-check 가 DB 연결(SUPABASE_DB_URL)로 읽는다.
-- 추가형: 표·함수를 새로 만들거나 바꿀 뿐, 표를 없애거나 기록을 비우는 문장은 없다(delete 는 함수 «본문»의 만료 정리뿐).
-- 여러 번 돌려도 같다. ⛔ 비밀 키 없음.
-- ════════════════════════════════════════════════════════════════════════════

create table if not exists public.yak_family_links (
  id               uuid primary key default gen_random_uuid(),
  owner_id         uuid not null references auth.users(id) on delete cascade,   -- 약 드시는 분
  member_id        uuid references auth.users(id) on delete cascade,            -- 알림 받는 가족(코드를 넣으면 채워짐)
  owner_label      text not null check (char_length(owner_label) between 1 and 20),   -- 가족 화면에 보일 이름(예: 엄마) — 본인이 정함
  code             text,                                                        -- 6자리, 연결되면 비움
  code_expires     timestamptz,
  consent_at       timestamptz not null,                                        -- 본인: 복약 체크 여부를 이 가족에게 알리는 데 동의(제3자 제공)
  member_consent_at timestamptz,                                                -- 가족: 알림 받기 동의
  created_at       timestamptz not null default now(),
  accepted_at      timestamptz,
  muted_day        date,                                                        -- 가족이 「오늘은 그만」 누른 날(서울 날짜)
  ended_at         timestamptz,                                                 -- 끊은 때(본인·가족 누구나)
  ended_by         text check (ended_by in ('owner', 'member', 'system'))
);
create unique index if not exists yak_family_links_code on public.yak_family_links (code) where code is not null;
create unique index if not exists yak_family_links_pair on public.yak_family_links (owner_id, member_id) where ended_at is null and member_id is not null;
create index if not exists yak_family_links_owner on public.yak_family_links (owner_id) where ended_at is null;
create index if not exists yak_family_links_member on public.yak_family_links (member_id) where ended_at is null;

create table if not exists public.yak_push_subs (
  endpoint    text primary key check (endpoint ~ '^https://' and char_length(endpoint) <= 1000),
  user_id     uuid not null references auth.users(id) on delete cascade,
  p256dh      text not null check (char_length(p256dh) <= 200),
  auth        text not null check (char_length(auth) <= 100),
  created_at  timestamptz not null default now(),
  last_ok     timestamptz
);
create index if not exists yak_push_subs_user on public.yak_push_subs (user_id);

create table if not exists public.yak_family_sent (
  link_id  uuid not null references public.yak_family_links(id) on delete cascade,
  day      date not null,
  slot     text not null check (slot ~ '^[0-2][0-9]:[0-5][0-9]$'),
  sent_at  timestamptz not null default now(),
  primary key (link_id, day, slot)
);

create table if not exists public.yak_family_tries (
  user_id  uuid not null references auth.users(id) on delete cascade,
  at       timestamptz not null default now()
);
create index if not exists yak_family_tries_user on public.yak_family_tries (user_id, at);

alter table public.yak_family_links enable row level security;
alter table public.yak_push_subs    enable row level security;
alter table public.yak_family_sent  enable row level security;
alter table public.yak_family_tries enable row level security;
revoke all on public.yak_family_links, public.yak_push_subs, public.yak_family_sent, public.yak_family_tries from anon, authenticated;

-- ── 본인: 초대 코드 만들기(동의 필수 · 연결+대기 합쳐 3명까지) ──
create or replace function public.yak_family_invite(p_label text, p_consent boolean)
returns table (code text, expires_at timestamptz)
language plpgsql security definer set search_path = public as $$
declare v_uid uuid := auth.uid(); v_label text := btrim(regexp_replace(coalesce(p_label, ''), '[[:cntrl:]<>]', '', 'g')); v_code text; v_n int; i int := 0;
begin
  if v_uid is null then raise exception 'login required' using errcode = '28000'; end if;
  if p_consent is not true then raise exception 'consent required' using errcode = '22023'; end if;
  if char_length(v_label) < 1 then v_label := '가족'; end if;
  v_label := left(v_label, 20);
  -- 지난 대기 코드는 만료로 정리(기록은 남기고 코드만 비움)
  update public.yak_family_links l set code = null, ended_at = now(), ended_by = 'system'
   where l.owner_id = v_uid and l.member_id is null and l.ended_at is null and l.code_expires < now();
  select count(*) into v_n from public.yak_family_links l where l.owner_id = v_uid and l.ended_at is null;
  if v_n >= 3 then raise exception 'family limit' using errcode = '23514'; end if;
  loop
    i := i + 1;
    v_code := lpad((floor(random() * 1000000))::int::text, 6, '0');
    exit when not exists (select 1 from public.yak_family_links l where l.code = v_code);
    if i > 20 then raise exception 'code busy'; end if;
  end loop;
  insert into public.yak_family_links (owner_id, owner_label, code, code_expires, consent_at)
  values (v_uid, v_label, v_code, now() + interval '24 hours', now());
  return query select v_code, now() + interval '24 hours';
end $$;

-- ── 가족: 코드 넣기(한 시간 10번까지 · 자기 자신·이미 연결된 사람은 안 됨 · 틀린 코드는 0줄) ──
create or replace function public.yak_family_accept(p_code text)
returns table (link_id uuid, owner_label text)
language plpgsql security definer set search_path = public as $$
declare v_uid uuid := auth.uid(); v_link public.yak_family_links;
begin
  if v_uid is null then raise exception 'login required' using errcode = '28000'; end if;
  if (select count(*) from public.yak_family_tries t where t.user_id = v_uid and t.at > now() - interval '1 hour') >= 10 then
    raise exception 'too many tries' using errcode = '54000'; end if;
  insert into public.yak_family_tries (user_id) values (v_uid);
  -- 틀린 코드는 오류 대신 «빈 답»(0줄) — 오류를 내면 위의 횟수 기록까지 함께 취소돼 맞히기를 막지 못한다
  if coalesce(p_code, '') !~ '^[0-9]{6}$' then return; end if;
  select * into v_link from public.yak_family_links l
   where l.code = p_code and l.member_id is null and l.ended_at is null and l.code_expires > now() for update;
  if not found then return; end if;
  if v_link.owner_id = v_uid then raise exception 'self' using errcode = '22023'; end if;
  if exists (select 1 from public.yak_family_links l where l.owner_id = v_link.owner_id and l.member_id = v_uid and l.ended_at is null) then
    raise exception 'already linked' using errcode = '23505'; end if;
  update public.yak_family_links l set member_id = v_uid, member_consent_at = now(), accepted_at = now(), code = null, code_expires = null
   where l.id = v_link.id;
  delete from public.yak_family_tries t where t.at < now() - interval '1 day';
  return query select v_link.id, v_link.owner_label;
end $$;

-- ── 둘 다: 내 연결 보기 ──
-- role 'owner' = 내가 약 드시는 쪽(상대 = 알림 받는 가족), 'member' = 내가 알림 받는 쪽(상대 = 약 드시는 분)
create or replace function public.yak_family_list()
returns table (id uuid, role text, label text, other_email text, status text, code text, code_expires timestamptz, accepted_at timestamptz, muted_today boolean)
language sql security definer set search_path = public as $$
  select l.id, 'owner', l.owner_label, u.email::text,
         case when l.member_id is null then 'waiting' else 'linked' end,
         l.code, l.code_expires, l.accepted_at, l.muted_day = (now() at time zone 'Asia/Seoul')::date
    from public.yak_family_links l left join auth.users u on u.id = l.member_id
   where l.owner_id = auth.uid() and l.ended_at is null and (l.member_id is not null or l.code_expires > now())
  union all
  select l.id, 'member', l.owner_label, u.email::text, 'linked', null, null, l.accepted_at, l.muted_day = (now() at time zone 'Asia/Seoul')::date
    from public.yak_family_links l join auth.users u on u.id = l.owner_id
   where l.member_id = auth.uid() and l.ended_at is null
$$;

-- ── 둘 다: 끊기 ──
create or replace function public.yak_family_end(p_id uuid)
returns boolean language plpgsql security definer set search_path = public as $$
declare v_uid uuid := auth.uid(); v_n int;
begin
  if v_uid is null then raise exception 'login required' using errcode = '28000'; end if;
  update public.yak_family_links l
     set ended_at = now(), ended_by = case when l.owner_id = v_uid then 'owner' else 'member' end, code = null
   where l.id = p_id and l.ended_at is null and (l.owner_id = v_uid or l.member_id = v_uid);
  get diagnostics v_n = row_count; return v_n > 0;
end $$;

-- ── 본인: 모두 끊기(「서버에 저장하기」 동의를 거둘 때·가족 알림 끄기) ──
create or replace function public.yak_family_end_all()
returns int language plpgsql security definer set search_path = public as $$
declare v_uid uuid := auth.uid(); v_n int;
begin
  if v_uid is null then raise exception 'login required' using errcode = '28000'; end if;
  update public.yak_family_links l set ended_at = now(), ended_by = 'owner', code = null
   where l.owner_id = v_uid and l.ended_at is null;
  get diagnostics v_n = row_count; return v_n;
end $$;

-- ── 가족: 오늘은 그만 ──
create or replace function public.yak_family_mute(p_id uuid)
returns boolean language plpgsql security definer set search_path = public as $$
declare v_n int;
begin
  update public.yak_family_links l set muted_day = (now() at time zone 'Asia/Seoul')::date
   where l.id = p_id and l.member_id = auth.uid() and l.ended_at is null;
  get diagnostics v_n = row_count; return v_n > 0;
end $$;

-- ── 가족 기기: 알림 받을 곳 저장·지우기(한 사람 기기 5대까지) ──
create or replace function public.yak_push_save(p_endpoint text, p_p256dh text, p_auth text)
returns boolean language plpgsql security definer set search_path = public as $$
declare v_uid uuid := auth.uid();
begin
  if v_uid is null then raise exception 'login required' using errcode = '28000'; end if;
  insert into public.yak_push_subs (endpoint, user_id, p256dh, auth) values (p_endpoint, v_uid, p_p256dh, p_auth)
  on conflict (endpoint) do update set user_id = excluded.user_id, p256dh = excluded.p256dh, auth = excluded.auth, created_at = now();
  delete from public.yak_push_subs s where s.user_id = v_uid and s.endpoint not in
    (select s2.endpoint from public.yak_push_subs s2 where s2.user_id = v_uid order by s2.created_at desc limit 5);
  return true;
end $$;

create or replace function public.yak_push_drop(p_endpoint text)
returns boolean language plpgsql security definer set search_path = public as $$
declare v_n int;
begin
  delete from public.yak_push_subs s where s.endpoint = p_endpoint and s.user_id = auth.uid();
  get diagnostics v_n = row_count; return v_n > 0;
end $$;

revoke all on function public.yak_family_invite(text, boolean), public.yak_family_accept(text), public.yak_family_list(),
  public.yak_family_end(uuid), public.yak_family_end_all(), public.yak_family_mute(uuid),
  public.yak_push_save(text, text, text), public.yak_push_drop(text) from public, anon;
grant execute on function public.yak_family_invite(text, boolean), public.yak_family_accept(text), public.yak_family_list(),
  public.yak_family_end(uuid), public.yak_family_end_all(), public.yak_family_mute(uuid),
  public.yak_push_save(text, text, text), public.yak_push_drop(text) to authenticated;

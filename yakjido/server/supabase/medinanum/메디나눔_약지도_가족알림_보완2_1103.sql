-- ════════════════════════════════════════════════════════════════════════════
-- 약지도 알림 보완2(11-03 · GPT 개인정보 검수 + 「개인 맞춤」) — 메디나눔_약지도_가족알림_1102.sql «뒤에» 돌린다(보완_1103 을 합친 판)
--   ① 본인 허락 단계: 가족이 코드를 넣으면 «요청»(approved_at 비어 있음) → 본인이 상대 메일을 보고 허락해야 알림 시작
--   ② 연결을 끊거나 거절하면 연결 줄을 지운다(보낸 기록도 함께 — on delete cascade). 만료된 초대 코드도 지운다
--   ③ 코드 넣은 기록은 하루 지나면 지운다(초대·넣기 때마다)
--   ④ 「오늘만 끄기」를 가족 기기의 자정까지로(muted_until · 시간대 무관) — yak_family_mute(p_id, p_until)
--   ⑤ 본인 정시 알림 보낸 기록 yak_dose_sent(같은 날·같은 시각 한 번 · 30일 뒤 정리)
-- 추가형: 칸 하나 더하기 + 함수 바꾸기. 표를 없애는 문장은 없다(delete 는 함수 «본문» 안에만). 여러 번 돌려도 같다. ⛔ 비밀 키 없음.
-- ⚠️ Edge Function yak-family-check 도 같이 다시 배포(허락된 연결만 · 사람마다 시간대 · 본인 정시 알림 · 알림 글 바뀜).
-- ════════════════════════════════════════════════════════════════════════════

alter table public.yak_family_links add column if not exists approved_at timestamptz;   -- 본인이 허락한 때(비어 있으면 알림 안 감)
alter table public.yak_family_links add column if not exists muted_until timestamptz;   -- 가족이 「오늘만 끄기」— 가족 기기의 그날 자정까지

create table if not exists public.yak_dose_sent (
  user_id  uuid not null references auth.users(id) on delete cascade,
  day      date not null,
  slot     text not null check (slot ~ '^[0-2][0-9]:[0-5][0-9]$'),
  sent_at  timestamptz not null default now(),
  primary key (user_id, day, slot)
);
alter table public.yak_dose_sent enable row level security;
revoke all on public.yak_dose_sent from anon, authenticated;

-- 가족: 이 분 알림 오늘만 끄기(p_until = 가족 기기의 오늘 자정 · 2일 넘게는 못 정함)
create or replace function public.yak_family_mute(p_id uuid, p_until timestamptz)
returns boolean language plpgsql security definer set search_path = public as $$
declare v_n int;
begin
  if p_until is null or p_until <= now() or p_until > now() + interval '2 days' then raise exception 'bad until' using errcode = '22023'; end if;
  update public.yak_family_links l set muted_until = p_until
   where l.id = p_id and l.member_id = auth.uid() and l.ended_at is null;
  get diagnostics v_n = row_count; return v_n > 0;
end $$;

create or replace function public.yak_family_invite(p_label text, p_consent boolean)
returns table (code text, expires_at timestamptz)
language plpgsql security definer set search_path = public as $$
declare v_uid uuid := auth.uid(); v_label text := btrim(regexp_replace(coalesce(p_label, ''), '[[:cntrl:]<>]', '', 'g')); v_code text; v_n int; i int := 0;
begin
  if v_uid is null then raise exception 'login required' using errcode = '28000'; end if;
  if p_consent is not true then raise exception 'consent required' using errcode = '22023'; end if;
  if char_length(v_label) < 1 then v_label := '가족'; end if;
  v_label := left(v_label, 20);
  delete from public.yak_family_links l where l.member_id is null and l.code_expires < now();   -- 만료된 초대 코드
  delete from public.yak_family_tries t where t.at < now() - interval '1 day';
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

-- 가족: 코드 넣기 → 본인 허락을 기다리는 «요청». 틀린 코드는 0줄(오류를 내면 횟수 기록까지 취소돼 맞히기를 막지 못함)
create or replace function public.yak_family_accept(p_code text)
returns table (link_id uuid, owner_label text)
language plpgsql security definer set search_path = public as $$
declare v_uid uuid := auth.uid(); v_link public.yak_family_links;
begin
  if v_uid is null then raise exception 'login required' using errcode = '28000'; end if;
  if (select count(*) from public.yak_family_tries t where t.user_id = v_uid and t.at > now() - interval '1 hour') >= 10 then
    raise exception 'too many tries' using errcode = '54000'; end if;
  insert into public.yak_family_tries (user_id) values (v_uid);
  if coalesce(p_code, '') !~ '^[0-9]{6}$' then return; end if;
  select * into v_link from public.yak_family_links l
   where l.code = p_code and l.member_id is null and l.ended_at is null and l.code_expires > now() for update;
  if not found then return; end if;
  if v_link.owner_id = v_uid then raise exception 'self' using errcode = '22023'; end if;
  if exists (select 1 from public.yak_family_links l where l.owner_id = v_link.owner_id and l.member_id = v_uid and l.ended_at is null) then
    raise exception 'already linked' using errcode = '23505'; end if;
  update public.yak_family_links l set member_id = v_uid, member_consent_at = now(), accepted_at = now(), code = null, code_expires = null, approved_at = null
   where l.id = v_link.id;
  return query select v_link.id, v_link.owner_label;
end $$;

-- 본인: 요청 허락(p_ok true) 또는 거절(false → 줄을 지움)
create or replace function public.yak_family_approve(p_id uuid, p_ok boolean)
returns boolean language plpgsql security definer set search_path = public as $$
declare v_uid uuid := auth.uid(); v_n int;
begin
  if v_uid is null then raise exception 'login required' using errcode = '28000'; end if;
  if p_ok then
    update public.yak_family_links l set approved_at = now()
     where l.id = p_id and l.owner_id = v_uid and l.member_id is not null and l.approved_at is null and l.ended_at is null;
  else
    delete from public.yak_family_links l where l.id = p_id and l.owner_id = v_uid and l.approved_at is null;
  end if;
  get diagnostics v_n = row_count; return v_n > 0;
end $$;

-- 둘 다: 내 연결 보기. 본인 쪽 status: waiting(코드 대기) · asking(가족이 요청 — 허락 필요) · linked / 가족 쪽: asking(본인 허락 기다림) · linked
create or replace function public.yak_family_list()
returns table (id uuid, role text, label text, other_email text, status text, code text, code_expires timestamptz, accepted_at timestamptz, muted_today boolean)
language sql security definer set search_path = public as $$
  select l.id, 'owner', l.owner_label, u.email::text,
         case when l.member_id is null then 'waiting' when l.approved_at is null then 'asking' else 'linked' end,
         l.code, l.code_expires, l.accepted_at, coalesce(l.muted_until > now(), false)
    from public.yak_family_links l left join auth.users u on u.id = l.member_id
   where l.owner_id = auth.uid() and l.ended_at is null and (l.member_id is not null or l.code_expires > now())
  union all
  select l.id, 'member', l.owner_label, u.email::text, case when l.approved_at is null then 'asking' else 'linked' end,
         null, null, l.accepted_at, coalesce(l.muted_until > now(), false)
    from public.yak_family_links l join auth.users u on u.id = l.owner_id
   where l.member_id = auth.uid() and l.ended_at is null
$$;

-- 둘 다: 끊기 = 연결 줄을 지움(보낸 기록도 함께)
create or replace function public.yak_family_end(p_id uuid)
returns boolean language plpgsql security definer set search_path = public as $$
declare v_uid uuid := auth.uid(); v_n int;
begin
  if v_uid is null then raise exception 'login required' using errcode = '28000'; end if;
  delete from public.yak_family_links l where l.id = p_id and (l.owner_id = v_uid or l.member_id = v_uid);
  get diagnostics v_n = row_count; return v_n > 0;
end $$;

create or replace function public.yak_family_end_all()
returns int language plpgsql security definer set search_path = public as $$
declare v_uid uuid := auth.uid(); v_n int;
begin
  if v_uid is null then raise exception 'login required' using errcode = '28000'; end if;
  delete from public.yak_family_links l where l.owner_id = v_uid;
  get diagnostics v_n = row_count; return v_n;
end $$;

revoke all on function public.yak_family_approve(uuid, boolean), public.yak_family_list(), public.yak_family_mute(uuid, timestamptz) from public, anon;
grant execute on function public.yak_family_approve(uuid, boolean), public.yak_family_list(), public.yak_family_mute(uuid, timestamptz) to authenticated;

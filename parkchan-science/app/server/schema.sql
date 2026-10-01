-- 박찬 과학 앱 — Supabase(Postgres) 스키마 v3 · 2026-09-29
-- 앱의 서버 어댑터(app-shell.html 의 serverDB)와 1:1 로 맞춘 표·함수·행 단위 보안(RLS)이다.
-- 새 프로젝트의 SQL Editor 에 통째로 붙여 넣고 한 번 실행한다. 여러 번 실행해도 된다.
-- 실행 뒤 맨 아래 [설정] 두 줄(원장 이메일·출석 씨앗)을 원장님 값으로 바꿔 한 번 더 실행한다.
--
-- 보안 원칙
--  · 학생·보호자가 직접 고칠 수 있는 칸은 이름·연락처·닉네임뿐이다. 역할·이용권 만료일·학원 코드는 함수로만 바뀐다.
--  · 학원 코드 연결은 link_code() 한 곳 — 틀린 코드는 1시간에 10번까지, 한 학생 코드는 학생 계정 하나에만.
--  · 원장 = 설정한 이메일로 가입해 메일 인증을 마친 계정 → 그 뒤 owner_uid 로 못 박으면 그 계정만.
--  · 코드 추측: 계정당 10번 · 같은 IP 30번 · 전체 300번(1시간, 틀린 것만) — 계정을 여러 개 만들어도 막힌다.
--  · 날짜·시각은 모두 한국 시간(Asia/Seoul). 서버 기본값(UTC)이면 저녁 수업이 지각으로 안 잡힌다.

create extension if not exists pgcrypto;
do $$ begin execute format('alter database %I set timezone to %L', current_database(), 'Asia/Seoul'); end $$;
set timezone to 'Asia/Seoul';

-- ── 비공개 설정(앱 API 로는 보이지 않는 스키마) ──
create schema if not exists private;
revoke all on schema private from public;
create table if not exists private.config (k text primary key, v text not null);
-- 보호자 동의 링크(한 번 쓰면 끝 · 7일)
create table if not exists private.consent_links (token text primary key, uid uuid not null, at timestamptz not null default now(), used_at timestamptz);
-- 틀린 코드 입력 기록(학원 코드·출석 코드·이용권 코드 무차별 대입 방지)
create table if not exists private.attempts (uid uuid, kind text not null, ok boolean not null, at timestamptz not null default now());
alter table private.attempts add column if not exists ip text;
create index if not exists attempts_kind_at on private.attempts (kind, at desc) where not ok;
create index if not exists attempts_idx on private.attempts (uid, kind, at desc);

create or replace function kst_today() returns date language sql stable as $$ select (now() at time zone 'Asia/Seoul')::date $$;
create or replace function kst_time()  returns time language sql stable as $$ select (now() at time zone 'Asia/Seoul')::time(0) $$;

-- ═══ 표 ═══
create table if not exists students (
  code   text primary key,                          -- 6자리, 원장 앱이 발급
  name   text not null,
  cls    text not null,
  phone  text not null default '',
  until  date not null,                             -- 수강 만료일. 지나면 앱이 저절로 닫힌다
  joined date not null default kst_today()
);
create table if not exists classes (cls text primary key, start_time time not null);
insert into classes values ('월목반','18:00'), ('화금반','18:00'), ('수토반','14:00') on conflict do nothing;

create table if not exists attendance (
  code   text not null references students(code) on delete cascade,
  date   date not null default kst_today(),
  time   time not null default kst_time(),
  late   boolean not null default false,
  manual boolean not null default false,            -- 원장님이 명단에서 직접 체크
  primary key (code, date)
);
create table if not exists notices (
  id uuid primary key default gen_random_uuid(),
  cls text not null, title text not null, body text not null default '',
  at timestamptz not null default now()
);
create table if not exists notice_reads (
  notice_id uuid not null references notices(id) on delete cascade,
  code text not null references students(code) on delete cascade,
  at timestamptz not null default now(),
  primary key (notice_id, code)
);
create table if not exists sched (
  id uuid primary key default gen_random_uuid(),
  cls text not null, date date not null, title text not null,
  kind text not null default 'etc', memo text not null default '',
  at timestamptz not null default now()
);
create index if not exists sched_date_idx on sched (date);

-- 계정 프로필 — 가입하면 트리거가 만든다(메일 인증을 켜 두어도 역할·보호자 정보가 빠지지 않게)
create table if not exists profiles (
  id           uuid primary key references auth.users(id) on delete cascade,
  role         text not null default 'student' check (role in ('student','parent','owner')),
  name         text not null default '',
  phone        text not null default '',
  nick         text not null default '',
  student_code text references students(code) on delete set null,
  pass_until   date,
  under14      boolean not null default false,       -- 만 14세 미만(법정대리인 동의)
  guardian     text not null default '',             -- 법정대리인 성명·연락처
  terms_ver    text not null default '',             -- 동의한 약관 판(날짜)
  guardian_ok  boolean not null default false,       -- 만 14세 미만: 법정대리인 동의를 확인했는가
  guardian_how text not null default '',             -- 'web'(동의 페이지) · 'paper'(서면)
  guardian_at  timestamptz,                          -- 동의 시각
  guardian_notified_at timestamptz,                  -- 웹 동의를 확인했다고 보호자에게 문자로 알린 시각
  agreed_at    timestamptz,
  created_at   timestamptz not null default now()
);
-- 보호자 ↔ 자녀(여러 명 가능 — 형제가 같은 학원에 다닐 때). 한 자녀에 보호자도 여럿 가능
create table if not exists guardian_links (
  uid  uuid not null references auth.users(id) on delete cascade,
  code text not null references students(code) on delete cascade,
  at   timestamptz not null default now(),
  primary key (uid, code)
);
-- 보호자 연결은 원장이 확인해야 열린다 — 코드만 알면 반 친구도 '보호자'로 출석 알림·연락처를 받던 것(2026-10-01 점검에서 재현)
alter table guardian_links add column if not exists approved boolean not null default false;
alter table guardian_links add column if not exists decided_at timestamptz;
-- 한 학생 코드는 학생 계정 하나에만(코드 돌려쓰기 방지). 보호자는 여럿 연결 가능
create unique index if not exists profiles_student_code_uq on profiles (student_code) where student_code is not null;

-- 학습 진도 — 키는 학생 코드 또는 'u:'||계정 id(학원 밖 이용자)
create table if not exists progress (
  code  text primary key,
  state jsonb not null default '{}'::jsonb,
  at    timestamptz not null default now()
);

create table if not exists passes (
  code text primary key, days int not null check (days between 1 and 800),
  issued date not null default kst_today(),
  used_by uuid references auth.users(id) on delete set null, used_at date
);
-- 스토어 결제 영수증(검증 함수가 서비스 키로만 쓴다) — 같은 영수증은 한 번만 반영
create table if not exists purchases (
  purchase_token text primary key,
  uid        uuid references auth.users(id) on delete set null,   -- 탈퇴해도 결제 기록은 5년 보관(전자상거래법) — 누구 것인지만 끊는다
  product    text not null,
  order_id   text,
  platform   text not null default 'android',
  days       int not null,
  until      date not null,
  raw        jsonb,
  at         timestamptz not null default now()
);
alter table purchases add column if not exists revoked_at timestamptz;   -- 환불·취소 — 줄은 지우지 않는다(같은 영수증 재사용 막기 · 5년 보관)

-- 공부 노트 — 나만 보는 메모장. 원장·보호자도 못 본다(진도와 달리 owner_read 정책이 없다).
-- id 는 앱이 만든다(오프라인에서 쓰고 나중에 올려도 같은 노트로 합쳐지게)
create table if not exists notes (
  id         uuid primary key,
  uid        uuid not null default auth.uid() references auth.users(id) on delete cascade,
  date       date not null,
  title      text not null default '' check (char_length(title) <= 80),
  body       text not null default '' check (char_length(body) <= 5000),
  cids       text[] not null default '{}' check (cardinality(cids) <= 12),
  updated_at timestamptz not null default now(),
  created_at timestamptz not null default now()
);
create index if not exists notes_uid_date on notes (uid, date);
create or replace function private.note_guard() returns trigger language plpgsql security definer set search_path = public as $$
begin
  if auth.uid() is not null then new.uid := auth.uid(); end if;   -- 앱에서 오는 요청은 늘 본인 것으로(남의 계정으로 넣기 막기) · 관리용 SQL 은 그대로
  if tg_op = 'UPDATE' then
    new.created_at := old.created_at;
    if new.updated_at < old.updated_at then return null; end if;   -- 더 오래된 수정(늦게 올라온 옛 기기의 것)은 버린다 — 나중에 고친 쪽이 이긴다
  end if;
  return new;
end $$;
drop trigger if exists notes_guard on notes;
create trigger notes_guard before insert or update on notes for each row execute function private.note_guard();
-- 개수 제한은 '정말 새로 들어간 뒤'에 센다 — 올리기(upsert)의 BEFORE INSERT 는 이미 있는 노트를 고칠 때도 불리므로
create or replace function private.note_limit() returns trigger language plpgsql security definer set search_path = public as $$
begin
  if (select count(*) from notes where uid = new.uid) > 3000 then
    raise exception 'note_limit' using hint = '노트는 3,000개까지 저장됩니다';
  end if;
  return null;
end $$;
drop trigger if exists notes_limit on notes;
create trigger notes_limit after insert on notes for each row execute function private.note_limit();

-- 의견 보내기 · 교재 오류 신고 — 보낸 사람과 원장만 본다. 하루 10건 · 1년 뒤 파기 · 만 14세 미만은 보호자 동의 뒤
create table if not exists feedback (
  id      bigint generated always as identity primary key,
  uid     uuid not null default auth.uid() references auth.users on delete cascade,
  kind    text not null check (kind in ('content','bug','idea','other')),   -- 교재·문제 오류 / 앱 오류 / 제안 / 기타
  body    text not null check (char_length(body) between 2 and 1000),
  ref     text check (ref is null or ref ~ '^(concept|quiz|bank|lab):[A-Za-z0-9_#.-]{1,60}$'),   -- 어느 개념·문제에서 보냈는지
  ver     text check (ver is null or char_length(ver) <= 40),
  care    boolean not null default false,                                    -- 힘든 마음이 담긴 글(이야기와 같은 규칙)
  at      timestamptz not null default now(),
  done_at timestamptz
);
create index if not exists feedback_open on feedback (at desc) where done_at is null;
-- 어디서 보냈는지에 이야기('talk:appeal' — 이용 제한을 다시 봐 달라는 요청)도
alter table feedback drop constraint if exists feedback_ref_check;
alter table feedback add constraint feedback_ref_check check (ref is null or ref ~ '^(concept|quiz|bank|lab|talk):[A-Za-z0-9_#.-]{1,60}$');
create or replace function private.feedback_guard() returns trigger language plpgsql security definer set search_path = public, private as $$
begin
  new.uid := auth.uid(); new.at := now(); new.done_at := null; new.care := private.care_hit(new.body);
  if (select count(*) from feedback where uid = new.uid and at > now() - interval '1 day') >= 10 then
    raise exception '의견은 하루 10건까지 보낼 수 있습니다.' using errcode = '54000'; end if;
  return new;
end $$;
drop trigger if exists feedback_guard on feedback;
create trigger feedback_guard before insert on feedback for each row execute function private.feedback_guard();

-- 이야기(커뮤니티)
create table if not exists posts (
  id        uuid primary key default gen_random_uuid(),
  author    uuid not null default auth.uid() references auth.users(id) on delete cascade,
  nick      text not null default '익명',
  board     text not null default 'qna' check (board in ('qna','share','talk')),
  title     text not null check (char_length(title) between 1 and 80),
  body      text not null default '' check (char_length(body) <= 4000),
  attach    jsonb,
  likes     uuid[] not null default '{}',
  report_n  int not null default 0,                -- 신고 수(누가 신고했는지는 reports 표 — API 로 보이지 않는다)
  comment_n int not null default 0,
  staff     boolean not null default false,          -- 원장(선생님)이 쓴 글 — 서버가 표시한다
  solved    boolean not null default false,
  deleted   boolean not null default false,
  at        timestamptz not null default now(),
  edited    timestamptz
);
create table if not exists comments (
  id      uuid primary key default gen_random_uuid(),
  post_id uuid not null references posts(id) on delete cascade,
  author  uuid not null default auth.uid() references auth.users(id) on delete cascade,
  nick    text not null default '익명',
  body    text not null check (char_length(body) between 1 and 1500),
  likes   uuid[] not null default '{}',
  report_n int not null default 0,
  staff   boolean not null default false,             -- 선생님 답변
  picked  boolean not null default false,
  deleted boolean not null default false,
  at      timestamptz not null default now()
);
create index if not exists posts_at_idx      on posts (at desc);
create index if not exists comments_post_idx on comments (post_id, at);

-- 신고 — 한 사람이 한 글(댓글)에 한 번. 사유를 고르고, '친구가 걱정돼요'(worry)는 가리지 않고 원장에게 먼저 알린다.
--  원장이 '신고 되돌리기'(kept)·지우기(removed)를 하면 그 신고는 끝난다 — 끝난 신고를 낸 사람이 다시 눌러도 다시 세지 않는다
--  (되돌린 글이 같은 학생들 신고로 다시 가려지던 것 · docs/11 §11). 신고한 사람에게는 결과를 짧게 알린다(my_reports).
create table if not exists reports (
  id          bigint generated always as identity primary key,
  post_id     uuid references posts(id) on delete cascade,
  comment_id  uuid references comments(id) on delete cascade,
  uid         uuid not null references auth.users(id) on delete cascade,
  reason      text not null default 'other' check (reason in ('privacy','bully','harm','ad','copy','other','worry')),
  state       text not null default 'open' check (state in ('open','kept','removed')),
  at          timestamptz not null default now(),
  resolved_at timestamptz,
  seen_at     timestamptz,                             -- 신고한 사람이 결과 안내를 본 때
  check ((post_id is null) <> (comment_id is null))
);
create unique index if not exists reports_post_uq    on reports (post_id, uid, (reason = 'worry')) where post_id is not null;
create unique index if not exists reports_comment_uq on reports (comment_id, uid, (reason = 'worry')) where comment_id is not null;
create index if not exists reports_uid_idx on reports (uid, at desc);
-- 예전 판(신고한 사람 배열 posts.reports)에서 옮긴다 — 여러 번 실행해도 된다
do $$ begin
  if exists (select 1 from information_schema.columns where table_schema = 'public' and table_name = 'posts' and column_name = 'reports') then
    execute $q$insert into reports (post_id, uid) select p.id, r from posts p, unnest(p.reports) r where exists (select 1 from auth.users u where u.id = r) on conflict do nothing$q$;
    alter table posts drop column reports; end if;
  if exists (select 1 from information_schema.columns where table_schema = 'public' and table_name = 'comments' and column_name = 'reports') then
    execute $q$insert into reports (comment_id, uid) select c.id, r from comments c, unnest(c.reports) r where exists (select 1 from auth.users u where u.id = r) on conflict do nothing$q$;
    alter table comments drop column reports; end if;
end $$;

-- 이야기 이용 제한(약관 제8조의3 ①②) — 원장만 건다. 이 날짜까지(한국 날짜) 글·댓글·도움됨을 못 한다(읽기는 된다). 'infinity' = 중지
alter table profiles add column if not exists talk_until  date;
alter table profiles add column if not exists talk_reason text not null default '';   -- 학생에게 보이는 짧은 사유
-- 제한 기록(누가 언제 무엇을 · 원장 메모) — 원장만 함수로 본다 · 6개월 뒤 파기(purge_old)
create table if not exists talk_log (
  id       bigint generated always as identity primary key,
  uid      uuid not null references auth.users(id) on delete cascade,
  action   text not null check (action in ('d7','d30','stop','lift')),
  reason   text not null default '' check (char_length(reason) <= 40),
  memo     text not null default '' check (char_length(memo) <= 300),
  guardian boolean not null default false,              -- 보호자 요청으로 건 제한
  until    date,
  at       timestamptz not null default now()
);
create index if not exists talk_log_uid on talk_log (uid, at desc);

-- 밤(22~07시) 동안 미룬 댓글 알림 — 아침 7시에 '밤사이 새 댓글이 있어요'로 한 번 보내고 지운다(push 함수 · 서비스 키 전용)
create table if not exists push_later (
  uid     uuid not null references auth.users(id) on delete cascade,
  post_id uuid,
  at      timestamptz not null default now()
);

-- 푸시 알림 받을 기기 · 앱 오류 기록
create table if not exists push_tokens (
  token    text primary key,
  uid      uuid not null references auth.users(id) on delete cascade,
  platform text not null default 'android',
  at       timestamptz not null default now()
);
create table if not exists client_errors (
  id  bigserial primary key,
  at  timestamptz not null default now(),
  uid uuid default auth.uid(),
  ver text not null default '' check (char_length(ver) <= 40),
  msg text not null check (char_length(msg) <= 500),
  stack text not null default '' check (char_length(stack) <= 2000),
  url text not null default '' check (char_length(url) <= 300),
  ua  text not null default '' check (char_length(ua) <= 300)
);

-- ═══ 누가 누구인가 ═══
-- 원장 판정: 원장이 가입·메일 인증을 마친 뒤 owner_uid 로 계정을 못 박으면(README 순서 ③) 그 계정만 원장.
-- 못 박기 전에는 설정한 이메일 + 메일 인증 완료 계정. (메일 인증을 꺼 두면 먼저 그 이메일로 가입한 사람이 원장이 될 수 있어 못 박기가 꼭 필요)
create or replace function is_owner() returns boolean language sql stable security definer set search_path = public, private as $$
  select case when exists (select 1 from private.config where k = 'owner_uid')
    then exists (select 1 from private.config c join auth.users u on u.id::text = c.v where c.k = 'owner_uid' and u.id = auth.uid() and u.email_confirmed_at is not null)
    else exists (select 1 from auth.users u join private.config c on c.k = 'owner_email'
                 where u.id = auth.uid() and lower(u.email) = lower(c.v) and u.email_confirmed_at is not null) end;
$$;
create or replace function my_student_code() returns text language sql stable security definer set search_path = public as $$
  select student_code from profiles where id = auth.uid() and role = 'student' $$;
create or replace function my_codes() returns setof text language sql stable security definer set search_path = public as $$
  select student_code from profiles where id = auth.uid() and student_code is not null
  union select code from guardian_links where uid = auth.uid() and approved $$;
create or replace function my_classes() returns setof text language sql stable security definer set search_path = public as $$
  select cls from students where code in (select my_codes()) and until >= kst_today() $$;

-- 틀린 입력 제한: 최근 1시간 실패가 n번 이상이면 true
-- 요청한 기기의 IP(PostgREST 가 넘기는 헤더) — 없으면 null
create or replace function private.req_ip() returns text language sql stable as $$
  with h as (select nullif(current_setting('request.headers', true), '')::json j)
  select nullif(trim(coalesce(j->>'cf-connecting-ip', split_part(coalesce(j->>'x-forwarded-for', ''), ',', 1))), '') from h $$;   -- 앞단(Cloudflare)이 채운 값을 먼저 · 위조해도 계정당·전체 한도는 그대로
-- 코드 추측 막기: 계정당 n번 · 같은 IP 3n번 · 학원 전체 300번(1시간, 틀린 것만). 계정을 여러 개 만들어 돌려도 전체 한도에 걸린다
create or replace function private.too_many(k text, n int) returns boolean language sql stable security definer set search_path = private as $$
  select (select count(*) from private.attempts where uid = auth.uid() and kind = k and not ok and at > now() - interval '1 hour') >= n
      or (private.req_ip() is not null and (select count(*) from private.attempts where ip = private.req_ip() and kind = k and not ok and at > now() - interval '1 hour') >= n * 3)
      or (select count(*) from private.attempts where kind = k and not ok and at > now() - interval '1 hour') >= 300 $$;
create or replace function private.note(k text, good boolean) returns void language sql security definer set search_path = private as $$
  insert into private.attempts(uid, kind, ok, ip) values (auth.uid(), k, good, case when good then null else private.req_ip() end) $$;   -- IP 는 틀린 입력에만(최소 수집 · 하루 뒤 파기)

-- ═══ 가입하면 프로필을 만든다(역할은 학생·보호자만 — 원장은 설정한 이메일만) ═══
create or replace function private.on_signup() returns trigger language plpgsql security definer set search_path = public, private as $$
declare m jsonb := coalesce(new.raw_user_meta_data, '{}'::jsonb); r text := coalesce(m->>'role', 'student');
begin
  if r not in ('student','parent') then r := 'student'; end if;
  if not exists (select 1 from private.config where k = 'owner_uid')
     and exists (select 1 from private.config where k = 'owner_email' and lower(v) = lower(new.email)) then r := 'owner'; end if;   -- 원장 계정을 못 박은 뒤에는 새 가입자에게 원장 역할을 주지 않는다
  insert into profiles (id, role, name, phone, under14, guardian, terms_ver, agreed_at)
  values (new.id, r, left(coalesce(m->>'name',''), 40), left(coalesce(m->>'phone',''), 20),
          coalesce((m->>'under14')::boolean, false), left(coalesce(m->>'guardian',''), 60),
          left(coalesce(m->>'terms_ver',''), 20), case when m ? 'terms_ver' then now() end)
  on conflict (id) do nothing;
  return new;
end $$;
drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created after insert on auth.users for each row execute function private.on_signup();

-- ═══ 학원 코드 연결(학생) · 자녀 연결(보호자) ═══
-- p_code 가 빈 값이면 연결 해제. 성공하면 학생 정보를 돌려준다.
create or replace function link_code(p_kind text, p_code text) returns json language plpgsql security definer set search_path = public, private as $$
declare u uuid := auth.uid(); pr profiles; s students; c text := upper(trim(coalesce(p_code, '')));
begin
  if u is null then return json_build_object('ok', false, 'why', '로그인이 필요합니다.'); end if;
  select * into pr from profiles where id = u;
  if not found then return json_build_object('ok', false, 'why', '계정 정보를 찾을 수 없습니다. 다시 로그인해 주세요.'); end if;
  if p_kind not in ('student','child') then return json_build_object('ok', false, 'why', '잘못된 요청입니다.'); end if;
  if c = '' then
    if p_kind = 'student' then update profiles set student_code = null where id = u; else delete from guardian_links where uid = u; end if;
    return json_build_object('ok', true);
  end if;
  if private.too_many('code', 10) then return json_build_object('ok', false, 'why', '코드를 여러 번 틀렸습니다. 1시간 뒤에 다시 시도하거나 원장님께 문의해 주세요.'); end if;
  select * into s from students where code = c;
  if not found then perform private.note('code', false); return json_build_object('ok', false, 'why', '등록되지 않은 코드입니다. 원장님께 받은 코드를 확인해 주세요.'); end if;
  if s.until < kst_today() then perform private.note('code', false); return json_build_object('ok', false, 'why', '수강 기간이 ' || to_char(s.until, 'FMMM"월" FMDD"일"') || '에 끝났습니다. 원장님께 문의해 주세요.'); end if;
  if p_kind = 'student' then
    if pr.role <> 'student' then return json_build_object('ok', false, 'why', '학생 계정에서만 학원 코드를 등록할 수 있습니다.'); end if;
    if exists (select 1 from profiles where student_code = c and id <> u) then
      perform private.note('code', false); return json_build_object('ok', false, 'why', '이 코드는 이미 다른 학생 계정에 연결되어 있습니다. 원장님께 문의해 주세요.'); end if;
    update profiles set student_code = c, name = case when name = '' then s.name else name end where id = u;
  else
    if pr.role <> 'parent' then return json_build_object('ok', false, 'why', '보호자 계정에서만 자녀를 연결할 수 있습니다.'); end if;
    if (select count(*) from guardian_links where uid = u) >= 5 and not exists (select 1 from guardian_links where uid = u and code = c) then
      return json_build_object('ok', false, 'why', '자녀는 다섯 명까지 연결할 수 있습니다.'); end if;
    insert into guardian_links(uid, code) values (u, c) on conflict do nothing;
    perform private.note('code', true);
    if not exists (select 1 from guardian_links where uid = u and code = c and approved) then
      return json_build_object('ok', true, 'pending', true);   -- 원장 확인 전에는 자녀 이름도 보여 주지 않는다
    end if;
    return json_build_object('ok', true, 'student', json_build_object('code', s.code, 'name', s.name, 'cls', s.cls, 'until', s.until));
  end if;
  perform private.note('code', true);
  return json_build_object('ok', true, 'student', json_build_object('code', s.code, 'name', s.name, 'cls', s.cls, 'until', s.until));
end $$;

-- 원장: 학생 코드에 묶인 계정을 풀어 준다(학생이 계정을 새로 만들었을 때)
create or replace function release_code(p_code text) returns int language plpgsql security definer set search_path = public as $$
declare n int;
begin
  if not is_owner() then raise exception 'owner only' using errcode = '42501'; end if;
  update profiles set student_code = null where student_code = p_code; get diagnostics n = row_count; return n;
end $$;
-- 원장: 학생 코드에 연결된 계정 수(학생·보호자)
create or replace function linked_of(p_code text) returns json language sql stable security definer set search_path = public as $$
  select case when is_owner() then json_build_object(
    'student', (select count(*) from profiles where student_code = p_code),
    'guardians', coalesce((select json_agg(json_build_object('uid', g.uid, 'name', p.name, 'phone', p.phone, 'approved', g.approved, 'at', g.at) order by g.at) from guardian_links g join profiles p on p.id = g.uid where g.code = p_code), '[]'::json))
  end $$;
-- 원장: 보호자 연결 요청(확인 전) 목록 · 확인/거절(거절·해제는 연결을 지운다)
create or replace function guardian_requests() returns json language plpgsql stable security definer set search_path = public as $$
begin
  if not is_owner() then return '[]'::json; end if;
  return coalesce((select json_agg(x order by x.at) from (
    select g.uid, g.code, g.at, p.name, p.phone, u.email, s.name as student, s.cls
      from guardian_links g join profiles p on p.id = g.uid join auth.users u on u.id = g.uid join students s on s.code = g.code
     where not g.approved limit 200) x), '[]'::json);
end $$;
create or replace function guardian_decide(p_uid uuid, p_code text, p_ok boolean) returns void language plpgsql security definer set search_path = public as $$
begin
  if not is_owner() then raise exception 'owner only' using errcode = '42501'; end if;
  if p_ok then update guardian_links set approved = true, decided_at = now() where uid = p_uid and code = p_code;
  else delete from guardian_links where uid = p_uid and code = p_code; end if;
end $$;
-- 학생: 내 코드에 연결된(확인된) 보호자 — 누가 내 출석·진도를 보는지 학생도 안다
create or replace function my_guardians() returns json language sql stable security definer set search_path = public as $$
  select coalesce(json_agg(json_build_object('name', p.name, 'at', g.decided_at) order by g.decided_at), '[]'::json)
    from guardian_links g join profiles p on p.id = g.uid
   where g.approved and g.code = (select student_code from profiles where id = auth.uid() and role = 'student') $$;

-- 보호자: 자녀 한 명만 연결 해제
create or replace function unlink_child(p_code text) returns void language sql security definer set search_path = public as $$
  delete from guardian_links where uid = auth.uid() and code = upper(trim(coalesce(p_code, ''))) $$;

-- ═══ 출석 ═══
create or replace function private.attend_code(win bigint) returns text language sql stable security definer set search_path = private as $$
  select lpad(((('x' || substr(md5(coalesce((select v from private.config where k = 'attend_secret'), '') || ':' || win), 1, 8))::bit(32)::bigint) % 10000)::text, 4, '0') $$;
create or replace function private.attend(p_code text, p_manual boolean) returns json language plpgsql security definer set search_path = public as $$
declare s students; st time; t time := kst_time(); r attendance;
begin
  select * into s from students where code = p_code;
  select start_time into st from classes where cls = s.cls;
  insert into attendance(code, date, time, late, manual) values (p_code, kst_today(), t, t > coalesce(st, '18:00'), p_manual)
    on conflict (code, date) do nothing returning * into r;
  if r.code is null then select * into r from attendance where code = p_code and date = kst_today();
    return json_build_object('ok', true, 'dup', true, 'time', to_char(r.time, 'HH24:MI'), 'late', r.late); end if;
  return json_build_object('ok', true, 'time', to_char(r.time, 'HH24:MI'), 'late', r.late);
end $$;
-- 학생 앱: 자기 계정에 연결된 코드로만, 입구 화면의 30초 코드가 맞을 때만
create or replace function mark_attend(p_code text, p_entered text) returns json language plpgsql security definer set search_path = public, private as $$
declare w bigint := floor(extract(epoch from now()) / 30); mine text := my_student_code();
begin
  if mine is null or mine <> p_code then return json_build_object('ok', false, 'why', '이 계정에 연결된 학원 코드가 아닙니다.'); end if;
  if not exists (select 1 from students where code = p_code and until >= kst_today()) then
    return json_build_object('ok', false, 'why', '수강 기간이 끝난 코드입니다. 원장님께 문의해 주세요.'); end if;
  if private.too_many('attend', 6) then return json_build_object('ok', false, 'why', '여러 번 틀렸습니다. 원장님께 직접 출석 체크를 부탁해 주세요.'); end if;
  if coalesce(p_entered, '') not in (private.attend_code(w), private.attend_code(w - 1)) then
    perform private.note('attend', false);
    return json_build_object('ok', false, 'why', '코드가 맞지 않습니다. 입구 화면의 지금 숫자를 다시 봐 주세요.'); end if;
  return private.attend(p_code, false);
end $$;
create or replace function mark_attend_manual(p_code text) returns json language plpgsql security definer set search_path = public, private as $$
begin
  if not is_owner() then raise exception 'owner only' using errcode = '42501'; end if;
  if not exists (select 1 from students where code = p_code) then return json_build_object('ok', false, 'why', '학생을 찾을 수 없습니다.'); end if;
  return private.attend(p_code, true);
end $$;
create or replace function current_attend_code() returns json language plpgsql security definer set search_path = public, private as $$
declare w bigint := floor(extract(epoch from now()) / 30);
begin
  if not is_owner() then raise exception 'owner only' using errcode = '42501'; end if;
  return json_build_object('code', private.attend_code(w), 'win', w);
end $$;

-- ═══ 이용권 ═══
create or replace function redeem_pass(p_code text) returns json language plpgsql security definer set search_path = public, private as $$
declare p passes; base date; c text := upper(trim(coalesce(p_code, '')));
begin
  if auth.uid() is null then return json_build_object('ok', false, 'why', '로그인이 필요합니다.'); end if;
  if private.too_many('pass', 10) then return json_build_object('ok', false, 'why', '코드를 여러 번 틀렸습니다. 1시간 뒤에 다시 시도해 주세요.'); end if;
  select * into p from passes where code = c for update;
  if not found then perform private.note('pass', false); return json_build_object('ok', false, 'why', '없는 이용권 코드입니다.'); end if;
  if p.used_by is not null then perform private.note('pass', false); return json_build_object('ok', false, 'why', '이미 사용된 코드입니다.'); end if;
  select greatest(coalesce(pass_until, kst_today()), kst_today()) into base from profiles where id = auth.uid() for update;   -- 결제 반영과 동시에 와도 기간이 덮이지 않게
  update profiles set pass_until = base + p.days where id = auth.uid();
  update passes set used_by = auth.uid(), used_at = kst_today() where code = c;
  perform private.note('pass', true);
  return json_build_object('ok', true, 'until', (base + p.days)::text);
end $$;
-- 스토어 결제 반영 — verify-purchase 함수(서비스 키)만 부른다. 같은 영수증은 두 번 반영하지 않는다
create or replace function grant_purchase(p_uid uuid, p_token text, p_product text, p_order text, p_days int, p_raw jsonb) returns json
language plpgsql security definer set search_path = public as $$
declare base date; u date; old purchases;
begin
  select * into old from purchases where purchase_token = p_token for update;
  if found and old.revoked_at is not null then return json_build_object('ok', false, 'revoked', true, 'why', '환불·취소된 결제입니다.'); end if;
  if found and old.uid is distinct from p_uid then return json_build_object('ok', false, 'why', '다른 계정으로 반영된 결제입니다.'); end if;   -- 남이 먼저 낸 영수증을 '반영됨'으로 속이지 않게
  if found then return json_build_object('ok', true, 'dup', true, 'until', old.until::text); end if;
  select greatest(coalesce(pass_until, kst_today()), kst_today()) into base from profiles where id = p_uid for update;
  if base is null then return json_build_object('ok', false, 'why', 'no profile'); end if;
  u := base + p_days;
  insert into purchases(purchase_token, uid, product, order_id, days, until, raw) values (p_token, p_uid, p_product, p_order, p_days, u, p_raw);
  update profiles set pass_until = u where id = p_uid;
  return json_build_object('ok', true, 'until', u::text);
end $$;
-- 환불·취소된 영수증(검증 함수가 확인한 뒤) — 그 기간만큼 되돌린다
create or replace function revoke_purchase(p_token text) returns void language plpgsql security definer set search_path = public as $$
declare p purchases;
begin
  select * into p from purchases where purchase_token = p_token for update; if not found or p.revoked_at is not null then return; end if;
  update profiles set pass_until = greatest(kst_today() - 1, pass_until - p.days) where id = p.uid;
  update purchases set revoked_at = now() where purchase_token = p_token;   -- 지우지 않는다: 같은 영수증으로 다시 받기 막기 · 전자상거래법 5년 보관
end $$;

-- ═══ 이야기: 글쓴이·닉네임은 서버가 채운다 · 도배 제한 · 댓글 수 ═══
-- 도움이 필요해 보이는 글(자해·자살 신호) — 가리지 않고, 쓴 사람에게는 상담 안내를, 원장에게는 '먼저 살펴볼 글'로 알린다.
-- 앱(CARE_RE)과 같은 목록 — 둘이 어긋나지 않는지 tools/testbed_security.py 가 같은 문장 묶음을 양쪽에 넣어 본다. '세포 자살'(생물 용어)·'유서 깊은'은 빼고 본다.
-- 2026-10 보강: 청소년 은어 '뒤지고 싶'·'죽어야겠'·'태어나지 말았'·'살 의미가 없'(docs/11 §12-4 · '배고파 죽겠다'·'서랍을 뒤져' 같은 말은 걸리지 않는지 시험)
create or replace function private.care_hit(t text) returns boolean language sql immutable as $$
  select coalesce(regexp_replace(t, '세포\s*(의|가|는|들의|들이)?\s*자살|자살\s*예방|자살률|유서\s*깊', '', 'g')
    ~ '(죽고\s*싶|죽어\s*버리고\s*싶|자살|자해|손목을?\s*긋|목숨을?\s*끊|뛰어\s*내리고\s*싶|살기\s*싫|살고\s*싶지\s*않|사라지고\s*싶|없어지고\s*싶|극단적\s*선택|유서를|유서\s*(를\s*)?(써|쓰)|그만\s*살고\s*싶|살\s*이유가\s*없|다\s*끝내고\s*싶|뒤지고\s*싶|죽어야\s*겠|태어나지\s*말았|살\s*의미가\s*없)', false) $$;
alter table posts    add column if not exists care boolean not null default false;
alter table posts add column if not exists deleted_at timestamptz;
alter table comments add column if not exists deleted_at timestamptz;
alter table comments add column if not exists care boolean not null default false;
-- 개인정보 — 앱(PII_SRC)과 같은 규칙(같은 글자). 앱을 거치지 않고 들어온 글도 서버가 본다(docs/11 §12-3).
--  주민등록번호 → 거절 · 휴대전화 → 가운데를 가려(010-****-5678) 저장 · 이메일·SNS 아이디·○동 ○호·'○○중 2학년 김○○' → 앱이 올리기 전에 한 번 더 묻는다(닉네임은 모두 거절)
create or replace function private.pii_hard(t text) returns boolean language sql immutable as $$
  select coalesce(t ~ '(?<![0-9])[0-9]{6}\s*[-–]\s*[1-4][0-9]{6}(?![0-9])', false) $$;
create or replace function private.pii_mask(t text) returns text language sql immutable as $$
  select regexp_replace(t, '(?<![0-9])(01[016-9])[-. ]?([0-9]{3,4})[-. ]?([0-9]{4})(?![0-9])', '\1-****-\3', 'g') $$;
create or replace function private.pii_kinds(t text) returns text[] language sql immutable as $$
  select array_remove(array[
    case when t ~ '(?<![0-9])[0-9]{6}\s*[-–]\s*[1-4][0-9]{6}(?![0-9])' then 'rrn' end,
    case when t ~ '(?<![0-9])(01[016-9])[-. ]?([0-9]{3,4})[-. ]?([0-9]{4})(?![0-9])' then 'phone' end,
    case when t ~ '[A-Za-z0-9_.+-]+@[A-Za-z0-9_-]+\.[A-Za-z0-9_.]{2,}' then 'email' end,
    case when t ~ '(카톡|카카오톡|오픈챗|오픈카톡|인스타|텔레그램)\s*(아이디|[Ii][Dd])?\s*[:：]?\s*@?[A-Za-z0-9_.-]{3,}' then 'sns' end,
    case when t ~ '(?<![0-9])[0-9]{1,3}\s*동\s*[0-9]{1,4}\s*호' then 'addr' end,
    case when t ~ '[가-힣]{1,10}(초등학교|중학교|고등학교|초|중|고)\s*[1-6]\s*학년(\s*[0-9]{1,2}\s*반)?\s*[김이박최정강조윤장임한오서신권황안송류유전홍고문양손배백허남심노하곽성차주우구민진나지엄채원천방공현함변염여추도소석선설마길연위표명기반라왕금옥육인맹제모탁국어은편용예경봉사부가복태목형피두감음빈동온호범좌팽승간상시갈][가-힣]{1,2}' then 'school' end], null) $$;
create or replace function private.pii_guard() returns trigger language plpgsql security definer set search_path = public, private as $$
declare t text;
begin
  if tg_table_name = 'posts' then t := coalesce(new.title, '') || ' ' || coalesce(new.body, ''); else t := coalesce(new.body, ''); end if;   -- 댓글에는 제목 칸이 없다
  if private.pii_hard(t) then
    raise exception '주민등록번호로 보이는 내용은 올릴 수 없습니다. 지우고 다시 올려 주세요.' using errcode = '22023'; end if;
  if not is_owner() then   -- 학원 연락처를 적는 원장 글은 그대로
    if tg_table_name = 'posts' then new.title := private.pii_mask(new.title); end if;
    new.body := private.pii_mask(new.body); end if;
  return new;
end $$;

-- ═══ 이야기에 쓸 수 있는가 — 원장 · 또는 (보호자 동의 끝 · 이용 제한 중 아님 · 학생 계정 · 학원 코드(수강 중)나 이용권 기간 안) ═══
--  보호자 계정과 손님(코드도 이용권도 없는 학생 계정)은 읽기만 — 가입할 때 '보호자'만 고르면 어른이 학생 공간에 바로 쓰던 것(docs/11 §11)
create or replace function private.talk_block(u uuid) returns text language sql stable security definer set search_path = public as $$
  select case when u is null or p.id is null then 'login'
              when p.role = 'owner' and is_owner() then null
              when p.under14 and not p.guardian_ok then 'consent'
              when p.talk_until >= kst_today() then 'limit'
              when p.role <> 'student' then 'parent'
              when p.pass_until >= kst_today() or exists (select 1 from students s where s.code = p.student_code and s.until >= kst_today()) then null
              else 'member' end
    from (select 1) o left join profiles p on p.id = u $$;
create or replace function private.talk_msg(b text, u uuid) returns text language sql stable security definer set search_path = public as $$
  select case b
    when 'limit' then (select case when talk_until = 'infinity' then '이야기 쓰기가 멈춰 있습니다. 읽기는 그대로 할 수 있어요.'
                                   else '이야기 쓰기가 ' || to_char(talk_until, 'FMMM"월" FMDD"일"') || '까지 쉬는 중입니다. 읽기는 그대로 할 수 있어요.' end from profiles where id = u)
    when 'parent'  then '보호자 계정은 이야기를 읽기만 할 수 있습니다.'
    when 'member'  then '이야기 글쓰기는 학원 코드나 이용권을 등록한 계정에서 할 수 있습니다.'
    when 'consent' then '보호자 동의가 끝난 뒤에 쓸 수 있습니다.'
    else '로그인이 필요합니다.' end $$;
create or replace function talk_ok() returns boolean language sql stable security definer set search_path = public, private as $$
  select private.talk_block(auth.uid()) is null $$;
-- 내 이야기 상태(앱이 글쓰기 단추 대신 차분한 안내를 그릴 때) — 제한이면 언제까지·사유, 이의 제기 기한(제한 뒤 7일, 약관 제8조의3 ④)
create or replace function my_talk() returns json language sql stable security definer set search_path = public, private as $$
  select json_build_object('ok', b is null, 'block', b, 'msg', case when b is null then null else private.talk_msg(b, auth.uid()) end,
           'until', case when b = 'limit' then (select case when talk_until = 'infinity' then 'stop' else talk_until::text end from profiles where id = auth.uid()) end,
           'reason', case when b = 'limit' then (select nullif(talk_reason, '') from profiles where id = auth.uid()) end,
           'appeal_until', case when b = 'limit' then (select (at at time zone 'Asia/Seoul')::date + 7 from talk_log where uid = auth.uid() and action <> 'lift' order by at desc limit 1) end,
           'guardian', case when b = 'limit' then coalesce((select guardian from talk_log where uid = auth.uid() and action <> 'lift' order by at desc limit 1), false) end)   -- 보호자 요청이면 이의 제기 대신 '보호자와 이야기'
    from (select private.talk_block(auth.uid()) as b) z $$;
-- 제한 중·읽기 전용 계정은 지금 글을 고치지도 못한다(지우기는 된다)
create or replace function private.talk_edit_guard() returns trigger language plpgsql security definer set search_path = public, private as $$
declare b text;
begin
  if auth.uid() is null or is_owner() then return new; end if;
  if new.title is distinct from old.title or new.body is distinct from old.body or new.attach is distinct from old.attach or new.board is distinct from old.board then
    b := private.talk_block(auth.uid());
    if b is not null then raise exception '%', private.talk_msg(b, auth.uid()) using errcode = '42501'; end if; end if;
  return new;
end $$;
drop trigger if exists posts_talk_guard on posts; create trigger posts_talk_guard before update on posts for each row execute function private.talk_edit_guard();
create or replace function private.stamp_author() returns trigger language plpgsql security definer set search_path = public, private as $$
declare n int; b text;
begin
  if not is_owner() then new.author := auth.uid(); end if;
  if new.author is null then raise exception '로그인이 필요합니다' using errcode = '42501'; end if;
  if not is_owner() then b := private.talk_block(new.author);   -- 이용 제한 · 보호자 · 손님은 쓰지 못한다(정책 write_posts·write_comments 도 같은 조건)
    if b is not null then raise exception '%', private.talk_msg(b, new.author) using errcode = '42501'; end if; end if;
  new.staff := is_owner();
  select coalesce(nullif(nick, ''), case when new.staff then '원장님' else '익명' end) into new.nick from profiles where id = new.author;
  new.nick := coalesce(new.nick, '익명');
  new.likes := '{}'; new.report_n := 0; new.deleted := false; new.at := now();
  if tg_table_name = 'posts' then
    new.care := private.care_hit(coalesce(new.title, '') || ' ' || coalesce(new.body, ''));
    new.comment_n := 0; new.solved := false;
    select count(*) into n from posts where author = new.author and at > now() - interval '10 minutes';
    if n >= 5 and not is_owner() then raise exception '글은 10분에 5개까지 올릴 수 있습니다. 잠시 뒤에 올려 주세요.' using errcode = 'P0001'; end if;
  else
    new.picked := false; new.care := private.care_hit(new.body);
    select count(*) into n from comments where author = new.author and at > now() - interval '10 minutes';
    if n >= 20 and not is_owner() then raise exception '댓글은 10분에 20개까지 달 수 있습니다. 잠시 뒤에 달아 주세요.' using errcode = 'P0001'; end if;
  end if;
  return new;
end $$;
drop trigger if exists posts_stamp on posts;       create trigger posts_stamp    before insert on posts    for each row execute function private.stamp_author();
drop trigger if exists comments_stamp on comments; create trigger comments_stamp before insert on comments for each row execute function private.stamp_author();
-- 개인정보 검사는 글쓴이 확인(stamp) 뒤에 — 트리거 이름 순서로 돈다
drop trigger if exists posts_x_pii on posts;       create trigger posts_x_pii    before insert or update of title, body on posts for each row execute function private.pii_guard();
drop trigger if exists comments_x_pii on comments; create trigger comments_x_pii before insert on comments for each row execute function private.pii_guard();
create or replace function private.recare() returns trigger language plpgsql security definer set search_path = public as $$
begin new.care := private.care_hit(coalesce(new.title, '') || ' ' || coalesce(new.body, '')); return new; end $$;
drop trigger if exists posts_recare on posts; create trigger posts_recare before update of title, body on posts for each row execute function private.recare();
-- 이 칸이 생기기 전에 올라온 글·댓글도 한 번 판정(여러 번 돌려도 같다)
update posts    set care = private.care_hit(coalesce(title, '') || ' ' || coalesce(body, '')) where care is distinct from private.care_hit(coalesce(title, '') || ' ' || coalesce(body, ''));
update comments set care = private.care_hit(body) where care is distinct from private.care_hit(body);
-- 원장: '먼저 살펴볼 글·댓글' — 최근 30일 힘든 마음의 말(care) + '친구가 걱정돼요' 신고가 남은 것(worry). 누가 썼는지(이름·학원 코드)까지. 원장만 부를 수 있다
create or replace function care_list() returns json language plpgsql stable security definer set search_path = public as $$
begin
  if not is_owner() then return '[]'::json; end if;
  return coalesce((select json_agg(x order by x.worry > 0 desc, x.at desc) from (
    select 'post' as kind, p.id, p.id as post_id, p.title, left(p.body, 140) as body, p.nick, p.at, pr.name, pr.student_code as code, pr.role, p.author as uid, p.care,
           (select count(*) from reports r where r.post_id = p.id and r.reason = 'worry' and r.state = 'open') as worry
      from posts p join profiles pr on pr.id = p.author
     where not p.staff and not p.deleted and ((p.care and p.at > now() - interval '30 days') or exists (select 1 from reports r where r.post_id = p.id and r.reason = 'worry' and r.state = 'open'))
    union all
    select 'comment', c.id, c.post_id, null, left(c.body, 140), c.nick, c.at, pr.name, pr.student_code, pr.role, c.author, c.care,
           (select count(*) from reports r where r.comment_id = c.id and r.reason = 'worry' and r.state = 'open')
      from comments c join profiles pr on pr.id = c.author
     where not c.staff and not c.deleted and ((c.care and c.at > now() - interval '30 days') or exists (select 1 from reports r where r.comment_id = c.id and r.reason = 'worry' and r.state = 'open'))) x), '[]'::json);
end $$;
-- 원장: 받은 의견(보낸 사람 이름·학원 코드와 함께) · 처리 표시
create or replace function feedback_list() returns json language plpgsql stable security definer set search_path = public as $$
begin
  if not is_owner() then return '[]'::json; end if;
  return coalesce((select json_agg(x order by x.done_at is not null, x.at desc) from (
    select f.id, f.kind, f.body, f.ref, f.ver, f.care, f.at, f.done_at, pr.name, pr.student_code as code, pr.role
      from feedback f join profiles pr on pr.id = f.uid
     where f.done_at is null or f.done_at > now() - interval '30 days' limit 200) x), '[]'::json);
end $$;
create or replace function feedback_done(p_id bigint, p_done boolean default true) returns void language plpgsql security definer set search_path = public as $$
begin
  if not is_owner() then raise exception 'owner only' using errcode = '42501'; end if;
  update feedback set done_at = case when p_done then now() else null end where id = p_id;
end $$;
create or replace function private.count_comments() returns trigger language plpgsql security definer set search_path = public as $$
begin
  update posts set comment_n = (select count(*) from comments where post_id = coalesce(new.post_id, old.post_id) and not deleted)
   where id = coalesce(new.post_id, old.post_id);
  return null;
end $$;
drop trigger if exists comments_count on comments;
create trigger comments_count after insert or update of deleted or delete on comments for each row execute function private.count_comments();

create or replace function like_toggle(p_kind text, p_id uuid) returns void language plpgsql security definer set search_path = public, private as $$
declare u uuid := auth.uid();
begin
  if u is null then raise exception '로그인이 필요합니다' using errcode = '42501'; end if;
  if not talk_ok() then raise exception '%', private.talk_msg(private.talk_block(u), u) using errcode = '42501'; end if;   -- 도움됨도 '쓰기' — 보호자·손님·제한 중에는 읽기만
  if p_kind = 'post' then update posts set likes = case when u = any(likes) then array_remove(likes, u) else likes || u end where id = p_id and not deleted and report_n < 3;
  else update comments set likes = case when u = any(likes) then array_remove(likes, u) else likes || u end where id = p_id and not deleted and report_n < 3; end if;
end $$;
-- 신고 — 사유를 고른다. 가림(3건)은 '열린' 신고 중 걱정돼요를 뺀 것만 센다(private.recount)
drop function if exists report_item(text, uuid);
create or replace function report_item(p_kind text, p_id uuid, p_reason text default 'other') returns json language plpgsql security definer set search_path = public, private as $$
declare u uuid := auth.uid(); r text := coalesce(nullif(trim(p_reason), ''), 'other'); w boolean; au uuid; stf boolean; pv reports; n int; pid uuid; cid uuid;
begin
  if u is null then raise exception '로그인이 필요합니다' using errcode = '42501'; end if;
  if r not in ('privacy','bully','harm','ad','copy','other','worry') then raise exception '신고 사유를 골라 주세요.' using errcode = '22023'; end if;
  w := r = 'worry';
  -- 신고 3건이면 글이 가려지므로, 계정을 여러 개 만들어 남의 글을 지우는 일을 막는다: 보호자 동의 · 가입 하루 뒤 · 하루 20건 · 선생님 글 제외
  --  '친구가 걱정돼요'는 글을 가리지 않으므로 가입 첫날에도 된다(원장에게 알리는 길을 막지 않는다)
  if not consent_ok() then raise exception '보호자 동의가 끝난 뒤에 신고할 수 있습니다. 급한 일은 원장님께 알려 주세요.' using errcode = '42501'; end if;
  if not w and (select created_at from profiles where id = u) > now() - interval '1 day' then
    raise exception '가입하고 하루가 지나면 신고할 수 있습니다. 급한 일은 내 정보 › 의견 보내기로 원장님께 알려 주세요.' using errcode = 'P0001'; end if;
  if (select count(*) from private.attempts where uid = u and kind = 'report' and at > now() - interval '1 day') >= 20 then
    raise exception '오늘은 신고를 너무 많이 했습니다. 원장님께 직접 알려 주세요.' using errcode = '54000'; end if;
  if p_kind = 'post' then select author, staff into au, stf from posts where id = p_id and not deleted; pid := p_id;
  elsif p_kind = 'comment' then select author, staff into au, stf from comments where id = p_id and not deleted; cid := p_id;
  else raise exception '잘못된 요청입니다.' using errcode = '22023'; end if;
  if au is null then return json_build_object('ok', false, 'why', '지워졌거나 없는 글입니다.'); end if;
  if stf then return json_build_object('ok', false, 'why', '선생님 글은 신고 대신 원장님께 직접 말해 주세요.'); end if;
  if au = u then return json_build_object('ok', false, 'why', '내 글은 신고할 수 없습니다. 지우려면 지우기를 눌러 주세요.'); end if;
  -- 같은 사람은 한 글에 한 번(걱정돼요는 따로 한 번). 원장이 이미 살펴본(되돌린) 신고는 다시 눌러도 다시 세지 않는다
  select * into pv from reports where uid = u and (reason = 'worry') = w and (post_id = pid or comment_id = cid);
  if found then return json_build_object('ok', true, 'again', true, 'checked', pv.state <> 'open', 'n', private.recount(pid, cid), 'worry', w); end if;
  insert into private.attempts(uid, kind, ok) values (u, 'report', true);
  insert into reports(post_id, comment_id, uid, reason) values (pid, cid, u, r);
  n := private.recount(pid, cid);
  return json_build_object('ok', true, 'n', n, 'hidden', n >= 3, 'worry', w);
end $$;
-- 신고 수(가림 기준) = 열린 신고 중 걱정돼요를 뺀 수
create or replace function private.recount(p_post uuid, p_comment uuid) returns int language plpgsql security definer set search_path = public as $$
declare n int;
begin
  if p_post is not null then
    select count(*) into n from reports where post_id = p_post and state = 'open' and reason <> 'worry';
    update posts set report_n = n where id = p_post and report_n is distinct from n;
  else
    select count(*) into n from reports where comment_id = p_comment and state = 'open' and reason <> 'worry';
    update comments set report_n = n where id = p_comment and report_n is distinct from n;
  end if;
  return coalesce(n, 0);
end $$;
create or replace function private.reports_after() returns trigger language plpgsql security definer set search_path = public, private as $$
begin
  if tg_op = 'DELETE' then perform private.recount(old.post_id, old.comment_id); else perform private.recount(new.post_id, new.comment_id); end if;
  return null;
end $$;
drop trigger if exists reports_count on reports;   -- 신고한 계정이 지워지면(연쇄 삭제) 그 신고도 빠지고 수가 다시 맞춰진다
create trigger reports_count after insert or update of state or delete on reports for each row execute function private.reports_after();
-- 글·댓글이 지워지면 열린 신고는 '지움'으로 끝낸다(신고한 사람에게 결과가 간다)
create or replace function private.reports_on_delete() returns trigger language plpgsql security definer set search_path = public as $$
begin
  if new.deleted and not coalesce(old.deleted, false) then
    if tg_table_name = 'posts' then update reports set state = 'removed', resolved_at = now() where post_id = new.id and state = 'open';
    else update reports set state = 'removed', resolved_at = now() where comment_id = new.id and state = 'open'; end if;
  end if;
  return null;
end $$;
drop trigger if exists posts_reports_done on posts;       create trigger posts_reports_done    after update of deleted on posts    for each row execute function private.reports_on_delete();
drop trigger if exists comments_reports_done on comments; create trigger comments_reports_done after update of deleted on comments for each row execute function private.reports_on_delete();
-- 원장: 잘못된 신고 되돌리기(가려진 글·댓글을 다시 보이게) — 그 신고들은 '그대로 둠'으로 끝나고, 같은 학생이 다시 눌러도 다시 가려지지 않는다
create or replace function clear_reports(p_kind text, p_id uuid) returns void language plpgsql security definer set search_path = public, private as $$
begin
  if not is_owner() then raise exception 'owner only' using errcode = '42501'; end if;
  if p_kind = 'post' then update reports set state = 'kept', resolved_at = now() where post_id = p_id and state = 'open' and reason <> 'worry';
  else update reports set state = 'kept', resolved_at = now() where comment_id = p_id and state = 'open' and reason <> 'worry'; end if;
end $$;
-- 원장: '친구가 걱정돼요'를 살펴봤다(먼저 살펴볼 목록에서 내려감 · 신고한 학생에게 '원장님이 살펴봤어요')
create or replace function care_done(p_kind text, p_id uuid) returns void language plpgsql security definer set search_path = public as $$
begin
  if not is_owner() then raise exception 'owner only' using errcode = '42501'; end if;
  if p_kind = 'post' then update reports set state = 'kept', resolved_at = now() where post_id = p_id and state = 'open' and reason = 'worry';
  else update reports set state = 'kept', resolved_at = now() where comment_id = p_id and state = 'open' and reason = 'worry'; end if;
end $$;
-- 원장: 신고된 글·댓글(열린 신고) — 사유별 건수와 함께
create or replace function reported_list() returns json language plpgsql stable security definer set search_path = public as $$
begin
  if not is_owner() then return '[]'::json; end if;
  return coalesce((select json_agg(x order by x.report_n desc, x.at desc) from (
    select 'post' as kind, p.id, p.id as post_id, p.title, left(p.body, 140) as body, p.nick, p.author as uid, p.at, p.report_n,
           (select json_object_agg(reason, n) from (select reason, count(*) as n from reports r where r.post_id = p.id and r.state = 'open' and r.reason <> 'worry' group by reason) z) as reasons,
           (select count(*) from reports r where r.post_id = p.id and r.state = 'kept' and r.reason <> 'worry') as kept
      from posts p where not p.deleted and exists (select 1 from reports r where r.post_id = p.id and r.state = 'open' and r.reason <> 'worry')
    union all
    select 'comment', c.id, c.post_id, null, left(c.body, 140), c.nick, c.author, c.at, c.report_n,
           (select json_object_agg(reason, n) from (select reason, count(*) as n from reports r where r.comment_id = c.id and r.state = 'open' and r.reason <> 'worry' group by reason) z),
           (select count(*) from reports r where r.comment_id = c.id and r.state = 'kept' and r.reason <> 'worry')
      from comments c where not c.deleted and exists (select 1 from reports r where r.comment_id = c.id and r.state = 'open' and r.reason <> 'worry')) x), '[]'::json);
end $$;
-- 신고한 사람: 원장이 처리한 내 신고(아직 안 본 것) · 봤다고 표시. 글 내용은 주지 않는다
create or replace function my_reports() returns json language sql stable security definer set search_path = public as $$
  select coalesce(json_agg(json_build_object('id', r.id, 'kind', case when r.post_id is null then 'comment' else 'post' end, 'reason', r.reason, 'state', r.state, 'at', r.at, 'resolved_at', r.resolved_at) order by r.resolved_at desc), '[]'::json)
    from reports r where r.uid = auth.uid() and r.state <> 'open' and r.seen_at is null and r.resolved_at > now() - interval '30 days' $$;
create or replace function my_reports_seen() returns void language sql security definer set search_path = public as $$
  update reports set seen_at = now() where uid = auth.uid() and state <> 'open' and seen_at is null $$;

-- ═══ 이야기 이용 제한(원장) — 7일 · 30일 · 중지 · 풀기. 보호자 요청도 같은 길(약관 제8조의3 ②) ═══
--  p_days: 7 · 30 · -1(중지) · 0(풀기). p_uid 대신 학생 코드(p_code)로도 — 글을 쓴 적 없는 학생도 보호자 요청으로 막을 수 있게
create or replace function talk_limit(p_uid uuid, p_days int, p_reason text default '', p_memo text default '', p_guardian boolean default false, p_code text default null) returns json
language plpgsql security definer set search_path = public as $$
declare u uuid := p_uid; t date; a text;
begin
  if not is_owner() then raise exception 'owner only' using errcode = '42501'; end if;
  if u is null and coalesce(p_code, '') <> '' then select id into u from profiles where student_code = upper(trim(p_code)) and role = 'student'; end if;
  if u is null or not exists (select 1 from profiles where id = u) then return json_build_object('ok', false, 'why', '학생 계정을 찾을 수 없습니다. 학생이 앱에 학원 코드를 등록했는지 확인해 주세요.'); end if;
  if exists (select 1 from profiles where id = u and role = 'owner') then return json_build_object('ok', false, 'why', '원장 계정은 제한할 수 없습니다.'); end if;
  if p_days is null or p_days not in (0, 7, 30, -1) then return json_build_object('ok', false, 'why', '7일 · 30일 · 중지 · 풀기 중에서 골라 주세요.'); end if;
  t := case p_days when 0 then null when -1 then 'infinity'::date else kst_today() + p_days end;
  a := case p_days when 0 then 'lift' when -1 then 'stop' when 7 then 'd7' else 'd30' end;
  update profiles set talk_until = t, talk_reason = case when p_days = 0 then '' else left(trim(coalesce(p_reason, '')), 40) end where id = u;
  insert into talk_log(uid, action, reason, memo, guardian, until) values (u, a, left(trim(coalesce(p_reason, '')), 40), left(trim(coalesce(p_memo, '')), 300), coalesce(p_guardian, false), t);
  return json_build_object('ok', true, 'until', t);
end $$;
-- 원장: 지금 제한 중인 학생 + 최근 처리 기록 30건(누가 · 언제 · 무엇을 · 메모)
create or replace function talk_limits() returns json language plpgsql stable security definer set search_path = public as $$
begin
  if not is_owner() then return json_build_object('active', '[]'::json, 'log', '[]'::json); end if;
  return json_build_object(
    'active', coalesce((select json_agg(x order by x.until) from (
        select p.id as uid, p.name, p.student_code as code, p.nick, p.role, p.talk_until as until, p.talk_reason as reason, l.memo, l.guardian, l.at as since
          from profiles p left join lateral (select memo, guardian, at from talk_log where uid = p.id order by at desc limit 1) l on true
         where p.talk_until >= kst_today()) x), '[]'::json),
    'log', coalesce((select json_agg(x order by x.at desc) from (
        select l.uid, l.at, l.action, l.reason, l.memo, l.guardian, l.until, p.name, p.nick, p.student_code as code
          from talk_log l join profiles p on p.id = l.uid order by l.at desc limit 30) x), '[]'::json));
end $$;
create or replace function pick_comment(p_post uuid, p_comment uuid) returns void language plpgsql security definer set search_path = public as $$
begin
  if not exists (select 1 from posts where id = p_post and author = auth.uid() and not deleted) then raise exception '글쓴이만 채택할 수 있습니다' using errcode = '42501'; end if;
  if not exists (select 1 from comments where id = p_comment and post_id = p_post and not deleted) then raise exception '이 글의 댓글이 아닙니다'; end if;
  update comments set picked = (id = p_comment) where post_id = p_post;
  update posts set solved = true where id = p_post;
end $$;

-- ═══ 푸시 알림 기기 등록 · 계정 삭제 ═══
create or replace function register_push(p_token text, p_platform text) returns void language plpgsql security definer set search_path = public as $$
begin
  if auth.uid() is null or coalesce(p_token, '') = '' then return; end if;
  delete from push_tokens where token = p_token;
  insert into push_tokens(token, uid, platform) values (left(p_token, 400), auth.uid(), left(coalesce(p_platform, 'android'), 20));
  delete from push_tokens where uid = auth.uid() and token not in (select token from push_tokens where uid = auth.uid() order by at desc limit 5);   -- 한 사람 기기 5대까지
end $$;
create or replace function delete_my_account() returns void language plpgsql security definer set search_path = public, private as $$
declare u uuid := auth.uid();
begin
  if u is null then raise exception 'login required' using errcode = '42501'; end if;
  -- 남의 글에 남은 내 흔적도 지운다 — 도움됨은 여기서, 신고는 계정과 함께 연쇄 삭제되고 신고 수가 다시 맞춰진다(탈퇴한 계정의 신고로 글이 계속 가려지지 않게)
  update posts set likes = array_remove(likes, u) where u = any(likes);
  update comments set likes = array_remove(likes, u) where u = any(likes);
  delete from client_errors where uid = u; delete from private.attempts where uid = u; delete from private.consent_links where uid = u;
  delete from progress where code = 'u:' || u::text;
  delete from progress where code = (select student_code from profiles where id = u);
  delete from auth.users where id = u;      -- 프로필·글·댓글·푸시 기기는 연쇄 삭제, 결제 기록은 계정 연결만 끊고 5년 보관
end $$;
-- 푸시 받을 기기 목록(서비스 키 전용 · push 함수가 부른다): 공지/일정 → 그 반 학생·보호자, 출석 → 그 학생의 보호자
create or replace function push_targets(p_kind text, p_cls text, p_code text) returns table(token text, uid uuid, who text)
language sql stable security definer set search_path = public as $$
  with codes as (
    select code from students where p_kind in ('notice','sched') and (p_cls = '전체' or cls = p_cls) and until >= kst_today()
    union select p_code where p_kind = 'attend'
  )
  select t.token, t.uid, case when pr.role = 'parent' then 'parent' when pr.role = 'owner' then 'owner' else 'student' end
    from push_tokens t join profiles pr on pr.id = t.uid
   where (p_kind = 'care' and pr.role = 'owner')
      or (p_kind not in ('attend', 'care') and pr.student_code in (select code from codes))
      or exists (select 1 from guardian_links g where g.uid = t.uid and g.approved and g.code in (select code from codes))
$$;

-- ═══ 만 14세 미만 — 법정대리인 동의 확인(개인정보 보호법 제22조의2) ═══
-- 방법 ① 동의 페이지: 아이가 보호자 폰으로 링크를 보내고 → 보호자가 페이지에서 동의 표시 → 학원이 '확인했다'는 문자를 보호자에게 보냄
-- 방법 ② 서면: 학원에서 동의서에 서명을 받고 원장이 앱에 '서면 동의 받음'을 누름
-- 동의 전에는 이야기(글·댓글·읽기)와 진도의 서버 저장을 막고, 7일 안에 동의가 없으면 계정을 지운다(purge_old).
-- 인자 없이 '나'만 — 남의 id 로 부르면 동의 전 14세 미만 계정을 가려낼 수 있었다(2026-10-01 점검). 정책을 새로 거는 아래에서 다시 만든다
drop function if exists consent_ok(uuid) cascade;
create or replace function consent_ok() returns boolean language sql stable security definer set search_path = public as $$
  select coalesce((select not under14 or guardian_ok from profiles where id = auth.uid()), true) $$;
revoke execute on function consent_ok() from public, anon; grant execute on function consent_ok() to authenticated;
-- p_phone: 학원이 '번호가 달라요'로 되돌린 뒤 아이가 보호자 번호를 고쳐 다시 보낼 때만(동의 확인 전까지)
drop function if exists consent_request();
create or replace function consent_request(p_phone text default null) returns json language plpgsql security definer set search_path = public, private as $$
declare pr profiles; t text; d text := regexp_replace(coalesce(p_phone, ''), '[^0-9]', '', 'g');
begin
  select * into pr from profiles where id = auth.uid();
  if not found or not pr.under14 then return json_build_object('ok', false, 'why', '보호자 동의가 필요한 계정이 아닙니다.'); end if;
  if pr.guardian_ok then return json_build_object('ok', true, 'done', true); end if;
  if pr.guardian_how = 'web' and pr.guardian_at is not null then return json_build_object('ok', true, 'given', true); end if;
  if p_phone is not null then
    if d !~ '^01[0-9]{8,9}$' then return json_build_object('ok', false, 'why', '보호자 휴대전화 번호를 확인해 주세요.'); end if;
    update profiles set guardian = left(split_part(guardian, ' ', 1) || ' ' || d, 60) where id = pr.id returning * into pr; end if;
  if (select count(*) from private.consent_links where uid = pr.id and at > now() - interval '1 day') >= 5 then
    return json_build_object('ok', false, 'why', '오늘은 요청을 너무 많이 보냈습니다. 내일 다시 시도해 주세요.'); end if;
  t := encode(gen_random_bytes(18), 'hex');
  insert into private.consent_links(token, uid) values (t, pr.id);
  return json_build_object('ok', true, 'token', t, 'guardian', pr.guardian);
end $$;
-- 동의 페이지가 보여 줄 것(로그인 없이) — 아이 이름은 첫 글자만
create or replace function consent_info(p_token text) returns json language plpgsql stable security definer set search_path = public, private as $$
declare l private.consent_links; pr profiles;
begin
  select * into l from private.consent_links where token = p_token and at > now() - interval '7 days';
  if not found then return json_build_object('ok', false, 'why', '만료된 링크입니다. 자녀에게 새 링크를 보내 달라고 해 주세요.'); end if;
  select * into pr from profiles where id = l.uid;
  if not found then return json_build_object('ok', false, 'why', '계정을 찾을 수 없습니다.'); end if;
  if l.used_at is not null and not pr.guardian_ok and not (pr.guardian_how = 'web' and pr.guardian_at is not null) then return json_build_object('ok', false, 'why', '이미 사용한 링크입니다. 자녀에게 새 링크를 보내 달라고 해 주세요.'); end if;
  return json_build_object('ok', true, 'child', left(pr.name, 1) || repeat('○', greatest(char_length(pr.name) - 1, 1)), 'done', pr.guardian_ok or (pr.guardian_how = 'web' and pr.guardian_at is not null),
                           'expires', to_char((l.at + interval '7 days') at time zone 'Asia/Seoul', 'FMMM"월" FMDD"일"'));
end $$;
create or replace function consent_give(p_token text, p_name text) returns json language plpgsql security definer set search_path = public, private as $$
declare l private.consent_links;
begin
  if char_length(trim(coalesce(p_name, ''))) < 2 then return json_build_object('ok', false, 'why', '보호자 성함을 적어 주세요.'); end if;
  select * into l from private.consent_links where token = p_token and used_at is null and at > now() - interval '7 days' for update;
  if not found then return json_build_object('ok', false, 'why', '만료되었거나 이미 사용한 링크입니다.'); end if;
  update private.consent_links set used_at = now() where token = p_token;
  -- 동의 '표시'만 기록한다. 학원이 보호자 휴대전화로 확인 문자를 보낸 때(consent_mark 'notified') 동의가 끝난다
  --  (개인정보 보호법 시행령의 '인터넷 동의 표시 + 확인 문자' 방법 — 아이가 링크를 스스로 눌러도, 확인 문자를 받은 보호자가 알게 된다)
  update profiles set guardian_how = 'web', guardian_at = now(),
         guardian = left(trim(p_name) || ' ' || coalesce(nullif(substring(guardian from '[0-9][0-9 -]{7,}'), ''), ''), 60)
   where id = l.uid;
  return json_build_object('ok', true);
end $$;
-- 원장: 동의가 필요한 계정 목록 · 서면 동의 표시 · 확인 문자 보냄 표시
create or replace function consent_list() returns table(id uuid, name text, guardian text, guardian_ok boolean, guardian_how text, guardian_at timestamptz, notified_at timestamptz, created_at timestamptz)
language sql stable security definer set search_path = public as $$
  select p.id, p.name, p.guardian, p.guardian_ok, p.guardian_how, p.guardian_at, p.guardian_notified_at, p.created_at from profiles p
   where p.under14 and is_owner() order by p.guardian_ok, p.created_at desc $$;
create or replace function consent_mark(p_uid uuid, p_what text) returns void language plpgsql security definer set search_path = public as $$
begin
  if not is_owner() then raise exception 'owner only' using errcode = '42501'; end if;
  if p_what = 'paper' then update profiles set guardian_ok = true, guardian_how = 'paper', guardian_at = now() where id = p_uid and under14;
  elsif p_what = 'notified' then update profiles set guardian_notified_at = now(), guardian_ok = true where id = p_uid and under14 and (guardian_ok or (guardian_how = 'web' and guardian_at is not null));
  elsif p_what = 'reset' then   -- 번호가 등록 서류와 다름 → 웹 동의 표시를 지우고 다시 요청받게(이때부터 7일)
    update profiles set guardian_how = 'reset', guardian_at = now() where id = p_uid and under14 and not guardian_ok and guardian_how = 'web';
  end if;
end $$;

-- ═══ 앱 운영 스위치(로그인 없이 읽음) — 새 APK 없이 '업데이트 필요'·'점검 중'을 알린다 ═══
-- 값은 private.config 에 넣는다: min_version(이보다 낮으면 업데이트해야 씀) · latest_version(권장) · notice(점검·안내 한 줄)
--   insert into private.config values ('min_version', '1.0.0') on conflict (k) do update set v = excluded.v;
create or replace function app_meta() returns json language sql stable security definer set search_path = private as $$
  select json_build_object(
    'min_version',    (select v from private.config where k = 'min_version'),
    'latest_version', (select v from private.config where k = 'latest_version'),
    'notice',         (select v from private.config where k = 'notice')) $$;

-- ═══ 권한 — Supabase 는 public 표에 전부 열어 두므로, 여기서 칸 단위로 다시 좁힌다 ═══
revoke all on all functions in schema private from public, anon, authenticated;
revoke execute on function consent_list(), consent_mark(uuid, text), consent_request(text) from public, anon;
grant execute on function consent_list(), consent_mark(uuid, text), consent_request(text) to authenticated;
grant execute on function consent_info(text), consent_give(text, text) to anon, authenticated;
grant execute on function app_meta() to anon, authenticated;
revoke execute on function care_list() from public, anon; grant execute on function care_list() to authenticated;   -- 안에서 원장만 결과를 받는다
revoke execute on function grant_purchase(uuid, text, text, text, int, jsonb), revoke_purchase(text), push_targets(text, text, text) from public, anon, authenticated;
grant execute on function grant_purchase(uuid, text, text, text, int, jsonb), revoke_purchase(text), push_targets(text, text, text) to service_role;

revoke insert, update on profiles from anon, authenticated;
grant insert (id, role, name, phone, under14, guardian, terms_ver) on profiles to authenticated;   -- 트리거가 못 만든 옛 계정 대비
grant update (name, phone, nick) on profiles to authenticated;

revoke select, insert, update on posts, comments from anon, authenticated;
grant select (id, author, nick, board, title, body, attach, likes, report_n, comment_n, staff, solved, deleted, at, edited, care) on posts to authenticated;
grant select (id, post_id, author, nick, body, likes, report_n, staff, picked, deleted, at, care) on comments to authenticated;
grant insert (board, title, body, attach) on posts to authenticated;
grant insert (post_id, body) on comments to authenticated;
grant update (board, title, body, attach, edited, deleted) on posts to authenticated;
grant update (deleted) on comments to authenticated;

revoke all on purchases from anon, authenticated; grant select on purchases to authenticated;
revoke all on reports, talk_log, push_later from anon, authenticated;   -- 신고·제한 기록·밤 알림은 함수로만(누가 신고했는지 API 로 안 보인다)
revoke execute on function report_item(text, uuid, text), clear_reports(text, uuid), care_done(text, uuid), reported_list(), my_reports(), my_reports_seen(),
  talk_limit(uuid, int, text, text, boolean, text), talk_limits(), talk_ok(), my_talk() from public, anon;
grant execute on function report_item(text, uuid, text), clear_reports(text, uuid), care_done(text, uuid), reported_list(), my_reports(), my_reports_seen(),
  talk_limit(uuid, int, text, text, boolean, text), talk_limits(), talk_ok(), my_talk() to authenticated;   -- 원장 함수는 안에서 원장만 결과를 받는다
revoke all on push_tokens from anon, authenticated; grant select, delete on push_tokens to authenticated;
revoke all on feedback from anon, authenticated; grant select, insert (kind, body, ref, ver) on feedback to authenticated;
grant usage on sequence feedback_id_seq to authenticated;
revoke execute on function feedback_list(), feedback_done(bigint, boolean) from public, anon; grant execute on function feedback_list(), feedback_done(bigint, boolean) to authenticated;
revoke all on notes from anon, authenticated; grant select, delete on notes to authenticated;
grant insert (id, date, title, body, cids, updated_at), update (id, date, title, body, cids, updated_at) on notes to authenticated;   -- 올리기(upsert)가 id 도 SET 한다 · 남의 행은 RLS 가 막는다
revoke all on guardian_links from anon, authenticated; grant select on guardian_links to authenticated;   -- 연결·해제는 link_code()·unlink_child()·guardian_decide() 로만
revoke execute on function guardian_requests(), guardian_decide(uuid, text, boolean), my_guardians() from public, anon;
grant execute on function guardian_requests(), guardian_decide(uuid, text, boolean), my_guardians() to authenticated;
revoke all on client_errors from anon, authenticated; grant insert (ver, msg, stack, url, ua) on client_errors to anon, authenticated; grant select on client_errors to authenticated;
grant usage, select on sequence client_errors_id_seq to anon, authenticated;

-- ═══ 행 단위 보안(RLS) ═══
alter table students enable row level security;   alter table classes enable row level security;
alter table attendance enable row level security; alter table notices enable row level security;
alter table notice_reads enable row level security; alter table sched enable row level security;
alter table profiles enable row level security;   alter table progress enable row level security;
alter table passes enable row level security;     alter table purchases enable row level security;
alter table posts enable row level security;      alter table comments enable row level security;
alter table push_tokens enable row level security; alter table client_errors enable row level security;
alter table guardian_links enable row level security;
alter table notes enable row level security;
alter table feedback enable row level security;
alter table reports enable row level security; alter table talk_log enable row level security; alter table push_later enable row level security;

do $$ declare p record; begin      -- 다시 실행해도 되게 기존 정책을 비운다
  for p in select policyname, tablename from pg_policies where schemaname = 'public' loop
    execute format('drop policy %I on %I', p.policyname, p.tablename); end loop; end $$;

-- 원장: 운영 표 전부
create policy owner_all on students     for all to authenticated using ((select is_owner())) with check ((select is_owner()));
create policy owner_all on classes      for all to authenticated using ((select is_owner())) with check ((select is_owner()));
create policy owner_all on attendance   for all to authenticated using ((select is_owner())) with check ((select is_owner()));
create policy owner_all on notices      for all to authenticated using ((select is_owner())) with check ((select is_owner()));
create policy owner_all on notice_reads for all to authenticated using ((select is_owner())) with check ((select is_owner()));
create policy owner_all on sched        for all to authenticated using ((select is_owner())) with check ((select is_owner()));
create policy owner_all on passes       for all to authenticated using ((select is_owner())) with check ((select is_owner()));
create policy owner_all on posts        for all to authenticated using ((select is_owner())) with check ((select is_owner()));
create policy owner_all on comments     for all to authenticated using ((select is_owner())) with check ((select is_owner()));
create policy owner_read on profiles      for select to authenticated using ((select is_owner()));
create policy owner_read on progress      for select to authenticated using ((select is_owner()));
create policy owner_read on purchases     for select to authenticated using ((select is_owner()));
create policy owner_read on client_errors for select to authenticated using ((select is_owner()));

-- 학생·보호자: 연결된 코드(자녀 코드)와 그 반 것만
create policy classes_read   on classes      for select using (true);
create policy mine_students  on students     for select to authenticated using (code in (select my_codes()) and until >= kst_today());
create policy mine_att       on attendance   for select to authenticated using (code in (select my_codes()));
create policy mine_notices   on notices      for select to authenticated using (cls = '전체' or cls in (select my_classes()));
create policy mine_sched     on sched        for select to authenticated using (cls = '전체' or cls in (select my_classes()));
create policy mine_reads     on notice_reads for select to authenticated using (code in (select my_codes()));
create policy mine_reads_ins on notice_reads for insert to authenticated with check (code = (select my_student_code()));
create policy self_profile   on profiles     for select to authenticated using (id = (select auth.uid()));
create policy self_profile_ins on profiles   for insert to authenticated with check (id = (select auth.uid()) and role in ('student','parent'));
create policy self_profile_upd on profiles   for update to authenticated using (id = (select auth.uid())) with check (id = (select auth.uid()));
create policy self_purchases on purchases    for select to authenticated using (uid = (select auth.uid()));
create policy self_push      on push_tokens  for select to authenticated using (uid = (select auth.uid()));
create policy self_children  on guardian_links for select to authenticated using (uid = (select auth.uid()));
create policy owner_read on guardian_links for select to authenticated using ((select is_owner()));
create policy self_push_del  on push_tokens  for delete to authenticated using (uid = (select auth.uid()));
create policy errors_ins     on client_errors for insert with check (uid is null or uid = (select auth.uid()));
-- 진도: 읽기는 내 코드·자녀 코드·내 계정 키, 쓰기는 내 코드·내 계정 키만(보호자는 못 고친다)
create policy prog_read on progress for select to authenticated
  using (code in (select my_codes()) or code = 'u:' || (select auth.uid())::text);
create policy prog_ins  on progress for insert to authenticated
  with check ((code = (select my_student_code()) or code = 'u:' || (select auth.uid())::text) and (select consent_ok()));
create policy prog_upd  on progress for update to authenticated
  using (code = (select my_student_code()) or code = 'u:' || (select auth.uid())::text)
  with check ((code = (select my_student_code()) or code = 'u:' || (select auth.uid())::text) and (select consent_ok()));
-- 노트: 내 것만 · 만 14세 미만 보호자 동의 전에는 서버에 올리지 않는다(앱은 기기 안에 둔다)
create policy note_sel on notes for select to authenticated using (uid = (select auth.uid()));
create policy note_ins on notes for insert to authenticated with check (uid = (select auth.uid()) and (select consent_ok()));
create policy note_upd on notes for update to authenticated using (uid = (select auth.uid())) with check (uid = (select auth.uid()) and (select consent_ok()));
create policy note_del on notes for delete to authenticated using (uid = (select auth.uid()));
-- 의견: 보낸 사람은 자기 것만 본다(원장은 feedback_list 로). 고치기·지우기 없음
create policy fb_sel on feedback for select to authenticated using (uid = (select auth.uid()));
create policy fb_ins on feedback for insert to authenticated with check (uid = (select auth.uid()) and (select consent_ok()));
-- 이야기: 로그인한 사람은 지워지지 않았고 신고 3건 미만인 글을 본다(자기 글은 늘 보인다). 자기 글만 고치고 지운다(되살리기는 안 됨)
create policy read_posts on posts for select to authenticated using (not deleted and (report_n < 3 or author = (select auth.uid())) and (select consent_ok()));
create policy write_posts on posts for insert to authenticated with check (author = (select auth.uid()) and (select consent_ok()) and (select talk_ok()));   -- 보호자·손님·이용 제한 중은 못 쓴다
create policy edit_posts on posts for update to authenticated using (author = (select auth.uid()) and not deleted) with check (author = (select auth.uid()));
create policy read_comments on comments for select to authenticated using (not deleted and (report_n < 3 or author = (select auth.uid())) and (select consent_ok())
  and exists (select 1 from posts p where p.id = post_id));   -- 가려진 글의 댓글도 가린다(글 정책이 그대로 걸림)
create policy write_comments on comments for insert to authenticated
  with check (author = (select auth.uid()) and (select consent_ok()) and (select talk_ok()) and exists (select 1 from posts p where p.id = post_id and not p.deleted));
create policy edit_comments on comments for update to authenticated using (author = (select auth.uid()) and not deleted) with check (author = (select auth.uid()));

-- 닉네임: 선생님·원장 사칭 금지(진짜 선생님 글에는 서버가 '선생님' 표시를 단다) · 연락처·아이디·학교+학년+이름도 안 됨.
--  앱(NICK_BAN · nickBad)과 같은 말 목록 · 띄어쓰기·점·밑줄은 빼고 본다 — 앱은 통과시키고 서버가 막아 안내가 달라지던 것(docs/11 §11)
create or replace function private.nick_bad(t text) returns boolean language sql immutable as $$
  select lower(regexp_replace(coalesce(t, ''), '[\s._\-·]', '', 'g')) ~ '(선생|쌤|원장|관리|운영|매니저|교사|강사|admin|teacher|staff|manager|official)' $$;
create or replace function private.check_nick() returns trigger language plpgsql security definer set search_path = public, private as $$
begin
  if new.nick is distinct from old.nick and not is_owner() then
    if private.nick_bad(new.nick) then
      raise exception '선생님·원장·관리자로 보이는 닉네임은 쓸 수 없습니다.' using errcode = 'P0001'; end if;
    if cardinality(private.pii_kinds(coalesce(new.nick, ''))) > 0 then
      raise exception '닉네임에 연락처나 아이디를 넣지 마세요.' using errcode = 'P0001'; end if;
  end if;
  return new;
end $$;
drop trigger if exists profiles_nick on profiles;
create trigger profiles_nick before update of nick on profiles for each row execute function private.check_nick();

-- 학생 코드가 지워지면 그 진도도 지운다
create or replace function private.drop_progress() returns trigger language plpgsql security definer set search_path = public as $$
begin delete from progress where code = old.code; return old; end $$;
drop trigger if exists students_drop_progress on students;
create trigger students_drop_progress after delete on students for each row execute function private.drop_progress();

-- ═══ 보관 기간이 지난 기록 지우기(개인정보처리방침 3항) — 오류 기록 90일 · 틀린 입력 기록 1일 · 처리 끝난 신고·이용 제한 기록 6개월 · 보호자 동의가 7일 안에 없는 만 14세 미만 계정 ═══
create or replace function private.purge_old() returns void language sql security definer set search_path = public, private as $$
  delete from client_errors where at < now() - interval '90 days';
  delete from private.attempts where at < now() - interval '1 day';
  delete from private.consent_links where at < now() - interval '8 days';
  delete from feedback where at < now() - interval '1 year';
  delete from comments where deleted and deleted_at < now() - interval '6 months';
  delete from posts where deleted and deleted_at < now() - interval '6 months';
  delete from reports where state <> 'open' and resolved_at < now() - interval '6 months';   -- 처리 끝난 신고 기록 6개월(처리방침 3③)
  delete from talk_log where at < now() - interval '6 months';                               -- 이용 제한 기록 6개월
  update profiles set talk_until = null, talk_reason = '' where talk_until < kst_today();   -- 끝난 제한은 사유까지 지운다
  delete from push_later where at < now() - interval '2 days';                               -- 못 보낸 밤 알림(보통은 아침에 보내고 바로 지운다)
  delete from auth.users where id in (select id from profiles where under14 and not guardian_ok
    and ((guardian_at is null and created_at < now() - interval '7 days') or (guardian_how = 'reset' and guardian_at < now() - interval '7 days')));   -- 보호자가 동의를 표시했고 학원 확인만 남은 계정은 두고 원장 목록에 남긴다 · '번호 다름'으로 되돌린 계정은 그때부터 7일
$$;
-- Supabase 에서는 pg_cron 으로 매일 새벽 4시에 돌린다(Database → Extensions 에서 pg_cron 켠 뒤 이 파일을 다시 실행)
-- 매일 새벽 정리가 돌아야 처리방침의 보관 기간(오류 90일·IP 1일·의견 1년·동의 없는 14세 미만 7일)이 지켜진다 — pg_cron 을 켠다(Supabase 는 된다)
do $$ begin
  begin create extension if not exists pg_cron; exception when others then raise notice 'pg_cron 을 켜지 못했습니다 — Supabase Database › Extensions 에서 켠 뒤 이 파일을 다시 실행하세요: %', sqlerrm; end;
  if exists (select 1 from pg_extension where extname = 'pg_cron') then
    perform cron.schedule('pcs-purge-old', '0 19 * * *', 'select private.purge_old()');   -- 19시 UTC = 04시 KST
  end if;
end $$;

-- ═══ 크기·개수 한도(2026-10-01 점검: 로그인 없이 오류 기록을 무한히 넣어 DB 를 채우거나, 3MB 첨부·200,000자 닉네임이 들어갔다) ═══
create or replace function private.errors_cap() returns trigger language plpgsql security definer set search_path = public as $$
begin
  if new.uid is not null and (select count(*) from client_errors where uid = new.uid and at > now() - interval '1 hour') >= 30 then return null; end if;
  if new.uid is null and (select count(*) from client_errors where uid is null and at > now() - interval '1 hour') >= 300 then return null; end if;
  if (select count(*) from client_errors where at > now() - interval '1 hour') >= 3000 then return null; end if;
  return new;
end $$;
drop trigger if exists client_errors_cap on client_errors;
create trigger client_errors_cap before insert on client_errors for each row execute function private.errors_cap();
-- 지운 글·댓글은 6개월 뒤 실제로 지운다(처리방침 3③) — 지운 시각을 서버가 적는다
create or replace function private.mark_deleted() returns trigger language plpgsql security definer set search_path = public as $$
begin
  if new.deleted and not coalesce(old.deleted, false) then new.deleted_at := now(); end if;
  return new;
end $$;
drop trigger if exists posts_deleted_at on posts;
create trigger posts_deleted_at before update of deleted on posts for each row execute function private.mark_deleted();
drop trigger if exists comments_deleted_at on comments;
create trigger comments_deleted_at before update of deleted on comments for each row execute function private.mark_deleted();
-- 내 글·댓글 지우기 — 함수로. PostgREST 는 고칠 때 RETURNING 을 붙여, 지운 줄(deleted)이 읽기 정책(not deleted)에 걸려
--  학생이 자기 글을 지우지 못했다(2026-10-02 시험에서 발견 · 원장은 owner_all 이라 몰랐다). 제한 중에도 지우기는 된다(약관·docs/11).
create or replace function delete_item(p_kind text, p_id uuid) returns boolean language plpgsql security definer set search_path = public, private as $$
declare n int;
begin
  if auth.uid() is null then raise exception '로그인이 필요합니다' using errcode = '42501'; end if;
  if p_kind = 'post' then update posts set deleted = true where id = p_id and not deleted and (author = auth.uid() or is_owner());
  elsif p_kind = 'comment' then update comments set deleted = true where id = p_id and not deleted and (author = auth.uid() or is_owner());
  else raise exception '알 수 없는 종류' using errcode = '22023'; end if;
  get diagnostics n = row_count; return n > 0;
end $$;
revoke execute on function delete_item(text, uuid) from public, anon; grant execute on function delete_item(text, uuid) to authenticated;
-- 원장: 앱을 지운 사람이 전화·메일로 계정 삭제를 요청했을 때(처리방침 6①·삭제 안내) — 앱의 '계정 삭제'와 같은 정리를 한다
create or replace function delete_user(p_email text) returns json language plpgsql security definer set search_path = public, private as $$
declare u uuid;
begin
  if not is_owner() then raise exception 'owner only' using errcode = '42501'; end if;
  select id into u from auth.users where lower(email) = lower(trim(p_email));
  if u is null then return json_build_object('ok', false, 'why', '그 이메일로 가입한 계정이 없습니다.'); end if;
  if u = auth.uid() then return json_build_object('ok', false, 'why', '원장 계정은 여기서 지울 수 없습니다.'); end if;
  update posts set likes = array_remove(likes, u) where u = any(likes);
  update comments set likes = array_remove(likes, u) where u = any(likes);   -- 신고는 계정과 함께 연쇄 삭제(신고 수는 트리거가 다시 맞춘다)
  delete from progress where code = 'u:' || u::text;
  delete from progress where code = (select student_code from profiles where id = u);
  delete from client_errors where uid = u; delete from private.attempts where uid = u; delete from private.consent_links where uid = u;
  delete from auth.users where id = u;
  return json_build_object('ok', true);
end $$;
revoke execute on function delete_user(text) from public, anon; grant execute on function delete_user(text) to authenticated;
-- 진도 저장 시각은 서버 시계로(기기 시계가 틀린 폰의 기록이 밀리거나 남의 기록을 덮지 않게 — 2026-10-01 점검)
create or replace function private.progress_at() returns trigger language plpgsql security definer set search_path = public as $$
begin
  new.state := jsonb_set(coalesce(new.state, '{}'::jsonb), '{at}', to_jsonb(to_char(clock_timestamp() at time zone 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"')));
  new.at := clock_timestamp();
  return new;
end $$;
drop trigger if exists progress_at on progress;
create trigger progress_at before insert or update on progress for each row execute function private.progress_at();
-- 글 수정 시각은 서버가 적는다(아무 날짜나 넣지 못하게)
create or replace function private.post_edited() returns trigger language plpgsql security definer set search_path = public as $$
begin
  new.edited := case when new.title is distinct from old.title or new.body is distinct from old.body or new.attach is distinct from old.attach then now() else old.edited end;
  return new;
end $$;
drop trigger if exists posts_edited on posts;
create trigger posts_edited before update on posts for each row execute function private.post_edited();
do $$ begin
  if not exists (select 1 from pg_constraint where conname = 'posts_attach_shape') then
    alter table posts add constraint posts_attach_shape check (attach is null or (jsonb_typeof(attach) = 'object' and octet_length(attach::text) <= 300
      and attach->>'kind' in ('concept','bank') and coalesce(attach->>'id', '') ~ '^[A-Za-z0-9_#.㉠-㉢-]{1,60}$')) not valid; end if;
  if not exists (select 1 from pg_constraint where conname = 'progress_size') then
    alter table progress add constraint progress_size check (octet_length(state::text) < 500000) not valid; end if;
  if not exists (select 1 from pg_constraint where conname = 'profiles_lengths') then
    alter table profiles add constraint profiles_lengths check (char_length(nick) <= 12 and char_length(name) <= 40 and phone ~ '^[0-9+ ()-]{0,20}$') not valid; end if;
end $$;

-- ═══ [설정] 앞의 -- 를 지우고 원장님 이메일로 바꿔 실행 ═══
-- insert into private.config values ('owner_email', '원장님@이메일') on conflict (k) do update set v = excluded.v;
-- update profiles set role = 'owner' where id in (select id from auth.users where lower(email) = lower((select v from private.config where k = 'owner_email')));
-- ▼ 원장님이 가입하고 메일 인증까지 마친 뒤 한 번 — 원장 계정을 id 로 못 박는다(그 뒤엔 이메일이 같아도 다른 계정은 원장이 못 된다)
-- insert into private.config select 'owner_uid', id::text from auth.users where lower(email) = lower((select v from private.config where k = 'owner_email')) and email_confirmed_at is not null on conflict (k) do update set v = excluded.v;
-- 출석 씨앗은 자동으로 만든다(아무도 몰라야 하는 값)
insert into private.config values ('attend_secret', encode(gen_random_bytes(24), 'hex')) on conflict (k) do nothing;

-- 뒤에서 만든 private 함수까지 다시 잠근다(맨 위의 일괄 회수는 그 뒤에 만든 함수에 안 걸린다)
revoke all on all functions in schema private from public, anon, authenticated;

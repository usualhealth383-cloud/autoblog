-- 박찬 과학 앱 — Supabase(Postgres) 스키마 v3 · 2026-09-29
-- 앱의 서버 어댑터(app-shell.html 의 serverDB)와 1:1 로 맞춘 표·함수·행 단위 보안(RLS)이다.
-- 새 프로젝트의 SQL Editor 에 통째로 붙여 넣고 한 번 실행한다. 여러 번 실행해도 된다.
-- 실행 뒤 맨 아래 [설정] 두 줄(원장 이메일·출석 씨앗)을 원장님 값으로 바꿔 한 번 더 실행한다.
--
-- 보안 원칙
--  · 학생·보호자가 직접 고칠 수 있는 칸은 이름·연락처·닉네임뿐이다. 역할·이용권 만료일·학원 코드는 함수로만 바뀐다.
--  · 학원 코드 연결은 link_code() 한 곳 — 틀린 코드는 1시간에 10번까지, 한 학생 코드는 학생 계정 하나에만.
--  · 원장 = 설정한 이메일로 로그인했고 그 메일을 인증한 계정.
--  · 날짜·시각은 모두 한국 시간(Asia/Seoul). 서버 기본값(UTC)이면 저녁 수업이 지각으로 안 잡힌다.

create extension if not exists pgcrypto;
do $$ begin execute format('alter database %I set timezone to %L', current_database(), 'Asia/Seoul'); end $$;
set timezone to 'Asia/Seoul';

-- ── 비공개 설정(앱 API 로는 보이지 않는 스키마) ──
create schema if not exists private;
revoke all on schema private from public;
create table if not exists private.config (k text primary key, v text not null);
-- 틀린 코드 입력 기록(학원 코드·출석 코드·이용권 코드 무차별 대입 방지)
create table if not exists private.attempts (uid uuid, kind text not null, ok boolean not null, at timestamptz not null default now());
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
  child_code   text references students(code) on delete set null,
  pass_until   date,
  under14      boolean not null default false,       -- 만 14세 미만(법정대리인 동의)
  guardian     text not null default '',             -- 법정대리인 성명·연락처
  terms_ver    text not null default '',             -- 동의한 약관 판(날짜)
  agreed_at    timestamptz,
  created_at   timestamptz not null default now()
);
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
  uid        uuid not null references auth.users(id) on delete cascade,
  product    text not null,
  order_id   text,
  platform   text not null default 'android',
  days       int not null,
  until      date not null,
  raw        jsonb,
  at         timestamptz not null default now()
);

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
  reports   uuid[] not null default '{}',           -- 누가 신고했는지는 API 로 보이지 않는다(report_n 만)
  report_n  int not null default 0,
  comment_n int not null default 0,
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
  reports uuid[] not null default '{}',
  report_n int not null default 0,
  picked  boolean not null default false,
  deleted boolean not null default false,
  at      timestamptz not null default now()
);
create index if not exists posts_at_idx      on posts (at desc);
create index if not exists comments_post_idx on comments (post_id, at);

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
create or replace function is_owner() returns boolean language sql stable security definer set search_path = public, private as $$
  select exists (select 1 from auth.users u join private.config c on c.k = 'owner_email'
                 where u.id = auth.uid() and lower(u.email) = lower(c.v) and u.email_confirmed_at is not null);
$$;
create or replace function my_student_code() returns text language sql stable security definer set search_path = public as $$
  select student_code from profiles where id = auth.uid() and role = 'student' $$;
create or replace function my_codes() returns setof text language sql stable security definer set search_path = public as $$
  select student_code from profiles where id = auth.uid() and student_code is not null
  union select child_code from profiles where id = auth.uid() and child_code is not null $$;
create or replace function my_classes() returns setof text language sql stable security definer set search_path = public as $$
  select cls from students where code in (select my_codes()) and until >= kst_today() $$;

-- 틀린 입력 제한: 최근 1시간 실패가 n번 이상이면 true
create or replace function private.too_many(k text, n int) returns boolean language sql stable security definer set search_path = private as $$
  select count(*) >= n from private.attempts where uid = auth.uid() and kind = k and not ok and at > now() - interval '1 hour' $$;
create or replace function private.note(k text, good boolean) returns void language sql security definer set search_path = private as $$
  insert into private.attempts(uid, kind, ok) values (auth.uid(), k, good) $$;

-- ═══ 가입하면 프로필을 만든다(역할은 학생·보호자만 — 원장은 설정한 이메일만) ═══
create or replace function private.on_signup() returns trigger language plpgsql security definer set search_path = public, private as $$
declare m jsonb := coalesce(new.raw_user_meta_data, '{}'::jsonb); r text := coalesce(m->>'role', 'student');
begin
  if r not in ('student','parent') then r := 'student'; end if;
  if exists (select 1 from private.config where k = 'owner_email' and lower(v) = lower(new.email)) then r := 'owner'; end if;
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
    if p_kind = 'student' then update profiles set student_code = null where id = u; else update profiles set child_code = null where id = u; end if;
    return json_build_object('ok', true);
  end if;
  if private.too_many('code', 10) then return json_build_object('ok', false, 'why', '코드를 여러 번 틀렸습니다. 1시간 뒤에 다시 시도하거나 원장님께 문의해 주세요.'); end if;
  select * into s from students where code = c;
  if not found then perform private.note('code', false); return json_build_object('ok', false, 'why', '등록되지 않은 코드입니다. 원장님께 받은 코드를 확인해 주세요.'); end if;
  if s.until < kst_today() then return json_build_object('ok', false, 'why', '수강 기간이 ' || to_char(s.until, 'FMMM"월" FMDD"일"') || '에 끝났습니다. 원장님께 문의해 주세요.'); end if;
  if p_kind = 'student' then
    if pr.role <> 'student' then return json_build_object('ok', false, 'why', '학생 계정에서만 학원 코드를 등록할 수 있습니다.'); end if;
    if exists (select 1 from profiles where student_code = c and id <> u) then
      return json_build_object('ok', false, 'why', '이 코드는 이미 다른 학생 계정에 연결되어 있습니다. 원장님께 문의해 주세요.'); end if;
    update profiles set student_code = c, name = case when name = '' then s.name else name end where id = u;
  else
    if pr.role <> 'parent' then return json_build_object('ok', false, 'why', '보호자 계정에서만 자녀를 연결할 수 있습니다.'); end if;
    update profiles set child_code = c where id = u;
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
    'guardians', coalesce((select json_agg(json_build_object('name', name, 'phone', phone)) from profiles where child_code = p_code), '[]'::json))
  end $$;

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
  if p.used_by is not null then return json_build_object('ok', false, 'why', '이미 사용된 코드입니다.'); end if;
  select greatest(coalesce(pass_until, kst_today()), kst_today()) into base from profiles where id = auth.uid();
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
  select * into old from purchases where purchase_token = p_token;
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
  select * into p from purchases where purchase_token = p_token; if not found then return; end if;
  update profiles set pass_until = greatest(kst_today() - 1, pass_until - p.days) where id = p.uid;
  delete from purchases where purchase_token = p_token;
end $$;

-- ═══ 이야기: 글쓴이·닉네임은 서버가 채운다 · 도배 제한 · 댓글 수 ═══
create or replace function private.stamp_author() returns trigger language plpgsql security definer set search_path = public as $$
declare n int;
begin
  if not is_owner() then new.author := auth.uid(); end if;
  if new.author is null then raise exception '로그인이 필요합니다' using errcode = '42501'; end if;
  select coalesce(nullif(nick, ''), '익명') into new.nick from profiles where id = new.author;
  new.nick := coalesce(new.nick, '익명');
  new.likes := '{}'; new.reports := '{}'; new.report_n := 0; new.deleted := false; new.at := now();
  if tg_table_name = 'posts' then
    new.comment_n := 0; new.solved := false;
    select count(*) into n from posts where author = new.author and at > now() - interval '10 minutes';
    if n >= 5 and not is_owner() then raise exception '글은 10분에 5개까지 올릴 수 있습니다. 잠시 뒤에 올려 주세요.' using errcode = 'P0001'; end if;
  else
    new.picked := false;
    select count(*) into n from comments where author = new.author and at > now() - interval '10 minutes';
    if n >= 20 and not is_owner() then raise exception '댓글은 10분에 20개까지 달 수 있습니다. 잠시 뒤에 달아 주세요.' using errcode = 'P0001'; end if;
  end if;
  return new;
end $$;
drop trigger if exists posts_stamp on posts;       create trigger posts_stamp    before insert on posts    for each row execute function private.stamp_author();
drop trigger if exists comments_stamp on comments; create trigger comments_stamp before insert on comments for each row execute function private.stamp_author();
create or replace function private.count_comments() returns trigger language plpgsql security definer set search_path = public as $$
begin
  update posts set comment_n = (select count(*) from comments where post_id = coalesce(new.post_id, old.post_id) and not deleted)
   where id = coalesce(new.post_id, old.post_id);
  return null;
end $$;
drop trigger if exists comments_count on comments;
create trigger comments_count after insert or update of deleted or delete on comments for each row execute function private.count_comments();

create or replace function like_toggle(p_kind text, p_id uuid) returns void language plpgsql security definer set search_path = public as $$
declare u uuid := auth.uid();
begin
  if u is null then raise exception '로그인이 필요합니다' using errcode = '42501'; end if;
  if p_kind = 'post' then update posts set likes = case when u = any(likes) then array_remove(likes, u) else likes || u end where id = p_id and not deleted;
  else update comments set likes = case when u = any(likes) then array_remove(likes, u) else likes || u end where id = p_id and not deleted; end if;
end $$;
create or replace function report_item(p_kind text, p_id uuid) returns int language plpgsql security definer set search_path = public as $$
declare u uuid := auth.uid(); c int;
begin
  if u is null then raise exception '로그인이 필요합니다' using errcode = '42501'; end if;
  if p_kind = 'post' then
    update posts set reports = case when u = any(reports) then reports else reports || u end,
                     report_n = cardinality(case when u = any(reports) then reports else reports || u end)
     where id = p_id returning report_n into c;
  else
    update comments set reports = case when u = any(reports) then reports else reports || u end,
                        report_n = cardinality(case when u = any(reports) then reports else reports || u end)
     where id = p_id returning report_n into c;
  end if;
  return coalesce(c, 0);
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
end $$;
create or replace function delete_my_account() returns void language plpgsql security definer set search_path = public as $$
declare u uuid := auth.uid();
begin
  if u is null then raise exception 'login required' using errcode = '42501'; end if;
  delete from progress where code = 'u:' || u::text;
  delete from progress where code = (select student_code from profiles where id = u);
  delete from auth.users where id = u;      -- 프로필·글·댓글·푸시 기기·결제 기록은 연쇄 삭제
end $$;
-- 푸시 받을 기기 목록(서비스 키 전용 · push 함수가 부른다): 공지/일정 → 그 반 학생·보호자, 출석 → 그 학생의 보호자
create or replace function push_targets(p_kind text, p_cls text, p_code text) returns table(token text, uid uuid, who text)
language sql stable security definer set search_path = public as $$
  with codes as (
    select code from students where p_kind in ('notice','sched') and (p_cls = '전체' or cls = p_cls) and until >= kst_today()
    union select p_code where p_kind = 'attend'
  )
  select t.token, t.uid, case when pr.role = 'parent' then 'parent' else 'student' end
    from push_tokens t join profiles pr on pr.id = t.uid
   where (p_kind <> 'attend' and pr.student_code in (select code from codes))
      or pr.child_code in (select code from codes)
$$;

-- ═══ 권한 — Supabase 는 public 표에 전부 열어 두므로, 여기서 칸 단위로 다시 좁힌다 ═══
revoke all on all functions in schema private from public, anon, authenticated;
revoke execute on function grant_purchase(uuid, text, text, text, int, jsonb), revoke_purchase(text), push_targets(text, text, text) from public, anon, authenticated;
grant execute on function grant_purchase(uuid, text, text, text, int, jsonb), revoke_purchase(text), push_targets(text, text, text) to service_role;

revoke insert, update on profiles from anon, authenticated;
grant insert (id, role, name, phone, under14, guardian, terms_ver) on profiles to authenticated;   -- 트리거가 못 만든 옛 계정 대비
grant update (name, phone, nick) on profiles to authenticated;

revoke select, insert, update on posts, comments from anon, authenticated;
grant select (id, author, nick, board, title, body, attach, likes, report_n, comment_n, solved, deleted, at, edited) on posts to authenticated;
grant select (id, post_id, author, nick, body, likes, report_n, picked, deleted, at) on comments to authenticated;
grant insert (board, title, body, attach) on posts to authenticated;
grant insert (post_id, body) on comments to authenticated;
grant update (board, title, body, attach, edited, deleted) on posts to authenticated;
grant update (deleted) on comments to authenticated;

revoke all on purchases from anon, authenticated; grant select on purchases to authenticated;
revoke all on push_tokens from anon, authenticated; grant select, delete on push_tokens to authenticated;
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
create policy self_push_del  on push_tokens  for delete to authenticated using (uid = (select auth.uid()));
create policy errors_ins     on client_errors for insert with check (uid is null or uid = (select auth.uid()));
-- 진도: 읽기는 내 코드·자녀 코드·내 계정 키, 쓰기는 내 코드·내 계정 키만(보호자는 못 고친다)
create policy prog_read on progress for select to authenticated
  using (code in (select my_codes()) or code = 'u:' || (select auth.uid())::text);
create policy prog_ins  on progress for insert to authenticated
  with check (code = (select my_student_code()) or code = 'u:' || (select auth.uid())::text);
create policy prog_upd  on progress for update to authenticated
  using (code = (select my_student_code()) or code = 'u:' || (select auth.uid())::text)
  with check (code = (select my_student_code()) or code = 'u:' || (select auth.uid())::text);
-- 이야기: 로그인한 사람은 지워지지 않았고 신고 3건 미만인 글을 본다(자기 글은 늘 보인다). 자기 글만 고치고 지운다(되살리기는 안 됨)
create policy read_posts on posts for select to authenticated using (not deleted and (report_n < 3 or author = (select auth.uid())));
create policy write_posts on posts for insert to authenticated with check (author = (select auth.uid()));
create policy edit_posts on posts for update to authenticated using (author = (select auth.uid()) and not deleted) with check (author = (select auth.uid()));
create policy read_comments on comments for select to authenticated using (not deleted and (report_n < 3 or author = (select auth.uid())));
create policy write_comments on comments for insert to authenticated
  with check (author = (select auth.uid()) and exists (select 1 from posts p where p.id = post_id and not p.deleted));
create policy edit_comments on comments for update to authenticated using (author = (select auth.uid()) and not deleted) with check (author = (select auth.uid()));

-- 학생 코드가 지워지면 그 진도도 지운다
create or replace function private.drop_progress() returns trigger language plpgsql security definer set search_path = public as $$
begin delete from progress where code = old.code; return old; end $$;
drop trigger if exists students_drop_progress on students;
create trigger students_drop_progress after delete on students for each row execute function private.drop_progress();

-- ═══ [설정] 앞의 -- 를 지우고 원장님 이메일로 바꿔 실행 ═══
-- insert into private.config values ('owner_email', '원장님@이메일') on conflict (k) do update set v = excluded.v;
-- update profiles set role = 'owner' where id in (select id from auth.users where lower(email) = lower((select v from private.config where k = 'owner_email')));
-- 출석 씨앗은 자동으로 만든다(아무도 몰라야 하는 값)
insert into private.config values ('attend_secret', encode(gen_random_bytes(24), 'hex')) on conflict (k) do nothing;

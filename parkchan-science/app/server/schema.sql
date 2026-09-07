-- 박찬 과학 앱 — Supabase(Postgres) 스키마 · 2026-09-07
-- 앱의 DB 어댑터(app-shell.html 의 DB 객체)와 1:1 로 맞춘 표들이다.
-- 원장님이 Supabase 프로젝트를 만든 뒤 SQL Editor 에 이 파일을 통째로 붙여 넣고 실행한다.

create extension if not exists pgcrypto;

-- 학생 · 코드 (1인 1코드 · 만료일 · 기기 1대)
create table if not exists students (
  code        text primary key,                  -- 6자리, 앱이 발급
  name        text not null,
  cls         text not null,                     -- 월목반 / 화금반 / 수토반 [확인 필요]
  phone       text default '',
  until       date not null,                     -- 수강 만료일. 지나면 앱이 자동으로 닫는다
  device_id   text,                              -- 처음 등록한 기기. 바꾸면 device_changed_at 갱신
  device_changed_at timestamptz,
  joined      date not null default current_date
);

-- 출석 (하루 1건) — 30초 코드는 서버 함수가 검증한다
create table if not exists attendance (
  code    text references students(code) on delete cascade,
  date    date not null default current_date,
  time    time not null default localtime,
  late    boolean not null default false,
  manual  boolean not null default false,        -- 원장님이 명단에서 직접 체크한 것
  primary key (code, date)
);

-- 공지 (반별) 와 읽음
create table if not exists notices (
  id     uuid primary key default gen_random_uuid(),
  cls    text not null,                          -- '전체' 또는 반 이름
  title  text not null,
  body   text default '',
  at     timestamptz not null default now()
);
create table if not exists notice_reads (
  notice_id uuid references notices(id) on delete cascade,
  code      text references students(code) on delete cascade,
  at        timestamptz not null default now(),
  primary key (notice_id, code)
);

-- 학습 진도(기기 바뀌어도 이어지도록)
create table if not exists progress (
  code   text primary key references students(code) on delete cascade,
  state  jsonb not null default '{}'::jsonb,     -- 앱의 S 객체(done·wrong·설정)
  at     timestamptz not null default now()
);

-- 반별 수업 시작 시각 → 지각 판정 [확인 필요]
create table if not exists classes (
  cls        text primary key,
  start_time time not null
);
insert into classes values ('월목반','18:00'), ('화금반','18:00'), ('수토반','14:00') on conflict do nothing;

-- ── 출석 코드 검증: 30초 창, 비밀 씨앗은 서버만 안다 ──
create or replace function attend_code(win bigint) returns text language sql stable as $$
  select lpad((('x' || substr(md5(current_setting('app.attend_secret', true) || ':' || win), 1, 8))::bit(32)::bigint % 10000)::text, 4, '0');
$$;
-- 현재 창(또는 직전 창)의 코드와 맞으면 출석 기록. 학생 앱은 이 함수만 부른다.
create or replace function mark_attend(p_code text, p_entered text) returns json language plpgsql security definer as $$
declare w bigint := floor(extract(epoch from now()) / 30); s students; c classes; t time := localtime; r attendance;
begin
  select * into s from students where code = p_code and until >= current_date;
  if not found then return json_build_object('ok', false, 'why', '등록되지 않았거나 만료된 코드입니다.'); end if;
  if p_entered not in (attend_code(w), attend_code(w-1)) then
    return json_build_object('ok', false, 'why', '코드가 맞지 않습니다. 입구 화면의 지금 숫자를 다시 봐 주세요.');
  end if;
  select * into c from classes where cls = s.cls;
  insert into attendance(code, date, time, late) values (p_code, current_date, t, t > coalesce(c.start_time, '18:00'))
    on conflict (code, date) do nothing returning * into r;
  if r.code is null then select * into r from attendance where code = p_code and date = current_date;
    return json_build_object('ok', true, 'dup', true, 'time', to_char(r.time, 'HH24:MI'), 'late', r.late); end if;
  return json_build_object('ok', true, 'time', to_char(r.time, 'HH24:MI'), 'late', r.late);
end $$;


-- ── 원장 화면이 띄우는 '지금 코드' (원장만) ──
create or replace function current_attend_code() returns json language plpgsql security definer as $$
declare w bigint := floor(extract(epoch from now()) / 30);
begin
  if not is_owner() then raise exception 'owner only'; end if;
  return json_build_object('code', attend_code(w), 'win', w);
end $$;
-- ── 원장이 명단에서 직접 체크하는 출석 (원장만) ──
create or replace function mark_attend_manual(p_code text) returns json language plpgsql security definer as $$
declare c classes; s students; t time := localtime; r attendance;
begin
  if not is_owner() then raise exception 'owner only'; end if;
  select * into s from students where code = p_code;
  if not found then return json_build_object('ok', false, 'why', '학생을 찾을 수 없습니다.'); end if;
  select * into c from classes where cls = s.cls;
  insert into attendance(code, date, time, late, manual) values (p_code, current_date, t, t > coalesce(c.start_time, '18:00'), true)
    on conflict (code, date) do nothing returning * into r;
  if r.code is null then select * into r from attendance where code = p_code and date = current_date;
    return json_build_object('ok', true, 'dup', true, 'time', to_char(r.time, 'HH24:MI'), 'late', r.late); end if;
  return json_build_object('ok', true, 'time', to_char(r.time, 'HH24:MI'), 'late', r.late);
end $$;

-- ── 행 단위 보안(RLS): 학생은 자기 코드 것만, 원장은 로그인 계정으로 전부 ──
alter table students     enable row level security;
alter table attendance   enable row level security;
alter table notices      enable row level security;
alter table notice_reads enable row level security;
alter table progress     enable row level security;
alter table classes      enable row level security;

-- 원장님: Supabase Auth 로 로그인한 계정(이메일 1개). 아래 이메일을 원장님 것으로 바꾼다.
create or replace function is_owner() returns boolean language sql stable as $$
  select coalesce(auth.jwt() ->> 'email', '') = 'OWNER_EMAIL_HERE';
$$;
create policy owner_all_students on students     for all using (is_owner()) with check (is_owner());
create policy owner_all_att      on attendance   for all using (is_owner()) with check (is_owner());
create policy owner_all_notices  on notices      for all using (is_owner()) with check (is_owner());
create policy owner_all_reads    on notice_reads for all using (is_owner()) with check (is_owner());
create policy owner_all_progress on progress     for all using (is_owner()) with check (is_owner());
create policy owner_all_classes  on classes      for all using (is_owner()) with check (is_owner());

-- 학생: 앱이 요청 헤더로 자기 코드를 보낸다(x-student-code). 그 코드 행만 보인다.
create or replace function my_code() returns text language sql stable as $$
  select coalesce(current_setting('request.headers', true)::json ->> 'x-student-code', '');
$$;
create policy student_self        on students     for select using (code = my_code() and until >= current_date);
create policy student_att         on attendance   for select using (code = my_code());
create policy student_notices     on notices      for select using (cls = '전체' or cls = (select cls from students where code = my_code()));
create policy student_reads_sel   on notice_reads for select using (code = my_code());
create policy student_reads_ins   on notice_reads for insert with check (code = my_code());
create policy student_progress    on progress     for all using (code = my_code()) with check (code = my_code());
create policy classes_read        on classes      for select using (true);

-- ══ v2: 계정 프로필 · 보호자 · 이용권 ══
-- 프로필: Supabase Auth 사용자(auth.users) 1명당 1행. 역할·이름·연결된 학생 코드(학생) 또는 자녀 코드(보호자)·이용권 만료일
create table if not exists profiles (
  id          uuid primary key references auth.users(id) on delete cascade,
  role        text not null default 'student' check (role in ('student','parent','owner')),
  name        text not null default '',
  phone       text default '',
  student_code text references students(code) on delete set null,
  child_code  text references students(code) on delete set null,
  pass_until  date,
  under14     boolean not null default false,        -- 만 14세 미만(법정대리인 동의 확인)
  guardian    text default '',                       -- 법정대리인 성명·연락처
  created_at  timestamptz not null default now()
);
-- 이용권 코드(원장이 발급, 앱에서 등록)
create table if not exists passes (
  code     text primary key,
  days     int not null,
  issued   date not null default current_date,
  used_by  uuid references auth.users(id) on delete set null,
  used_at  date
);
alter table profiles enable row level security;
alter table passes   enable row level security;
create policy profile_self   on profiles for all using (id = auth.uid()) with check (id = auth.uid() and (role <> 'owner' or is_owner()));
create policy profile_owner  on profiles for select using (is_owner());
create policy passes_owner   on passes   for all using (is_owner()) with check (is_owner());

-- 로그인한 학생·보호자가 헤더 없이도 자기(자녀) 코드로 보이게
create or replace function my_codes() returns setof text language sql stable as $$
  select my_code() union select coalesce(student_code, '') from profiles where id = auth.uid() union select coalesce(child_code, '') from profiles where id = auth.uid();
$$;
drop policy if exists student_self on students;
create policy student_self on students for select using (code in (select my_codes()) and until >= current_date);
drop policy if exists student_att on attendance;
create policy student_att on attendance for select using (code in (select my_codes()));
drop policy if exists student_notices on notices;
create policy student_notices on notices for select using (cls = '전체' or cls in (select cls from students where code in (select my_codes())));
drop policy if exists student_reads_sel on notice_reads;
create policy student_reads_sel on notice_reads for select using (code in (select my_codes()));
drop policy if exists student_progress on progress;
create policy student_progress on progress for all
  using (code in (select my_codes()) or code = 'u:' || coalesce(auth.uid()::text, ''))
  with check (code = my_code() or code = (select student_code from profiles where id = auth.uid()) or code = 'u:' || coalesce(auth.uid()::text, ''));

-- 이용권 등록: 한 번만, 남은 기간이 있으면 그 뒤로 이어 붙인다
create or replace function redeem_pass(p_code text) returns json language plpgsql security definer as $$
declare p passes; pr profiles; base date;
begin
  if auth.uid() is null then return json_build_object('ok', false, 'why', '로그인이 필요합니다.'); end if;
  select * into p from passes where code = p_code;
  if not found then return json_build_object('ok', false, 'why', '없는 이용권 코드입니다.'); end if;
  if p.used_by is not null then return json_build_object('ok', false, 'why', '이미 사용된 코드입니다.'); end if;
  select * into pr from profiles where id = auth.uid();
  base := greatest(coalesce(pr.pass_until, current_date), current_date);
  update profiles set pass_until = base + p.days where id = auth.uid();
  update passes set used_by = auth.uid(), used_at = current_date where code = p_code;
  return json_build_object('ok', true, 'until', (base + p.days)::text);
end $$;
-- 계정 삭제(개인정보 처리방침): 프로필·진도·인증 사용자까지
create or replace function delete_my_account() returns void language plpgsql security definer as $$
begin
  if auth.uid() is null then raise exception 'login required'; end if;
  delete from progress where code = 'u:' || auth.uid()::text;
  delete from profiles where id = auth.uid();
  delete from auth.users where id = auth.uid();
end $$;

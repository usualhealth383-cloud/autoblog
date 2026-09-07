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

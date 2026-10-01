-- 약지도 «부모님께 약 보내기» (설계: yakjido/설계-가족연결.md)
-- 서버에 두는 것은 «자녀가 보내기를 누른 약 목록 하나»뿐. 이름·전화번호·위치는 받지 않는다. 7일 뒤 지운다.
-- 테이블은 공개 키(anon)로 직접 읽고 쓰지 못한다 — Edge Function(share)이 서버 키로만 다룬다.

create table if not exists public.shares (
  id          uuid primary key default gen_random_uuid(),
  code        text not null unique check (char_length(code) between 20 and 40),
  items       jsonb not null check (jsonb_typeof(items) = 'array' and jsonb_array_length(items) between 1 and 10),
  label       text check (label is null or char_length(label) <= 20),       -- 받는 분 호칭(엄마·아빠 등, 선택)
  note        text check (note is null or char_length(note) <= 100),        -- 한 줄 메모(선택)
  consent_at  timestamptz not null,                                          -- 민감정보 처리 동의 시각
  created_at  timestamptz not null default now(),
  expires_at  timestamptz not null default now() + interval '7 days',
  bought_at   timestamptz                                                    -- 부모님이 「샀어요」를 누른 때
);

alter table public.shares enable row level security;
-- 정책을 하나도 두지 않는다 = anon·authenticated 는 아무것도 못 한다(서버 키만 통과)
revoke all on table public.shares from anon, authenticated;

create index if not exists shares_expires_idx on public.shares (expires_at);

-- 매일 새벽 만료분 삭제
create extension if not exists pg_cron;
select cron.schedule('yakjido-shares-expire', '17 18 * * *',   -- UTC 18:17 = 한국 03:17
  $$delete from public.shares where expires_at < now()$$);

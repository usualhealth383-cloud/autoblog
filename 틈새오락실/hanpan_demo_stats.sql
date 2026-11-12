-- 틈새 오락실 · 연령대 · 성별 · 나라별 게임 이용 통계 (2026-11-12)
-- Supabase → SQL Editor 에 통째로 붙여 넣고 Run 한 번. 여러 번 실행해도 안전(멱등).
-- 개인을 알아볼 수 있는 값은 저장하지 않음: 회원이 「선택」으로 알려 준 연령대 · 성별 · 나라 코드만, 이용 기록(events)에 묶음 꼬리표로 붙음.

-- 1) 이용 기록에 꼬리표 칸 (없으면 추가)
alter table public.events add column if not exists demo jsonb;

-- 2) 관리자만: 게임별 이용 횟수를 연령대 · 성별 · 나라로 나눠 보기 (기본 최근 30일)
create or replace function public.admin_game_demo(p_days int default 30) returns jsonb
language plpgsql stable security definer set search_path = public as $$
declare r jsonb;
begin
  if not public.is_admin() then raise exception 'not admin'; end if;
  with ev as (
    select e.demo, coalesce((to_jsonb(e)->>'created_at')::timestamptz, now()) as at, it
    from public.events e, jsonb_array_elements(coalesce(to_jsonb(e)->'items','[]'::jsonb)) it
  ), st as (
    select split_part(it->>'v',':',1) as game,
           coalesce(demo->>'a','?') as age, coalesce(demo->>'g','?') as sex, coalesce(demo->>'cc','?') as cc
    from ev where it->>'k'='start' and at > now() - make_interval(days => greatest(1,least(p_days,365)))
  )
  select jsonb_build_object(
    'days', p_days,
    'plays', (select count(*) from st),
    'tagged', (select count(*) from st where age<>'?' or sex<>'?' or cc<>'?'),
    'by_age', (select coalesce(jsonb_agg(x),'[]') from (select age, game, count(*) n from st group by 1,2 order by 1, 3 desc) x),
    'by_sex', (select coalesce(jsonb_agg(x),'[]') from (select sex, game, count(*) n from st group by 1,2 order by 1, 3 desc) x),
    'by_cc',  (select coalesce(jsonb_agg(x),'[]') from (select cc, game, count(*) n from st group by 1,2 order by 1, 3 desc) x),
    'members', (select coalesce(jsonb_agg(x),'[]') from (select coalesce(age_band,'?') age, coalesce(gender,'?') sex, coalesce(cc,'?') cc, count(*) n from public.profiles group by 1,2,3 order by 4 desc limit 200) x)
  ) into r;
  return r;
end $$;
revoke execute on function public.admin_game_demo(int) from public, anon;
grant execute on function public.admin_game_demo(int) to authenticated;

select 'ok' as done, (select count(*) from public.events) as events;

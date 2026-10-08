// 푸시 알림 — DB 웹훅이 부른다(공지·일정·출석이 새로 들어올 때).
//  공지·일정 → 그 반(또는 전체) 학생·보호자 폰 / 출석 → 그 학생의 보호자 폰("18:02 출석했습니다") / 이야기 댓글 → 그 글쓴이 폰
//  받을 사람은 DB 함수 push_targets() 가 정한다(서비스 키 전용). 없어진 기기 토큰은 지운다.
//  이야기 댓글 알림(2026-10, docs/11 §12-5)
//   · 잠금화면에 댓글 내용·글 제목을 싣지 않는다("새 댓글이 있어요") — 험한 댓글·힘든 마음의 글이 잠금화면에 뜨지 않게
//   · 밤 22시~아침 7시(한국 시간)에 달린 댓글은 보내지 않고 push_later 에 모았다가, 아침 7시 cron({action:'morning'})이 한 번에 "밤사이 새 댓글"로
//   · 원장 폰의 '먼저 살펴볼 글'(힘든 마음의 글·'친구가 걱정돼요' 신고)은 밤에도 바로 간다 — 원장님이 폰 설정으로 직접 정한다
//  보호자 주간 요약(벤치마크 ★5) — 일요일 저녁 cron({action:'weekly'})이 부른다. 받을 사람·숫자는 DB 함수 weekly_digest()(서비스 키 전용)
//   · 원장이 확인한 보호자 · 수강 중인 자녀마다 한 번(자녀 둘이면 알림 둘 — 서로 덮지 않게 자녀별 tag)
//   · 밤 22시~아침 7시에 불리면 보내지 않는다(다음 주에 다시) · 비교·순위 없이 그 주 숫자만, 잠금화면 공개 범위 PRIVATE
//  과제 알림(2026-10-07) — 새 과제(assignments INSERT) → 대상 학생 본인 폰 · 매일 19시 cron({action:'asgdue'}) → 내일 마감인데 아직 안 낸 학생에게 한 번
//   · 밤 22시~아침 7시에는 보내지 않는다(학생은 오늘 화면 맨 위 과제 카드로 본다) · 보호자에게는 보내지 않는다(주간 요약에 과제 제출이 있다)
// 비밀값: FIREBASE_SA_JSON(Firebase 서비스 계정 JSON, project_id 포함), PUSH_SECRET(웹훅 헤더 x-push-secret 값), ACADEMY(학원명, 선택)
import { googleToken, rpc, rest, json, CORS } from '../_shared/google.ts';

const SCOPE = 'https://www.googleapis.com/auth/firebase.messaging';
const FCM = () => Deno.env.get('FCM_API_BASE') || 'https://fcm.googleapis.com';
const md = (d: string) => { const [, m, dd] = d.split('-'); return `${+m}/${+dd}`; };
// 한국 시각(시) — 댓글이 달린 시각(record.at, 서버가 적음) 기준. 없으면 지금
const kstHour = (iso?: string) => { let t = iso ? new Date(iso) : new Date(); if (Number.isNaN(t.getTime())) t = new Date(); return (t.getUTCHours() + 9) % 24; };
const isNight = (iso?: string) => { const h = kstHour(iso); return h >= 22 || h < 7; };

type Msg = { title: string; body: string; kind: string; post?: string; quiet?: boolean; tag?: string; code?: string };
type Job = { args: any; uid?: string; tokens?: { token: string; uid: string }[]; msg: Msg };
// 도움이 필요해 보이는 글·댓글(서버가 care 로 표시) · '친구가 걱정돼요' 신고 → 원장 폰. 잠금화면에 보일 수 있으니 내용은 싣지 않는다
const careJob = (A: string, post: string, worry = false): Job => ({ args: { p_kind: 'care', p_cls: null, p_code: null },
  msg: { kind: 'care', post, quiet: true, title: `[${A}] 먼저 살펴볼 글이 있어요`,
    body: worry ? '친구가 걱정된다는 신고가 들어왔습니다. 원장 화면 → 이야기에서 확인해 주세요.' : '이야기에 도움이 필요해 보이는 글이 올라왔습니다. 원장 화면 → 이야기에서 확인해 주세요.' } });
async function composeAll(table: string, r: Record<string, any>): Promise<Job[]> {
  const A = Deno.env.get('ACADEMY') || '박찬 과학';
  const jobs: Job[] = [];
  if (r.care && !r.staff && (table === 'posts' || table === 'comments')) jobs.push(careJob(A, table === 'posts' ? r.id : r.post_id));
  if (table === 'reports') {
    if (r.reason !== 'worry') return jobs;
    let post = r.post_id;
    if (!post && r.comment_id) post = ((await rest(`comments?id=eq.${encodeURIComponent(r.comment_id)}&select=post_id`))[0] || {}).post_id;
    jobs.push(careJob(A, post || '', true)); return jobs;
  }
  const c = table === 'posts' ? null : await compose(table, r);
  if (c) jobs.push(c);
  return jobs;
}
async function compose(table: string, r: Record<string, any>): Promise<Job | null> {
  const A = Deno.env.get('ACADEMY') || '박찬 과학';
  if (table === 'notices') return { args: { p_kind: 'notice', p_cls: r.cls, p_code: null }, msg: { kind: 'notice', title: `[${A}] ${r.title}`, body: r.body || '공지를 확인해 주세요' } };
  if (table === 'sched') return { args: { p_kind: 'sched', p_cls: r.cls, p_code: null }, msg: { kind: 'sched', title: `[${A}] 일정 · ${md(r.date)} ${r.title}`, body: r.memo || '일정 화면에 들어갔습니다' } };
  if (table === 'assignments') {   // 새 과제 → 대상 학생 본인 폰(밤에 낸 과제는 알리지 않는다 — 다음 날 오늘 화면 맨 위 카드로 본다)
    if (isNight(r.at)) return null;
    const tokens = await rpc('asg_push_targets', { p_aid: r.id });
    return { args: null, tokens, msg: { kind: 'asg', tag: 'asg-' + r.id, title: `[${A}] 새 과제 · ${r.title}`, body: `${md(r.due)}까지 · 앱 오늘 화면 맨 위에서 풀 수 있어요` } };
  }
  if (table === 'attendance') {
    const s = (await rest(`students?code=eq.${encodeURIComponent(r.code)}&select=name`))[0];
    if (!s) return null;
    const t = String(r.time || '').slice(0, 5);
    return { args: { p_kind: 'attend', p_cls: null, p_code: r.code }, msg: { kind: 'attend', title: `[${A}] ${s.name} 학생 ${r.late ? '지각' : '출석'}`, body: `${t}에 ${r.manual ? '선생님이 출석 체크했습니다' : '출석했습니다'}${r.late ? ' (수업 시작 뒤)' : ''}` } };
  }
  if (table === 'comments') {   // 내 글에 댓글 → 글쓴이 폰으로(자기 댓글·지운 글은 빼고)
    const post = (await rest(`posts?id=eq.${encodeURIComponent(r.post_id)}&select=author,deleted`))[0];
    if (!post || post.deleted || post.author === r.author) return null;
    if (isNight(r.at)) {   // 밤에는 모아 두었다가 아침에 한 번
      await rest('push_later', { method: 'POST', headers: { Prefer: 'return=minimal' }, body: JSON.stringify({ uid: post.author, post_id: r.post_id }) });
      return null;
    }
    const who = r.staff ? '선생님이 답을 달았어요' : '내 글에 댓글이 달렸어요';
    // 잠금화면에는 내용을 싣지 않는다 — 글 제목·댓글 앞부분 모두
    return { args: null, uid: post.author, msg: { kind: 'comment', post: r.post_id, quiet: true, title: `[${A}] ${who}`, body: '새 댓글이 있어요. 앱에서 확인해 주세요.' } };
  }
  return null;
}
// 아침 7시: 밤사이 모아 둔 댓글 알림을 사람마다 한 번
async function morningJobs(): Promise<{ jobs: Job[]; upto: string | null }> {
  const A = Deno.env.get('ACADEMY') || '박찬 과학';
  const rows: { uid: string; post_id: string; at: string }[] = await rest('push_later?select=uid,post_id,at&order=at.asc&limit=5000');
  if (!rows.length) return { jobs: [], upto: null };
  const by = new Map<string, { n: number; post: string }>();
  for (const x of rows) { const o = by.get(x.uid) || { n: 0, post: x.post_id }; o.n++; o.post = x.post_id; by.set(x.uid, o); }
  const jobs: Job[] = [...by].map(([uid, o]) => ({ args: null, uid, msg: { kind: 'comment', post: o.post, quiet: true, title: `[${A}] 밤사이 새 댓글이 있어요`, body: `내 글에 새 댓글 ${o.n}개 · 앱에서 확인해 주세요.` } }));
  return { jobs, upto: rows[rows.length - 1].at };
}

// 일요일 저녁: 보호자마다(자녀별) 이번 주 요약 한 줄 — 앱의 '이번 주 요약' 카드로 이어진다
type Due = { token: string; uid: string; n: number; title: string };
async function asgDueJobs(): Promise<Job[]> {
  const A = Deno.env.get('ACADEMY') || '박찬 과학';
  const rows: Due[] = await rpc('asg_due_targets', {});
  return rows.map((d) => ({ args: null, tokens: [{ token: d.token, uid: d.uid }], msg: { kind: 'asg', tag: 'asg-due',
    title: `[${A}] 내일 마감인 과제가 ${d.n}개 있어요`, body: `${d.title}${d.n > 1 ? ` 외 ${d.n - 1}개` : ''} · 오늘 저녁에 풀어 두면 마음이 가벼워요` } }));
}
type Dig = { token: string; uid: string; code: string; name: string; days: number; solved: number; asg_due: number; asg_done: number };
async function weeklyJobs(): Promise<Job[]> {
  const A = Deno.env.get('ACADEMY') || '박찬 과학';
  const rows: Dig[] = await rpc('weekly_digest', {});
  const by = new Map<string, { d: Dig; tokens: { token: string; uid: string }[] }>();
  for (const r of rows || []) { const k = r.uid + '|' + r.code; const o = by.get(k) || { d: r, tokens: [] }; o.tokens.push({ token: r.token, uid: r.uid }); by.set(k, o); }
  return [...by.values()].map(({ d, tokens }) => {
    const parts = d.days ? [`공부한 날 ${d.days}일`] : ['이번 주는 쉬어 갔어요'];
    if (d.solved) parts.push(`푼 문제 ${d.solved}개`);
    if (d.asg_due) parts.push(`과제 ${d.asg_done}/${d.asg_due} 제출`);
    return { args: null, tokens, msg: { kind: 'weekly', tag: 'weekly-' + d.code, code: d.code, quiet: true,
      title: `[${A}] ${d.name} 학생의 이번 주`, body: `${parts.join(' · ')} — 앱에서 이번 주 요약을 볼 수 있어요` } };
  });
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: CORS });
  if (!Deno.env.get('PUSH_SECRET') || req.headers.get('x-push-secret') !== Deno.env.get('PUSH_SECRET')) return json({ ok: false }, 403);
  try {
    const ev = await req.json();
    let jobs: Job[] = [], upto: string | null = null;
    if (ev.action === 'morning') ({ jobs, upto } = await morningJobs());
    else if (ev.action === 'asgdue') {   // 매일 19:00(KST) cron — 내일 마감인데 아직 안 낸 학생에게 한 번
      if (isNight(ev.at)) return json({ ok: true, skipped: 'night', sent: 0 });
      jobs = await asgDueJobs();
    }
    else if (ev.action === 'weekly') {
      if (isNight(ev.at)) return json({ ok: true, skipped: 'night', sent: 0 });   // 밤 22~07시에는 보내지 않는다(ev.at: 시험용 시각, 없으면 지금)
      jobs = await weeklyJobs();
    } else {
      if (ev.type !== 'INSERT' || !ev.record) return json({ ok: true, skipped: 'not insert' });
      jobs = await composeAll(ev.table, ev.record);
    }
    const clear = async () => { if (upto) await rest(`push_later?at=lte.${encodeURIComponent(upto)}`, { method: 'DELETE' }); };
    if (!jobs.length) { await clear(); return json({ ok: true, skipped: ev.table || ev.action, sent: 0 }); }
    const plan: { c: Job; targets: { token: string; uid: string; who?: string }[] }[] = await Promise.all(jobs.map(async (c) => ({ c, targets: c.tokens ? c.tokens : c.uid
      ? await rest(`push_tokens?uid=eq.${encodeURIComponent(c.uid)}&select=token,uid`)
      : await rpc('push_targets', c.args) })));
    const total = plan.reduce((a, x) => a + x.targets.length, 0);
    if (!total) { await clear(); return json({ ok: true, sent: 0 }); }
    const sa = Deno.env.get('FIREBASE_SA_JSON')!, pid = JSON.parse(sa).project_id;
    const at = await googleToken(sa, SCOPE);
    let sent = 0, dropped = 0;
    for (const { c, targets } of plan) {
    await Promise.all(targets.map(async (t) => {
      const r = await fetch(`${FCM()}/v1/projects/${pid}/messages:send`, {
        method: 'POST', headers: { Authorization: `Bearer ${at}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: { token: t.token, notification: { title: c.msg.title, body: c.msg.body },
          data: { kind: c.msg.kind, ...(c.msg.post ? { post: c.msg.post } : {}), ...(c.msg.code ? { code: c.msg.code } : {}) },
          android: { priority: 'HIGH', notification: { channel_id: 'academy', tag: c.msg.tag || c.msg.kind, ...(c.msg.quiet ? { visibility: 'PRIVATE' } : {}) } } } }),
      });
      if (r.ok) { sent++; return; }
      const j = await r.json().catch(() => ({}));
      const code = (j.error?.details || []).map((d: any) => d.errorCode).join(',') + ' ' + (j.error?.status || '');
      if (r.status === 404 || /UNREGISTERED|INVALID_ARGUMENT/.test(code)) {   // 앱을 지웠거나 토큰이 바뀐 기기
        await rest(`push_tokens?token=eq.${encodeURIComponent(t.token)}`, { method: 'DELETE' }).catch(() => null); dropped++;
      }
    }));
    }
    await clear();
    return json({ ok: true, sent, dropped, targets: total });
  } catch (e) {
    console.error(e);
    return json({ ok: false, why: String(e) }, 500);
  }
});

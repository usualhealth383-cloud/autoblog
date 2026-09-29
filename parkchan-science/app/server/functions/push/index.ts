// 푸시 알림 — DB 웹훅이 부른다(공지·일정·출석이 새로 들어올 때).
//  공지·일정 → 그 반(또는 전체) 학생·보호자 폰 / 출석 → 그 학생의 보호자 폰("18:02 출석했습니다")
//  받을 사람은 DB 함수 push_targets() 가 정한다(서비스 키 전용). 없어진 기기 토큰은 지운다.
// 비밀값: FIREBASE_SA_JSON(Firebase 서비스 계정 JSON, project_id 포함), PUSH_SECRET(웹훅 헤더 x-push-secret 값), ACADEMY(학원명, 선택)
import { googleToken, rpc, rest, json, CORS } from '../_shared/google.ts';

const SCOPE = 'https://www.googleapis.com/auth/firebase.messaging';
const FCM = () => Deno.env.get('FCM_API_BASE') || 'https://fcm.googleapis.com';
const md = (d: string) => { const [, m, dd] = d.split('-'); return `${+m}/${+dd}`; };

type Msg = { title: string; body: string; kind: string };
async function compose(table: string, r: Record<string, any>): Promise<{ args: any; msg: Msg } | null> {
  const A = Deno.env.get('ACADEMY') || '박찬 과학';
  if (table === 'notices') return { args: { p_kind: 'notice', p_cls: r.cls, p_code: null }, msg: { kind: 'notice', title: `[${A}] ${r.title}`, body: r.body || '공지를 확인해 주세요' } };
  if (table === 'sched') return { args: { p_kind: 'sched', p_cls: r.cls, p_code: null }, msg: { kind: 'sched', title: `[${A}] 일정 · ${md(r.date)} ${r.title}`, body: r.memo || '일정 화면에 들어갔습니다' } };
  if (table === 'attendance') {
    const s = (await rest(`students?code=eq.${encodeURIComponent(r.code)}&select=name`))[0];
    if (!s) return null;
    const t = String(r.time || '').slice(0, 5);
    return { args: { p_kind: 'attend', p_cls: null, p_code: r.code }, msg: { kind: 'attend', title: `[${A}] ${s.name} 학생 ${r.late ? '지각' : '출석'}`, body: `${t}에 ${r.manual ? '선생님이 출석 체크했습니다' : '출석했습니다'}${r.late ? ' (수업 시작 뒤)' : ''}` } };
  }
  return null;
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: CORS });
  if (!Deno.env.get('PUSH_SECRET') || req.headers.get('x-push-secret') !== Deno.env.get('PUSH_SECRET')) return json({ ok: false }, 403);
  try {
    const ev = await req.json();
    if (ev.type !== 'INSERT' || !ev.record) return json({ ok: true, skipped: 'not insert' });
    const c = await compose(ev.table, ev.record);
    if (!c) return json({ ok: true, skipped: ev.table });
    const targets: { token: string; uid: string; who: string }[] = await rpc('push_targets', c.args);
    if (!targets.length) return json({ ok: true, sent: 0 });
    const sa = Deno.env.get('FIREBASE_SA_JSON')!, pid = JSON.parse(sa).project_id;
    const at = await googleToken(sa, SCOPE);
    let sent = 0, dropped = 0;
    await Promise.all(targets.map(async (t) => {
      const r = await fetch(`${FCM()}/v1/projects/${pid}/messages:send`, {
        method: 'POST', headers: { Authorization: `Bearer ${at}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: { token: t.token, notification: { title: c.msg.title, body: c.msg.body },
          data: { kind: c.msg.kind }, android: { priority: 'HIGH', notification: { channel_id: 'academy', tag: c.msg.kind } } } }),
      });
      if (r.ok) { sent++; return; }
      const j = await r.json().catch(() => ({}));
      const code = (j.error?.details || []).map((d: any) => d.errorCode).join(',') + ' ' + (j.error?.status || '');
      if (r.status === 404 || /UNREGISTERED|INVALID_ARGUMENT/.test(code)) {   // 앱을 지웠거나 토큰이 바뀐 기기
        await rest(`push_tokens?token=eq.${encodeURIComponent(t.token)}`, { method: 'DELETE' }).catch(() => null); dropped++;
      }
    }));
    return json({ ok: true, sent, dropped, targets: targets.length });
  } catch (e) {
    console.error(e);
    return json({ ok: false, why: String(e) }, 500);
  }
});

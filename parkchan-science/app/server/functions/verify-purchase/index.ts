// 스토어 결제 확인 → 이용권 연장 (Google Play 일회성 상품)
//  앱: 결제 끝 → { productId, purchaseToken, orderId } 를 여기로 보낸다(로그인한 사용자 토큰으로).
//  여기: Google Play 에 영수증을 직접 물어 '결제 완료 · 이 계정의 결제'인지 확인 → grant_purchase(같은 영수증은 한 번만) → 소비 처리(다시 살 수 있게).
//  하루 한 번(cron) x-cron-secret 을 붙여 { action:'voided' } 로 부르면 환불·취소된 영수증만큼 기간을 되돌린다.
// 비밀값(Supabase → Edge Functions → Secrets): GOOGLE_SA_JSON(서비스 계정 JSON), ANDROID_PACKAGE, CRON_SECRET
import { googleToken, rpc, rest, json, CORS } from '../_shared/google.ts';

// 상품 ID → 날수. 날수는 서버가 정한다(앱이 보낸 값은 믿지 않는다)
const PRODUCTS: Record<string, number> = { pass_m1: 30, pass_m6: 180, pass_y1: 365 };
const SCOPE = 'https://www.googleapis.com/auth/androidpublisher';
const API = () => (Deno.env.get('GOOGLE_API_BASE') || 'https://androidpublisher.googleapis.com') + '/androidpublisher/v3/applications/' + Deno.env.get('ANDROID_PACKAGE');

async function userOf(req: Request) {
  const auth = req.headers.get('Authorization') || '';
  const r = await fetch(Deno.env.get('SUPABASE_URL') + '/auth/v1/user', { headers: { apikey: Deno.env.get('SUPABASE_ANON_KEY')!, Authorization: auth } });
  return r.ok ? await r.json() : null;
}

async function voided() {
  const at = await googleToken(Deno.env.get('GOOGLE_SA_JSON')!, SCOPE);
  const since = Date.now() - 30 * 86400_000;
  const r = await fetch(`${API()}/purchases/voidedpurchases?startTime=${since}&maxResults=1000`, { headers: { Authorization: `Bearer ${at}` } });
  const j = await r.json(); if (!r.ok) throw new Error('voided: ' + r.status + ' ' + JSON.stringify(j));
  let n = 0;
  for (const v of j.voidedPurchases || []) { await rpc('revoke_purchase', { p_token: v.purchaseToken }); n++; }
  return n;
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: CORS });
  try {
    const body = await req.json().catch(() => ({}));
    if (body.action === 'voided') {
      if (!Deno.env.get('CRON_SECRET') || req.headers.get('x-cron-secret') !== Deno.env.get('CRON_SECRET')) return json({ ok: false, why: 'forbidden' }, 403);
      return json({ ok: true, revoked: await voided() });
    }
    const user = await userOf(req);
    if (!user || !user.id) return json({ ok: false, why: '로그인이 필요합니다.' }, 401);
    const { productId, purchaseToken, orderId } = body;
    const days = PRODUCTS[productId];
    if (!days || typeof purchaseToken !== 'string' || purchaseToken.length < 10) return json({ ok: false, why: '알 수 없는 상품입니다.' }, 400);

    // 만 14세 미만은 보호자 동의가 끝난 뒤에만 이용권을 반영한다. 확인(소비)하지 않은 결제는 Google Play 가 3일 안에 자동 환불한다
    const pr = (await rest(`profiles?id=eq.${encodeURIComponent(user.id)}&select=under14,guardian_ok`))[0];
    if (pr && pr.under14 && !pr.guardian_ok) return json({ ok: false, why: '보호자 동의가 끝난 뒤에 이용권을 살 수 있습니다. 이 결제는 반영하지 않았고 Google Play 가 3일 안에 자동으로 환불합니다.' }, 403);
    const at = await googleToken(Deno.env.get('GOOGLE_SA_JSON')!, SCOPE);
    const url = `${API()}/purchases/products/${encodeURIComponent(productId)}/tokens/${encodeURIComponent(purchaseToken)}`;
    const r = await fetch(url, { headers: { Authorization: `Bearer ${at}` } });
    const p = await r.json().catch(() => ({}));
    if (!r.ok) return json({ ok: false, why: '스토어에서 이 결제를 찾지 못했습니다. 잠시 뒤 [구매 복원]을 눌러 주세요.' }, 400);
    if (p.purchaseState === 2) return json({ ok: false, why: '결제가 아직 끝나지 않았습니다(보류 중). 결제가 끝나면 [구매 복원]을 눌러 주세요.' }, 202);
    if (p.purchaseState !== 0) return json({ ok: false, why: '취소된 결제입니다.' }, 400);
    // 결제할 때 넣은 계정 표시(obfuscatedExternalAccountId = Supabase 사용자 id)와 지금 로그인한 계정이 같아야 한다 — 남의 영수증 재사용 방지
    if (p.obfuscatedExternalAccountId && p.obfuscatedExternalAccountId !== user.id) return json({ ok: false, why: '다른 계정으로 결제한 영수증입니다.' }, 403);
    const g = await rpc('grant_purchase', { p_uid: user.id, p_token: purchaseToken, p_product: productId, p_order: p.orderId || orderId || null, p_days: days * (p.quantity || 1), p_raw: p });
    if (g && g.revoked) return json({ ok: false, why: g.why }, 400);   // 환불된 영수증을 다시 보낸 경우
    if (!g || !g.ok) return json({ ok: false, why: '이용권을 반영하지 못했습니다. 학원에 문의해 주세요.' }, 500);
    if (p.consumptionState === 0) {   // 소비 처리해야 같은 상품을 다시 살 수 있다. 실패해도 다음 복원 때 다시 시도
      await fetch(url + ':consume', { method: 'POST', headers: { Authorization: `Bearer ${at}` } }).catch(() => null);
    }
    return json({ ok: true, until: g.until, dup: !!g.dup, test: p.purchaseType === 0 });
  } catch (e) {
    console.error(e);
    return json({ ok: false, why: '결제 확인 중 오류가 났습니다. 잠시 뒤 [구매 복원]을 눌러 주세요.' }, 500);
  }
});

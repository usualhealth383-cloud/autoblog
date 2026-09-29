#!/usr/bin/env python3
"""Edge Function 시험 — verify-purchase(스토어 결제 확인)·push(푸시 알림)를 진짜 Deno 로 띄우고,
가짜 Google(OAuth 서명 검증 · Play 영수증 API · FCM 전송)과 진짜 Postgres 시험대에 붙여 끝까지 돌린다.

사용: bash tools/testbed_up.sh && python3 tools/testbed_functions.py
(Deno 는 /tmp/pcs-testbed/deno — testbed_up.sh 가 받아 둔다)
"""
import json, os, sys, time, base64, subprocess, threading, urllib.request as U, urllib.error, datetime as dt
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from zoneinfo import ZoneInfo
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FN = os.path.join(ROOT, 'app', 'server', 'functions')
W = os.environ.get('TESTBED_DIR', '/tmp/pcs-testbed'); DENO = os.path.join(W, 'deno')
GW = 'http://127.0.0.1:8767'; GPORT = 8768; PKG = 'kr.parkchan.science'
OK, BAD = [], []
def check(name, cond, info=''):
    (OK if cond else BAD).append(name); print(('  ✓ ' if cond else '  ✗ ') + name + ('' if cond else f'   ← {info}'))

# ── 가짜 Google ──
key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
PEM = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()).decode()
SA = json.dumps({'type': 'service_account', 'project_id': 'pcs-test', 'client_email': 'svc@pcs-test.iam.gserviceaccount.com', 'private_key': PEM})
PURCHASES = {}   # (productId, token) → ProductPurchase
VOIDED = []; SENT = []; SCOPES = []
def ub64(s): return base64.urlsafe_b64decode(s + '=' * (-len(s) % 4))

class G(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def out(self, code, body):
        d = json.dumps(body).encode(); self.send_response(code); self.send_header('Content-Type', 'application/json'); self.send_header('Content-Length', str(len(d))); self.end_headers(); self.wfile.write(d)
    def authed(self): return self.headers.get('Authorization', '').startswith('Bearer gtok-')
    def do_POST(self):
        n = int(self.headers.get('Content-Length') or 0); raw = self.rfile.read(n) if n else b''; p = urlparse(self.path).path
        if p == '/token':
            a = parse_qs(raw.decode())['assertion'][0]; h, c, s = a.split('.')
            try: key.public_key().verify(ub64(s), f'{h}.{c}'.encode(), padding.PKCS1v15(), hashes.SHA256())
            except Exception: return self.out(401, {'error': 'invalid_grant', 'error_description': 'bad signature'})
            claims = json.loads(ub64(c)); SCOPES.append(claims['scope'])
            return self.out(200, {'access_token': 'gtok-' + claims['scope'].rsplit('/', 1)[-1], 'expires_in': 3600})
        if not self.authed(): return self.out(401, {'error': {'status': 'UNAUTHENTICATED'}})
        if p.endswith(':consume'):
            parts = p.split('/'); pid, tok = parts[-3], parts[-1].split(':')[0]
            if (pid, tok) in PURCHASES: PURCHASES[(pid, tok)]['consumptionState'] = 1; return self.out(200, {})
            return self.out(404, {})
        if p.startswith('/v1/projects/pcs-test/messages:send'):
            m = json.loads(raw)['message']
            if m['token'].startswith('dead'): return self.out(404, {'error': {'status': 'NOT_FOUND', 'details': [{'errorCode': 'UNREGISTERED'}]}})
            SENT.append(m); return self.out(200, {'name': 'projects/pcs-test/messages/1'})
        self.out(404, {})
    def do_GET(self):
        if not self.authed(): return self.out(401, {})
        u = urlparse(self.path); parts = u.path.split('/')
        if u.path.endswith('/voidedpurchases'): return self.out(200, {'voidedPurchases': [{'purchaseToken': t} for t in VOIDED]})
        if '/purchases/products/' in u.path:
            pid, tok = parts[-3], parts[-1]
            if parts[4] != PKG: return self.out(404, {})
            return self.out(200, PURCHASES[(pid, tok)]) if (pid, tok) in PURCHASES else self.out(404, {'error': {'code': 404}})
        self.out(404, {})
_booted = {}
def boot():
    """가짜 Google + Deno 함수 둘을 띄운다. 이미 띄웠으면 그대로 돌려준다."""
    if _booted: return _booted
    threading.Thread(target=ThreadingHTTPServer(('127.0.0.1', GPORT), G).serve_forever, daemon=True).start()
    keys = json.loads(U.urlopen(GW + '/__anon').read())
    env = {**os.environ, 'DENO_NO_UPDATE_CHECK': '1', 'SUPABASE_URL': GW, 'SUPABASE_ANON_KEY': keys['anon'], 'SUPABASE_SERVICE_ROLE_KEY': keys['service'],
           'GOOGLE_OAUTH_URL': f'http://127.0.0.1:{GPORT}/token', 'GOOGLE_API_BASE': f'http://127.0.0.1:{GPORT}', 'FCM_API_BASE': f'http://127.0.0.1:{GPORT}',
           'GOOGLE_SA_JSON': SA, 'FIREBASE_SA_JSON': SA, 'ANDROID_PACKAGE': PKG, 'CRON_SECRET': 'cron-s', 'PUSH_SECRET': 'push-s', 'ACADEMY': '박찬 과학'}
    procs = []
    for name, port in (('verify-purchase', 8801), ('push', 8802)):
        procs.append(subprocess.Popen([DENO, 'run', '--allow-net', '--allow-env', os.path.join(FN, name, 'index.ts')],
                                      env={**env, 'DENO_SERVE_ADDRESS': f'tcp:127.0.0.1:{port}'}, stdout=subprocess.DEVNULL, stderr=open(os.path.join(W, f'fn-{name}.log'), 'w')))
    for _ in range(60):
        try: U.urlopen(U.Request('http://127.0.0.1:8801/', method='OPTIONS')); U.urlopen(U.Request('http://127.0.0.1:8802/', method='OPTIONS')); break
        except Exception: time.sleep(0.5)
    _booted.update(procs=procs, anon=keys['anon'], service=keys['service']); return _booted


def main_boot():
    global ANON, SERVICE, procs
    b = boot(); ANON, SERVICE, procs = b['anon'], b['service'], b['procs']
    U.urlopen(U.Request(GW + '/__reset', method='POST')).read()

def call(m, path, body=None, tok=None, headers=None):
    h = {'Content-Type': 'application/json', 'apikey': ANON, 'Authorization': 'Bearer ' + (tok or ANON), **(headers or {})}
    req = U.Request(GW + path, data=None if body is None else json.dumps(body).encode(), method=m, headers=h)
    try:
        with U.urlopen(req) as r: t = r.read(); return r.status, (json.loads(t) if t else None)
    except urllib.error.HTTPError as e:
        t = e.read()
        try: return e.code, json.loads(t)
        except Exception: return e.code, t.decode()
def signup(email, role='student'):
    s, j = call('POST', '/auth/v1/signup', {'email': email, 'password': 'pw123456', 'data': {'name': email[:2], 'role': role}}); return j['access_token'], j['user']['id']
def buy(pid, tok, uid, state=0): PURCHASES[(pid, tok)] = {'kind': 'androidpublisher#productPurchase', 'purchaseState': state, 'consumptionState': 0, 'acknowledgementState': 1, 'orderId': 'GPA.' + tok, 'obfuscatedExternalAccountId': uid, 'purchaseType': 0}
def until(tok, uid): return call('GET', f'/rest/v1/profiles?id=eq.{uid}&select=pass_until', tok=tok)[1][0]['pass_until']
VP = '/functions/v1/verify-purchase'
today = dt.datetime.now(ZoneInfo('Asia/Seoul')).date()

def main():
  main_boot()
  try:
      print('▸ 스토어 결제 확인(verify-purchase)')
      A, A_ID = signup('buyer@t.kr'); B, B_ID = signup('other@t.kr')
      buy('pass_y1', 'tokA-0000000001', A_ID)
      s, j = call('POST', VP, {'productId': 'pass_y1', 'purchaseToken': 'tokA-0000000001', 'orderId': 'x'}, A)
      exp = (today + dt.timedelta(days=365)).isoformat()
      check('정상 결제 → 1년 이용권', s == 200 and j['ok'] and j['until'] == exp and until(A, A_ID) == exp, (s, j))
      check('  └ Google 에 서비스 계정 서명으로 인증(RS256 검증 통과)', any('androidpublisher' in x for x in SCOPES))
      check('  └ 다시 살 수 있게 소비 처리', PURCHASES[('pass_y1', 'tokA-0000000001')]['consumptionState'] == 1)
      s, j = call('POST', VP, {'productId': 'pass_y1', 'purchaseToken': 'tokA-0000000001'}, A)
      check('같은 영수증 다시 보내도 한 번만 반영', s == 200 and j.get('dup') and until(A, A_ID) == exp, (s, j))
      s, j = call('POST', VP, {'productId': 'pass_y1', 'purchaseToken': 'tokA-0000000001'}, B)
      check('남의 영수증은 거절', s == 403 and until(B, B_ID) is None, (s, j))
      buy('pass_m1', 'tokB-0000000001', B_ID)
      s, j = call('POST', VP, {'productId': 'pass_y1', 'purchaseToken': 'tokB-0000000001'}, B)
      check('1개월 결제를 1년으로 속이면 거절', s == 400 and until(B, B_ID) is None, (s, j))
      s, j = call('POST', VP, {'productId': 'pass_m1', 'purchaseToken': 'tokB-0000000001'}, B)
      check('  └ 제 상품으로는 30일', s == 200 and until(B, B_ID) == (today + dt.timedelta(days=30)).isoformat(), (s, j))
      buy('pass_m6', 'tokP-0000000001', A_ID, state=2)
      s, j = call('POST', VP, {'productId': 'pass_m6', 'purchaseToken': 'tokP-0000000001'}, A)
      check('보류 중 결제는 반영 안 함(안내)', s == 202 and not j['ok'] and '보류' in j['why'] and until(A, A_ID) == exp, (s, j))
      PURCHASES[('pass_m6', 'tokP-0000000001')]['purchaseState'] = 0
      s, j = call('POST', VP, {'productId': 'pass_m6', 'purchaseToken': 'tokP-0000000001'}, A)
      exp2 = (today + dt.timedelta(days=365 + 180)).isoformat()
      check('보류가 끝난 뒤 [구매 복원] → 남은 기간 뒤로 180일', s == 200 and until(A, A_ID) == exp2, (s, j, until(A, A_ID)))
      s, j = call('POST', VP, {'productId': 'free_forever', 'purchaseToken': 'tokX-0000000001'}, A); check('모르는 상품 거절', s == 400, (s, j))
      s, j = call('POST', VP, {'productId': 'pass_y1', 'purchaseToken': 'tokA-0000000001'}); check('비로그인 거절', s == 401, (s, j))
      VOIDED.append('tokA-0000000001')
      s, j = call('POST', VP, {'action': 'voided'}, A); check('환불 정리는 cron 비밀값 없이는 못 부름', s == 403, (s, j))
      s, j = call('POST', VP, {'action': 'voided'}, headers={'x-cron-secret': 'cron-s'})
      check('환불된 1년 결제 → 그만큼 되돌림', s == 200 and j['revoked'] == 1 and until(A, A_ID) == (today + dt.timedelta(days=180)).isoformat(), (s, j, until(A, A_ID)))

      print('▸ 푸시 알림(push)')
      OWN = json.loads(U.urlopen(U.Request(GW + '/auth/v1/token?grant_type=password', data=json.dumps({'email': 'owner@parkchan.kr', 'password': 'owner-pass'}).encode(), headers={'Content-Type': 'application/json'}, method='POST')).read())['access_token']
      for code, nm, cls in (('PUSH01', '푸시학생', '월목반'), ('PUSH02', '다른반', '화금반')):
          call('POST', '/rest/v1/students', {'code': code, 'name': nm, 'cls': cls, 'until': '2099-01-01'}, OWN)
      S1, _ = signup('ps1@t.kr'); S2, _ = signup('ps2@t.kr'); P1, _ = signup('pp1@t.kr', 'parent')
      call('POST', '/rest/v1/rpc/link_code', {'p_kind': 'student', 'p_code': 'PUSH01'}, S1); call('POST', '/rest/v1/rpc/link_code', {'p_kind': 'student', 'p_code': 'PUSH02'}, S2)
      call('POST', '/rest/v1/rpc/link_code', {'p_kind': 'child', 'p_code': 'PUSH01'}, P1)
      for t, tok in ((S1, 'tok-stu1'), (S2, 'tok-stu2'), (P1, 'tok-par1')): call('POST', '/rest/v1/rpc/register_push', {'p_token': tok, 'p_platform': 'android'}, t)
      call('POST', '/rest/v1/rpc/register_push', {'p_token': 'dead-old-phone', 'p_platform': 'android'}, P1)
      PH = {'x-push-secret': 'push-s'}
      s, j = call('POST', '/functions/v1/push', {'type': 'INSERT', 'table': 'notices', 'record': {'cls': '월목반', 'title': '휴강', 'body': '태풍'}})
      check('웹훅 비밀값 없으면 거절', s == 403, (s, j))
      SENT.clear(); s, j = call('POST', '/functions/v1/push', {'type': 'INSERT', 'table': 'notices', 'record': {'cls': '월목반', 'title': '휴강 안내', 'body': '태풍으로 휴강'}}, headers=PH)
      to = sorted(m['token'] for m in SENT)
      check('월목반 공지 → 그 반 학생·보호자에게만', s == 200 and to == ['tok-par1', 'tok-stu1'], (s, j, to))
      check('  └ 제목·채널·우선순위', SENT and SENT[0]['notification']['title'] == '[박찬 과학] 휴강 안내' and SENT[0]['android']['notification']['channel_id'] == 'academy' and SENT[0]['android']['priority'] == 'HIGH', SENT[:1])
      check('  └ 없어진 기기 토큰은 지움', j.get('dropped') == 1 and call('GET', '/rest/v1/push_tokens?token=eq.dead-old-phone&select=token', tok=P1)[1] == [], j)
      SENT.clear(); call('POST', '/functions/v1/push', {'type': 'INSERT', 'table': 'notices', 'record': {'cls': '전체', 'title': '전체 공지', 'body': ''}}, headers=PH)
      check('전체 공지 → 모든 반', sorted(m['token'] for m in SENT) == ['tok-par1', 'tok-stu1', 'tok-stu2'], [m['token'] for m in SENT])
      SENT.clear(); call('POST', '/functions/v1/push', {'type': 'INSERT', 'table': 'sched', 'record': {'cls': '화금반', 'date': '2026-10-15', 'title': '단원 평가', 'memo': '3단원'}}, headers=PH)
      check('반 일정 → 그 반만 · "10/15 단원 평가"', [m['token'] for m in SENT] == ['tok-stu2'] and '10/15 단원 평가' in SENT[0]['notification']['title'], SENT)
      SENT.clear(); call('POST', '/functions/v1/push', {'type': 'INSERT', 'table': 'attendance', 'record': {'code': 'PUSH01', 'time': '18:02:11', 'late': True, 'manual': False}}, headers=PH)
      check('출석 → 보호자에게만 "푸시학생 학생 지각 · 18:02"', [m['token'] for m in SENT] == ['tok-par1'] and '푸시학생 학생 지각' in SENT[0]['notification']['title'] and '18:02' in SENT[0]['notification']['body'], SENT)
      check('  └ Firebase 범위로 따로 인증', any('firebase.messaging' in x for x in SCOPES))
  finally:
      for p in procs: p.terminate()

  print(f'\nEdge Function 시험 {len(OK)}/{len(OK) + len(BAD)} 통과')
  sys.exit(1 if BAD else 0)

if __name__ == '__main__': main()

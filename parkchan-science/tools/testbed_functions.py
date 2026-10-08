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
def signup(email, role='student', **meta):
    s, j = call('POST', '/auth/v1/signup', {'email': email, 'password': 'pw123456', 'data': {'name': email[:2], 'role': role, **meta}}); return j['access_token'], j['user']['id']
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

      s, j = call('POST', VP, {'productId': 'pass_y1', 'purchaseToken': 'tokA-0000000001'}, A)
      check('환불된 영수증을 다시 보내도 다시 열리지 않음', s == 400 and '환불' in j.get('why', '') and until(A, A_ID) == (today + dt.timedelta(days=180)).isoformat(), (s, j, until(A, A_ID)))
      K, K_ID = signup('kidbuy@t.kr', under14=True, guardian='김보호 01011112222')
      buy('pass_m1', 'tokK-0000000001', K_ID)
      s, j = call('POST', VP, {'productId': 'pass_m1', 'purchaseToken': 'tokK-0000000001'}, K)
      check('보호자 동의 전 14세 미만 결제는 반영 안 함', s == 403 and until(K, K_ID) is None, (s, j))
      check('  └ 소비하지 않아 마켓이 자동 환불(3일 미확인)', PURCHASES[('pass_m1', 'tokK-0000000001')]['consumptionState'] == 0)
      print('▸ 푸시 알림(push)')
      OWN = json.loads(U.urlopen(U.Request(GW + '/auth/v1/token?grant_type=password', data=json.dumps({'email': 'owner@parkchan.kr', 'password': 'owner-pass'}).encode(), headers={'Content-Type': 'application/json'}, method='POST')).read())['access_token']
      for code, nm, cls in (('PUSH01', '푸시학생', '월목반'), ('PUSH02', '다른반', '화금반')):
          call('POST', '/rest/v1/students', {'code': code, 'name': nm, 'cls': cls, 'until': '2099-01-01'}, OWN)
      S1, _ = signup('ps1@t.kr'); S2, _ = signup('ps2@t.kr'); P1, P1_ID = signup('pp1@t.kr', 'parent')
      call('POST', '/rest/v1/rpc/link_code', {'p_kind': 'student', 'p_code': 'PUSH01'}, S1); call('POST', '/rest/v1/rpc/link_code', {'p_kind': 'student', 'p_code': 'PUSH02'}, S2)
      call('POST', '/rest/v1/rpc/link_code', {'p_kind': 'child', 'p_code': 'PUSH01'}, P1)
      call('POST', '/rest/v1/rpc/guardian_decide', {'p_uid': P1_ID, 'p_code': 'PUSH01', 'p_ok': True}, OWN)   # 보호자 연결은 원장 확인 뒤
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
      # 이야기 댓글 → 글쓴이에게만(자기 댓글은 알리지 않음)
      import psycopg2 as _pg; _c = _pg.connect('host=127.0.0.1 port=54329 user=postgres dbname=pcs'); _c.autocommit = True
      _c.cursor().execute("update profiles set first_ok_at = now() where role = 'student'"); _c.close()   # 첫 글 검토를 지난 학생으로(검토는 testbed_security 에서)
      pid = call('POST', '/rest/v1/posts?select=id', {'board': 'qna', 'title': '충격량 질문', 'body': '넓이가 왜 충격량인가요'}, S1, headers={'Prefer': 'return=representation'})[1][0]['id']
      DAY = '2026-10-01T15:00:00+09:00'   # 낮(한국 시각) — 밤 22~07시 댓글 알림은 아침으로 미룬다(아래)
      SENT.clear(); call('POST', '/functions/v1/push', {'type': 'INSERT', 'table': 'comments', 'record': {'post_id': pid, 'author': 'someone-else', 'body': '힘-시간 그래프의 넓이는 F×Δt 입니다', 'staff': True, 'at': DAY}}, headers=PH)
      check('댓글 → 글쓴이 폰에만 · "선생님이 답을 달았어요"', [m['token'] for m in SENT] == ['tok-stu1'] and '선생님이 답을' in SENT[0]['notification']['title'] and SENT[0]['data'].get('post') == pid, SENT)
      blob = json.dumps(SENT[:1], ensure_ascii=False)
      check('  └ 잠금화면에 댓글 내용·글 제목을 싣지 않음("새 댓글이 있어요")', SENT and '새 댓글이 있어요' in SENT[0]['notification']['body'] and 'F×Δt' not in blob and '충격량 질문' not in blob, SENT[:1])
      check('  └ 안드로이드 잠금화면 공개 범위 PRIVATE', SENT and SENT[0]['android']['notification'].get('visibility') == 'PRIVATE', SENT[:1])
      s1_uid = call('GET', '/auth/v1/user', tok=S1)[1]['id']
      SENT.clear(); call('POST', '/functions/v1/push', {'type': 'INSERT', 'table': 'comments', 'record': {'post_id': pid, 'author': s1_uid, 'body': '고맙습니다', 'at': DAY}}, headers=PH)
      check('  └ 자기 글에 자기가 단 댓글은 알리지 않음', SENT == [], SENT)
      # 도움이 필요해 보이는 글·댓글 → 원장 폰에만, 잠금화면에 내용은 싣지 않는다
      call('POST', '/rest/v1/rpc/register_push', {'p_token': 'tok-own', 'p_platform': 'android'}, OWN)
      SENT.clear(); call('POST', '/functions/v1/push', {'type': 'INSERT', 'table': 'posts', 'record': {'id': pid, 'author': s1_uid, 'title': '요즘 지쳐요', 'body': '그만 살고 싶어요', 'care': True}}, headers=PH)
      check('힘든 마음의 글 → 원장 폰에만 "먼저 살펴볼 글"', [m['token'] for m in SENT] == ['tok-own'] and '먼저 살펴볼 글' in SENT[0]['notification']['title'] and SENT[0]['data'].get('kind') == 'care', SENT)
      check('  └ 알림에 글 내용은 싣지 않음', SENT and '살고 싶' not in json.dumps(SENT[0], ensure_ascii=False) and '지쳐요' not in json.dumps(SENT[0], ensure_ascii=False), SENT[:1])
      SENT.clear(); call('POST', '/functions/v1/push', {'type': 'INSERT', 'table': 'posts', 'record': {'id': pid, 'author': s1_uid, 'title': '질문', 'body': '충격량', 'care': False}}, headers=PH)
      check('  └ 보통 글은 원장에게 알리지 않음', SENT == [], SENT)
      SENT.clear(); call('POST', '/functions/v1/push', {'type': 'INSERT', 'table': 'comments', 'record': {'post_id': pid, 'author': 'someone-else', 'body': '자해하고 싶어', 'care': True, 'at': DAY}}, headers=PH)
      check('힘든 마음의 댓글 → 원장 + 글쓴이(보통 댓글 알림)', sorted(m['token'] for m in SENT) == ['tok-own', 'tok-stu1'], [m['token'] for m in SENT])
      check('  └ 글쓴이 폰 알림에도 댓글 내용은 싣지 않음', all('자해' not in json.dumps(m, ensure_ascii=False) for m in SENT), SENT)
      print('▸ 밤 22시~아침 7시 — 학생 댓글 알림은 아침으로 · 원장 위기 알림은 바로')
      import psycopg2; db = psycopg2.connect('host=127.0.0.1 port=54329 user=postgres dbname=pcs'); db.autocommit = True; cur = db.cursor()
      cur.execute('delete from push_later')
      for at, body in (('2026-10-01T23:30:00+09:00', '밤 댓글 하나'), ('2026-10-02T05:10:00+09:00', '새벽 댓글 둘'), ('2026-10-01T22:00:00+09:00', '딱 22시')):
          SENT.clear(); call('POST', '/functions/v1/push', {'type': 'INSERT', 'table': 'comments', 'record': {'post_id': pid, 'author': 'someone-else', 'body': body, 'at': at}}, headers=PH)
          if SENT: break
      check('밤(22:00·23:30·05:10)에 달린 댓글은 바로 보내지 않음', SENT == [], SENT)
      cur.execute('select count(*) from push_later where uid = %s', (s1_uid,)); check('  └ 아침에 보낼 것으로 모아 둠(3건)', cur.fetchone()[0] == 3)
      SENT.clear(); call('POST', '/functions/v1/push', {'type': 'INSERT', 'table': 'comments', 'record': {'post_id': pid, 'author': 'someone-else', 'body': '아침 7시 댓글', 'at': '2026-10-02T07:00:00+09:00'}}, headers=PH)
      check('  └ 아침 7시부터는 다시 바로 보냄', [m['token'] for m in SENT] == ['tok-stu1'], SENT)
      SENT.clear(); call('POST', '/functions/v1/push', {'type': 'INSERT', 'table': 'comments', 'record': {'post_id': pid, 'author': 'someone-else', 'body': '죽고 싶어', 'care': True, 'at': '2026-10-01T23:50:00+09:00'}}, headers=PH)
      check('밤에도 원장 "먼저 살펴볼 글" 알림은 바로(학생 댓글 알림만 미룸)', [m['token'] for m in SENT] == ['tok-own'] and SENT[0]['data']['kind'] == 'care', [m['token'] for m in SENT])
      s, j = call('POST', '/functions/v1/push', {'action': 'morning'}); check('아침 알림도 웹훅 비밀값 없으면 거절', s == 403, (s, j))
      SENT.clear(); s, j = call('POST', '/functions/v1/push', {'action': 'morning'}, headers=PH)
      check('아침 7시 → 밤사이 댓글을 사람마다 한 번 "새 댓글 4개"', s == 200 and [m['token'] for m in SENT] == ['tok-stu1'] and '밤사이' in SENT[0]['notification']['title'] and '4개' in SENT[0]['notification']['body'], (s, j, SENT))
      check('  └ 아침 알림에도 댓글 내용 없음', SENT and all(w not in json.dumps(SENT[0], ensure_ascii=False) for w in ('밤 댓글', '새벽 댓글', '죽고')), SENT[:1])
      cur.execute('select count(*) from push_later'); check('  └ 보낸 뒤 모아 둔 것은 지움', cur.fetchone()[0] == 0)
      SENT.clear(); s, j = call('POST', '/functions/v1/push', {'action': 'morning'}, headers=PH); check('  └ 다시 불러도 두 번 보내지 않음', SENT == [] and j.get('sent') == 0, (j, SENT))
      print("▸ '친구가 걱정돼요' 신고 → 원장 폰")
      SENT.clear(); call('POST', '/functions/v1/push', {'type': 'INSERT', 'table': 'reports', 'record': {'id': 1, 'post_id': pid, 'comment_id': None, 'uid': 'x', 'reason': 'worry'}}, headers=PH)
      check('걱정돼요 신고 1건 → 원장 폰에만 "먼저 살펴볼 글"', [m['token'] for m in SENT] == ['tok-own'] and '걱정' in SENT[0]['notification']['body'] and SENT[0]['data'].get('post') == pid, SENT)
      cid = call('POST', '/rest/v1/comments?select=id', {'post_id': pid, 'body': '댓글 하나'}, S2, headers={'Prefer': 'return=representation'})[1][0]['id']
      SENT.clear(); call('POST', '/functions/v1/push', {'type': 'INSERT', 'table': 'reports', 'record': {'id': 2, 'post_id': None, 'comment_id': cid, 'uid': 'x', 'reason': 'worry'}}, headers=PH)
      check('  └ 댓글에 대한 걱정돼요도 그 글로 이어짐', [m['data'].get('post') for m in SENT] == [pid], SENT)
      SENT.clear(); call('POST', '/functions/v1/push', {'type': 'INSERT', 'table': 'reports', 'record': {'id': 3, 'post_id': pid, 'comment_id': None, 'uid': 'x', 'reason': 'bully'}}, headers=PH)
      check('  └ 다른 사유의 신고는 원장 폰에 알리지 않음(매일 목록으로)', SENT == [], SENT)
      print('▸ 보호자 주간 요약(★5) — 일요일 저녁 · 확인된 보호자에게 자녀마다 한 줄 · 밤에는 보내지 않음')
      mon = today - dt.timedelta(days=today.isoweekday() - 1); D = lambda n: (mon + dt.timedelta(days=n)).isoformat()
      cur.execute("insert into progress(code, state) values ('PUSH01', %s) on conflict (code) do update set state = excluded.state",
                  (json.dumps({'days': [D(-1), D(0), D(1)], 'dq': {D(-1): [9, 9], D(0): [6, 5], D(1): [4, 2]}}),))
      aid = call('POST', '/rest/v1/rpc/assign_create', {'p_kind': 'bank', 'p_title': '1-01 문제', 'p_ref': '1101', 'p_items': ['1101-q1', '1101-q2'], 'p_cls': '월목반', 'p_codes': None, 'p_due': D(6)}, OWN)[1]['id']
      call('POST', '/rest/v1/rpc/assign_save', {'p_id': aid, 'p_done': 2, 'p_right': 2, 'p_secs': 50, 'p_wrong': [], 'p_submit': True}, S1)
      call('POST', '/rest/v1/rpc/link_code', {'p_kind': 'child', 'p_code': 'PUSH02'}, P1); call('POST', '/rest/v1/rpc/guardian_decide', {'p_uid': P1_ID, 'p_code': 'PUSH02', 'p_ok': True}, OWN)
      P2, P2_ID = signup('pp2@t.kr', 'parent'); call('POST', '/rest/v1/rpc/link_code', {'p_kind': 'child', 'p_code': 'PUSH01'}, P2)   # 원장 확인 전
      call('POST', '/rest/v1/rpc/register_push', {'p_token': 'tok-par2', 'p_platform': 'android'}, P2)
      SUN = (mon + dt.timedelta(days=6)).isoformat()
      s, j = call('POST', '/functions/v1/push', {'action': 'weekly', 'at': SUN + 'T19:00:00+09:00'}); check('주간 요약도 웹훅 비밀값 없으면 거절', s == 403, (s, j))
      SENT.clear(); s, j = call('POST', '/functions/v1/push', {'action': 'weekly', 'at': SUN + 'T19:00:00+09:00'}, headers=PH)
      to = sorted((m['token'], m['data'].get('code')) for m in SENT)
      check('일요일 19시 → 확인된 보호자에게만, 자녀마다 한 번(학생·확인 전 보호자는 안 받음)', s == 200 and to == [('tok-par1', 'PUSH01'), ('tok-par1', 'PUSH02')], (s, j, to))
      m1 = next((m for m in SENT if m['data'].get('code') == 'PUSH01'), {}); m2 = next((m for m in SENT if m['data'].get('code') == 'PUSH02'), {})
      check('  └ "푸시학생 학생의 이번 주" · 공부한 날 2일 · 푼 문제 10개 · 과제 1/1 제출(지난주 것은 세지 않음)', m1 and '푸시학생 학생의 이번 주' in m1['notification']['title']
            and '공부한 날 2일' in m1['notification']['body'] and '푼 문제 10개' in m1['notification']['body'] and '과제 1/1 제출' in m1['notification']['body'], m1)
      check('  └ 공부 기록이 없는 주는 탓하지 않는 말("쉬어 갔어요")', m2 and '쉬어 갔어요' in m2['notification']['body'] and all(w not in json.dumps(SENT, ensure_ascii=False) for w in ('안 했', '못 했', '순위', '평균', '친구')), m2)
      check('  └ 자녀별로 따로 남음(tag) · 잠금화면 공개 범위 PRIVATE · kind weekly', m1 and m2 and m1['android']['notification']['tag'] != m2['android']['notification']['tag']
            and m1['android']['notification'].get('visibility') == 'PRIVATE' and m1['data']['kind'] == 'weekly', SENT)
      for at in (SUN + 'T22:00:00+09:00', SUN + 'T23:30:00+09:00', SUN + 'T06:59:00+09:00'):
          SENT.clear(); s, j = call('POST', '/functions/v1/push', {'action': 'weekly', 'at': at}, headers=PH)
          if SENT: break
      check('밤 22시~아침 7시에 불리면 보내지 않음', SENT == [] and j.get('skipped') == 'night', (j, SENT))
      cur.execute("update guardian_links set approved = false where uid = %s and code = 'PUSH02'", (P1_ID,))
      SENT.clear(); call('POST', '/functions/v1/push', {'action': 'weekly', 'at': SUN + 'T19:00:00+09:00'}, headers=PH)
      check('  └ 확인이 풀린 자녀는 빠짐', sorted(m['data'].get('code') for m in SENT) == ['PUSH01'], [m['data'] for m in SENT])
      s, _ = call('PATCH', f'/rest/v1/profiles?id=eq.{P1_ID}', {'weekly_off': True}, P1, headers={'Prefer': 'return=minimal'}); check('보호자가 주간 요약 알림을 직접 끔(2026-10-07)', s in (200, 204), s)
      SENT.clear(); call('POST', '/functions/v1/push', {'action': 'weekly', 'at': SUN + 'T19:00:00+09:00'}, headers=PH)
      check('  └ 끈 보호자에게는 주간 요약이 가지 않음', not [m for m in SENT if m['token'] == 'tok-par1'], SENT)
      call('PATCH', f'/rest/v1/profiles?id=eq.{P1_ID}', {'weekly_off': False}, P1, headers={'Prefer': 'return=minimal'})
      print('▸ 과제 알림(2026-10-07) — 새 과제 → 받는 학생 폰 · 마감 전날 저녁 → 아직 안 낸 학생 · 밤에는 보내지 않음')
      TOM = (today + dt.timedelta(days=1)).isoformat()
      r = call('POST', '/rest/v1/rpc/assign_create', {'p_kind': 'bank', 'p_title': '알림 시험 과제', 'p_ref': '1101', 'p_items': ['1101-q1'], 'p_cls': '월목반', 'p_codes': None, 'p_due': TOM}, OWN)[1]; aid2 = r['id']
      rec = {'id': aid2, 'title': '알림 시험 과제', 'due': TOM}
      s, j = call('POST', '/functions/v1/push', {'type': 'INSERT', 'table': 'assignments', 'record': {**rec, 'at': today.isoformat() + 'T15:00:00+09:00'}}); check('과제 알림도 웹훅 비밀값 없으면 거절', s == 403, (s, j))
      SENT.clear(); call('POST', '/functions/v1/push', {'type': 'INSERT', 'table': 'assignments', 'record': {**rec, 'at': today.isoformat() + 'T15:00:00+09:00'}}, headers=PH)
      check('새 과제 → 받는 반 학생 폰에만(다른 반 학생·보호자·원장은 안 받음)', [m['token'] for m in SENT] == ['tok-stu1'] and SENT[0]['data']['kind'] == 'asg' and '새 과제 · 알림 시험 과제' in SENT[0]['notification']['title'], SENT)
      SENT.clear(); call('POST', '/functions/v1/push', {'type': 'INSERT', 'table': 'assignments', 'record': {**rec, 'at': today.isoformat() + 'T23:10:00+09:00'}}, headers=PH)
      check('  └ 밤 23시에 낸 과제는 알리지 않음(아침에 오늘 화면 카드로)', SENT == [], SENT)
      SENT.clear(); s, j = call('POST', '/functions/v1/push', {'action': 'asgdue', 'at': today.isoformat() + 'T19:00:00+09:00'}, headers=PH)
      due1 = [m for m in SENT if m['token'] == 'tok-stu1']
      check('저녁 7시 → 내일 마감인데 아직 안 낸 학생에게 한 번("내일 마감인 과제")', s == 200 and len(due1) == 1 and '내일 마감' in due1[0]['notification']['title'] and '알림 시험 과제' in due1[0]['notification']['body']
            and all(m['token'] not in ('tok-par1', 'tok-own', 'tok-stu2') for m in SENT), (s, j, SENT))
      call('POST', '/rest/v1/rpc/assign_save', {'p_id': aid2, 'p_done': 1, 'p_right': 1, 'p_secs': 20, 'p_wrong': [], 'p_submit': True}, S1)
      SENT.clear(); call('POST', '/functions/v1/push', {'action': 'asgdue', 'at': today.isoformat() + 'T19:00:00+09:00'}, headers=PH)
      check('  └ 내고 나면 마감 전날 알림이 오지 않음', not [m for m in SENT if m['token'] == 'tok-stu1'], SENT)
      SENT.clear(); s, j = call('POST', '/functions/v1/push', {'action': 'asgdue', 'at': today.isoformat() + 'T22:30:00+09:00'}, headers=PH)
      check('  └ 밤에 불리면 보내지 않음', SENT == [] and j.get('skipped') == 'night', (j, SENT))
  finally:
      for p in procs: p.terminate()

  print(f'\nEdge Function 시험 {len(OK)}/{len(OK) + len(BAD)} 통과')
  sys.exit(1 if BAD else 0)

if __name__ == '__main__': main()

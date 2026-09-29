#!/usr/bin/env python3
"""로컬 시험대 — 진짜 PostgreSQL + 진짜 PostgREST 위에 Supabase Auth 흉내를 얹어, 앱이 실제 프로젝트와 똑같이 붙게 한다.

파이썬으로 규칙을 흉내 내던 예전 모의 서버와 달리, 이 시험대는 schema.sql 의 RLS·권한·트리거를 그대로 돌린다.
보안 규칙이 실제로 막히는지·앱이 그 규칙 안에서 끝까지 도는지는 여기서 확인한다.

준비(한 번):  tools/testbed_up.sh   — Postgres(54329)·PostgREST(3001)·이 게이트웨이(8767)를 띄운다
주소:         http://127.0.0.1:8767   (앱에는 ?server=http://127.0.0.1:8767&key=<ANON> 으로 붙인다)
시험용:       POST /__reset (표 비우고 원장 계정 다시 만들기) · GET /__mail (보낸 메일 링크) · GET /__anon (anon 키)
              GET /__autoconfirm?on=0 (운영처럼 메일 인증 요구) · on=1 (바로 가입)
원장:         owner@parkchan.kr / owner-pass  (메일 인증된 상태)
"""
import json, os, sys, time, uuid, secrets, hmac, hashlib, base64
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs, urlencode
import urllib.request, urllib.error
import psycopg2

PORT = int(os.environ.get('GW_PORT', 8767))
PGRST = os.environ.get('PGRST_URL', 'http://127.0.0.1:3001')
DSN = os.environ.get('PG_DSN', 'host=127.0.0.1 port=54329 user=postgres dbname=pcs')
SECRET = os.environ.get('JWT_SECRET', 'testbed-secret-that-is-at-least-32-chars-long')
AUTOCONFIRM = os.environ.get('AUTOCONFIRM', '1') == '1'
OWNER = ('owner@parkchan.kr', 'owner-pass')
SITE = os.environ.get('SITE_URL', 'http://127.0.0.1:8765/index.html')
MAIL = []            # 보낸 메일(링크) — 시험에서 꺼내 쓴다
REFRESH = {}         # refresh_token → user id
OTP = {}             # 메일 링크 토큰 → (user id, 종류)


def b64(b): return base64.urlsafe_b64encode(b).rstrip(b'=').decode()
def jwt(claims):
    h = b64(json.dumps({'alg': 'HS256', 'typ': 'JWT'}).encode()); p = b64(json.dumps(claims).encode())
    s = b64(hmac.new(SECRET.encode(), f'{h}.{p}'.encode(), hashlib.sha256).digest()); return f'{h}.{p}.{s}'
def unjwt(t):
    try:
        h, p, s = t.split('.')
        if not hmac.compare_digest(s, b64(hmac.new(SECRET.encode(), f'{h}.{p}'.encode(), hashlib.sha256).digest())): return None
        c = json.loads(base64.urlsafe_b64decode(p + '=' * (-len(p) % 4)))
        return c if c.get('exp', 0) > time.time() else None
    except Exception: return None
ANON = jwt({'role': 'anon', 'iss': 'testbed', 'exp': int(time.time()) + 10 * 365 * 86400})
SERVICE = jwt({'role': 'service_role', 'iss': 'testbed', 'exp': int(time.time()) + 10 * 365 * 86400})


def db():
    c = psycopg2.connect(DSN); c.autocommit = True; return c
def q(sql, *a):
    with db() as c, c.cursor() as cur:
        cur.execute(sql, a)
        try: return cur.fetchall()
        except psycopg2.ProgrammingError: return []
def pwhash(pw): return hashlib.sha256(('pcs:' + pw).encode()).hexdigest()


def session(uid, email):
    rt = secrets.token_urlsafe(24); REFRESH[rt] = uid
    at = jwt({'sub': uid, 'email': email, 'role': 'authenticated', 'aud': 'authenticated', 'exp': int(time.time()) + 3600})
    return {'access_token': at, 'token_type': 'bearer', 'expires_in': 3600, 'refresh_token': rt,
            'user': {'id': uid, 'email': email, 'user_metadata': (q('select raw_user_meta_data from auth.users where id=%s', uid) or [[{}]])[0][0]}}


def reset():
    q("""truncate auth.users, students, attendance, notices, notice_reads, sched, progress, passes, purchases,
         posts, comments, push_tokens, client_errors, guardian_links, profiles cascade""")
    q("delete from private.attempts"); q("delete from classes")
    q("insert into classes values ('월목반','18:00'),('화금반','18:00'),('수토반','14:00')")
    q("insert into private.config values ('owner_email', %s) on conflict (k) do update set v = excluded.v", OWNER[0])
    q("insert into private.config values ('attend_secret', 'testbed-attend') on conflict (k) do update set v = excluded.v")
    q("insert into auth.users(email, encrypted_password, email_confirmed_at, raw_user_meta_data) values (%s, %s, now(), %s)",
      OWNER[0], pwhash(OWNER[1]), json.dumps({'name': '원장'}))
    q("update profiles set name = '원장' where role = 'owner'")
    MAIL.clear(); REFRESH.clear(); OTP.clear()


def mail(uid, email, kind, redirect):
    tok = secrets.token_urlsafe(16); OTP[tok] = (uid, kind)
    link = f'http://127.0.0.1:{PORT}/auth/v1/verify?' + urlencode({'token': tok, 'type': kind, 'redirect_to': redirect or SITE})
    MAIL.append({'to': email, 'type': kind, 'link': link})


class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET,POST,PATCH,PUT,DELETE,OPTIONS')
        self.send_header('Access-Control-Expose-Headers', 'Content-Range')
    def out(self, code, body=None, headers=None):
        self.send_response(code); self.cors()
        for k, v in (headers or {}).items(): self.send_header(k, v)
        data = b'' if body is None else (body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode())
        if body is not None and not (headers or {}).get('Content-Type'): self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data))); self.end_headers(); self.wfile.write(data)
    def body(self):
        n = int(self.headers.get('Content-Length') or 0); return self.rfile.read(n) if n else b''
    def do_OPTIONS(self): self.out(204)
    def do_GET(self): self.route('GET')
    def do_POST(self): self.route('POST')
    def do_PATCH(self): self.route('PATCH')
    def do_PUT(self): self.route('PUT')
    def do_DELETE(self): self.route('DELETE')

    def user(self):
        a = (self.headers.get('Authorization') or '').replace('Bearer ', '')
        c = unjwt(a); return c if c and c.get('role') == 'authenticated' else None

    def route(self, m):
        u = urlparse(self.path); qs = parse_qs(u.query); raw = self.body()
        try: j = json.loads(raw) if raw else {}
        except Exception: j = {}
        if u.path == '/__reset': reset(); return self.out(200, {'ok': True})
        if u.path == '/__mail': return self.out(200, MAIL)
        if u.path == '/__autoconfirm':            # 운영처럼 메일 인증을 요구하려면 ?on=0
            global AUTOCONFIRM; AUTOCONFIRM = qs.get('on', ['1'])[0] == '1'; return self.out(200, {'autoconfirm': AUTOCONFIRM})
        if u.path == '/__anon': return self.out(200, {'anon': ANON, 'service': SERVICE})
        if u.path.startswith('/rest/v1/'): return self.proxy(m, u, raw)
        if u.path.startswith('/auth/v1/'): return self.auth(m, u.path[9:], qs, j)
        if u.path.startswith('/functions/v1/'): return self.fn(m, u.path[14:], raw)
        self.out(404, {'message': 'not found'})

    def proxy(self, m, u, raw):
        url = PGRST + u.path[8:] + (('?' + u.query) if u.query else '')
        h = {k: v for k, v in self.headers.items() if k.lower() in ('authorization', 'content-type', 'prefer', 'accept', 'range', 'x-student-code')}
        if not h.get('Authorization') and not h.get('authorization'): h['Authorization'] = 'Bearer ' + ANON
        req = urllib.request.Request(url, data=raw if m in ('POST', 'PATCH', 'PUT', 'DELETE') and raw else None, method=m, headers=h)
        try:
            with urllib.request.urlopen(req) as r: code, data, ct = r.status, r.read(), r.headers.get('Content-Type', 'application/json')
        except urllib.error.HTTPError as e: code, data, ct = e.code, e.read(), e.headers.get('Content-Type', 'application/json')
        self.out(code, data, {'Content-Type': ct})

    def auth(self, m, p, qs, j):
        if p == 'signup':
            em = (j.get('email') or '').strip().lower(); pw = j.get('password') or ''
            if len(pw) < 6: return self.out(422, {'msg': 'Password should be at least 6 characters'})
            if q('select 1 from auth.users where email=%s', em): return self.out(422, {'msg': 'User already registered'})
            uid = q("insert into auth.users(email, encrypted_password, email_confirmed_at, raw_user_meta_data) values (%s,%s,%s,%s) returning id::text",
                    em, pwhash(pw), 'now()' if AUTOCONFIRM else None, json.dumps(j.get('data') or {}))[0][0]
            if AUTOCONFIRM: return self.out(200, session(uid, em))
            mail(uid, em, 'signup', (j.get('options') or {}).get('emailRedirectTo') or qs.get('redirect_to', [''])[0])
            return self.out(200, {'id': uid, 'email': em, 'user_metadata': j.get('data') or {}})
        if p == 'token':
            g = qs.get('grant_type', [''])[0]
            if g == 'password':
                r = q('select id::text, email, encrypted_password, email_confirmed_at from auth.users where email=%s', (j.get('email') or '').strip().lower())
                if not r or r[0][2] != pwhash(j.get('password') or ''): return self.out(400, {'error': 'invalid_grant', 'error_description': 'Invalid login credentials'})
                if r[0][3] is None: return self.out(400, {'error': 'invalid_grant', 'error_description': 'Email not confirmed'})
                return self.out(200, session(r[0][0], r[0][1]))
            if g == 'refresh_token':
                uid = REFRESH.pop(j.get('refresh_token') or '', None)
                r = uid and q('select email from auth.users where id=%s', uid)
                if not r: return self.out(400, {'error': 'invalid_grant', 'error_description': 'Invalid Refresh Token'})
                return self.out(200, session(uid, r[0][0]))
        if p == 'logout': return self.out(204)
        if p == 'recover':
            em = (j.get('email') or '').strip().lower(); r = q('select id::text from auth.users where email=%s', em)
            if r: mail(r[0][0], em, 'recovery', qs.get('redirect_to', [''])[0])
            return self.out(200, {})
        if p == 'verify':
            tok = qs.get('token', [''])[0]; kind = qs.get('type', [''])[0]; to = qs.get('redirect_to', [SITE])[0]
            if tok not in OTP: return self.out(303, None, {'Location': to + '#error=access_denied&error_description=' + 'Email+link+is+invalid+or+has+expired'})
            uid, k = OTP.pop(tok)
            q('update auth.users set email_confirmed_at = coalesce(email_confirmed_at, now()) where id=%s', uid)
            s = session(uid, q('select email from auth.users where id=%s', uid)[0][0])
            return self.out(303, None, {'Location': to + '#' + urlencode({'access_token': s['access_token'], 'refresh_token': s['refresh_token'], 'expires_in': 3600, 'token_type': 'bearer', 'type': k})})
        if p == 'user':
            c = self.user()
            if not c: return self.out(401, {'msg': 'Invalid JWT'})
            if m == 'PUT' and j.get('password'):
                if len(j['password']) < 6: return self.out(422, {'msg': 'Password should be at least 6 characters'})
                q('update auth.users set encrypted_password=%s where id=%s', pwhash(j['password']), c['sub'])
            r = q('select id::text, email, raw_user_meta_data from auth.users where id=%s', c['sub'])
            return self.out(200, {'id': r[0][0], 'email': r[0][1], 'user_metadata': r[0][2]})
        self.out(404, {'msg': 'unknown auth path ' + p})

    def fn(self, m, name, raw):
        # 로컬에서 띄운 Edge Function(Deno)으로 넘긴다 — FN_PORTS='verify-purchase=8801,push=8802'
        ports = dict(x.split('=') for x in os.environ.get('FN_PORTS', 'verify-purchase=8801,push=8802').split(','))
        if name not in ports: return self.out(404, {'message': 'function not deployed in testbed: ' + name})
        h = {k: v for k, v in self.headers.items() if k.lower() in ('authorization', 'content-type', 'apikey', 'x-cron-secret', 'x-push-secret')}
        req = urllib.request.Request(f'http://127.0.0.1:{ports[name]}/', data=raw or None, method=m, headers=h)
        try:
            with urllib.request.urlopen(req, timeout=30) as r: code, data = r.status, r.read()
        except urllib.error.HTTPError as e: code, data = e.code, e.read()
        except Exception as e: code, data = 502, json.dumps({'message': f'function {name} not running: {e}'}).encode()
        self.out(code, data, {'Content-Type': 'application/json'})


if __name__ == '__main__':
    reset()
    print(f'testbed gateway :{PORT} → PostgREST {PGRST} · anon={ANON[:16]}…', flush=True)
    ThreadingHTTPServer(('127.0.0.1', PORT), H).serve_forever()

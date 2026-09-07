#!/usr/bin/env python3
"""Supabase 흉내 서버 — 앱의 서버 어댑터를 실제 계정 없이 끝까지 시험하기 위한 것.

PostgREST(REST) 의 부분집합과 Auth(비밀번호 로그인)·RPC 3개를 메모리 안에서 흉내 낸다.
schema.sql 의 RLS 와 같은 규칙을 적용한다: 원장 토큰이면 전부, 학생(x-student-code)이면 자기 것만.

사용: python3 app/server/mock_server.py [포트=8766]
  원장 계정  owner@parkchan.kr / owner-pass
  anon 키    anon
  출석 씨앗  mock-secret (current_attend_code 로 원장 화면이 받아 간다)
"""
import json, sys, time, hashlib, uuid, datetime as dt
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs, unquote

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8766
OWNER_EMAIL, OWNER_PW, ANON, SECRET = 'owner@parkchan.kr', 'owner-pass', 'anon', 'mock-secret'
CLASS_START = {'월목반': '18:00', '화금반': '18:00', '수토반': '14:00'}
DB = {'students': [], 'attendance': [], 'notices': [], 'notice_reads': [], 'progress': []}
TOKENS = {}   # access_token → email
PK = {'students': ['code'], 'attendance': ['code', 'date'], 'notices': ['id'], 'notice_reads': ['notice_id', 'code'], 'progress': ['code']}


def attend_code(win):
    h = hashlib.md5(f'{SECRET}:{win}'.encode()).hexdigest()[:8]
    return f'{int(h, 16) % 10000:04d}'


def now_hm(): return dt.datetime.now().strftime('%H:%M:%S')
def today(): return dt.date.today().isoformat()


def match(row, filters):
    for k, v in filters:
        if k == 'or':               # or=(cls.eq.전체,cls.eq.월목반)
            inner = v.strip('()').split(',')
            if not any(str(row.get(c.split('.')[0])) == c.split('.', 2)[2] for c in inner): return False
        elif v.startswith('eq.'):
            if str(row.get(k)) != v[3:]: return False
    return True


class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def send(self, code, body=None, extra=None):
        data = b'' if body is None else json.dumps(body, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET,POST,PATCH,DELETE,OPTIONS')
        for k, v in (extra or {}).items(): self.send_header(k, v)
        self.send_header('Content-Length', str(len(data)))
        self.end_headers(); self.wfile.write(data)

    def do_OPTIONS(self): self.send(204)

    def who(self):
        auth = self.headers.get('Authorization', '').replace('Bearer ', '')
        if auth in TOKENS: return ('owner', None)
        code = self.headers.get('x-student-code', '')
        return ('student', code) if code else ('anon', None)

    def body(self):
        n = int(self.headers.get('Content-Length') or 0)
        return json.loads(self.rfile.read(n) or b'null') if n else None

    def visible(self, table, role, code):
        rows = DB[table]
        if role == 'owner': return rows
        if role != 'student': return []
        if table == 'students': return [r for r in rows if r['code'] == code and r['until'] >= today()]
        if table == 'attendance': return [r for r in rows if r['code'] == code]
        if table == 'notices':
            me = next((s for s in DB['students'] if s['code'] == code), None)
            return [r for r in rows if r['cls'] == '전체' or (me and r['cls'] == me['cls'])]
        if table in ('notice_reads', 'progress'): return [r for r in rows if r['code'] == code]
        return []

    def do_POST(self):
        u = urlparse(self.path); qs = parse_qs(u.query); b = self.body(); role, code = self.who()
        if u.path == '/__reset':          # 시험용: 메모리 비우기
            for k in DB: DB[k] = []
            TOKENS.clear(); return self.send(200, {'ok': True})
        if u.path == '/auth/v1/token':
            if qs.get('grant_type') == ['password']:
                if b.get('email') == OWNER_EMAIL and b.get('password') == OWNER_PW:
                    t = uuid.uuid4().hex; TOKENS[t] = OWNER_EMAIL
                    return self.send(200, {'access_token': t, 'refresh_token': 'r-' + t, 'user': {'email': OWNER_EMAIL}})
                return self.send(400, {'error_description': '이메일 또는 비밀번호가 다릅니다.'})
            if qs.get('grant_type') == ['refresh_token']:
                t = uuid.uuid4().hex; TOKENS[t] = OWNER_EMAIL
                return self.send(200, {'access_token': t, 'refresh_token': 'r-' + t})
            return self.send(400, {'error_description': 'unsupported'})
        if u.path.startswith('/rest/v1/rpc/'):
            fn = u.path.rsplit('/', 1)[1]
            if fn == 'mark_attend':
                s = next((x for x in DB['students'] if x['code'] == b.get('p_code') and x['until'] >= today()), None)
                if not s: return self.send(200, {'ok': False, 'why': '등록되지 않았거나 만료된 코드입니다.'})
                w = int(time.time() // 30)
                if b.get('p_entered') not in (attend_code(w), attend_code(w - 1)):
                    return self.send(200, {'ok': False, 'why': '코드가 맞지 않습니다. 입구 화면의 지금 숫자를 다시 봐 주세요.'})
                return self.send(200, self.attend(s, False))
            if role != 'owner': return self.send(401, {'message': 'owner only'})
            if fn == 'current_attend_code':
                w = int(time.time() // 30); return self.send(200, {'code': attend_code(w), 'win': w})
            if fn == 'mark_attend_manual':
                s = next((x for x in DB['students'] if x['code'] == b.get('p_code')), None)
                if not s: return self.send(200, {'ok': False, 'why': '학생을 찾을 수 없습니다.'})
                return self.send(200, self.attend(s, True))
            return self.send(404, {'message': 'no rpc ' + fn})
        if u.path.startswith('/rest/v1/'):
            table = u.path.split('/')[3]
            if table not in DB: return self.send(404, {'message': 'no table'})
            prefer = self.headers.get('Prefer', '')
            if role == 'anon': return self.send(401, {'message': 'no auth'})
            if role == 'student' and not (table in ('notice_reads', 'progress') and b.get('code') == code):
                return self.send(401, {'message': 'RLS: student may only write own notice_reads/progress'})
            row = dict(b)
            if table == 'notices': row.setdefault('id', str(uuid.uuid4())); row.setdefault('at', dt.datetime.now(dt.timezone.utc).isoformat()); row.setdefault('body', '')
            if table == 'students': row.setdefault('joined', today()); row.setdefault('phone', '')
            if table == 'notice_reads': row.setdefault('at', dt.datetime.now(dt.timezone.utc).isoformat())
            if table == 'progress': row.setdefault('at', dt.datetime.now(dt.timezone.utc).isoformat())
            key = tuple(row.get(k) for k in PK[table])
            dup = next((r for r in DB[table] if tuple(r.get(k) for k in PK[table]) == key), None)
            if dup is not None:
                if 'ignore-duplicates' in prefer: return self.send(201, [] if 'representation' in prefer else None)
                if 'merge-duplicates' in prefer: dup.update(row); row = dup
                else: return self.send(409, {'message': 'duplicate key'})
            else: DB[table].append(row)
            return self.send(201, [row] if 'representation' in prefer else None)
        self.send(404, {'message': 'not found'})

    def attend(self, s, manual):
        d = today(); r = next((a for a in DB['attendance'] if a['code'] == s['code'] and a['date'] == d), None)
        if r: return {'ok': True, 'dup': True, 'time': r['time'][:5], 'late': r['late']}
        t = now_hm(); late = t[:5] > CLASS_START.get(s['cls'], '18:00')
        DB['attendance'].append({'code': s['code'], 'date': d, 'time': t, 'late': late, 'manual': manual})
        return {'ok': True, 'time': t[:5], 'late': late}

    def do_GET(self):
        u = urlparse(self.path); role, code = self.who()
        if not u.path.startswith('/rest/v1/'): return self.send(404, {'message': 'not found'})
        table = u.path.split('/')[3]
        if table not in DB: return self.send(404, {'message': 'no table'})
        if role == 'anon': return self.send(401, {'message': 'no auth'})
        filters = [(unquote(k), unquote(v)) for k, v in parse_qs(u.query, keep_blank_values=True).items() for v in [v[0]] if k not in ('select', 'order')]
        rows = [r for r in self.visible(table, role, code) if match(r, filters)]
        order = parse_qs(u.query).get('order', [''])[0]
        if order:
            for part in reversed(order.split(',')):
                k, _, d = part.partition('.'); rows.sort(key=lambda r: str(r.get(k, '')), reverse=(d == 'desc'))
        self.send(200, rows)

    def do_DELETE(self):
        u = urlparse(self.path); role, _ = self.who()
        if role != 'owner': return self.send(401, {'message': 'owner only'})
        table = u.path.split('/')[3]
        filters = [(unquote(k), unquote(v[0])) for k, v in parse_qs(u.query).items()]
        keep = [r for r in DB[table] if not match(r, filters)]
        gone = [r for r in DB[table] if match(r, filters)]
        DB[table] = keep
        if table == 'students':   # on delete cascade
            codes = {r['code'] for r in gone}
            for t in ('attendance', 'notice_reads', 'progress'): DB[t] = [r for r in DB[t] if r['code'] not in codes]
        self.send(204)


if __name__ == '__main__':
    print(f'mock supabase on http://127.0.0.1:{PORT}  owner={OWNER_EMAIL}/{OWNER_PW} anon={ANON}')
    ThreadingHTTPServer(('127.0.0.1', PORT), H).serve_forever()

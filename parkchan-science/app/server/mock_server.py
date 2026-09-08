#!/usr/bin/env python3
"""Supabase 흉내 서버(v2) — 앱의 서버 어댑터를 실제 계정 없이 끝까지 시험하기 위한 것.

PostgREST(REST) 의 부분집합 + Auth(가입·로그인·재설정·로그아웃) + RPC(mark_attend·mark_attend_manual·current_attend_code·redeem_pass·delete_my_account)
를 메모리 안에서 흉내 내고, schema.sql 의 RLS 와 같은 규칙을 적용한다:
  원장(is_owner 이메일) → 전부 · 로그인한 학생/보호자 → 자기(자녀) 코드 행만 · 비로그인 + x-student-code → 그 코드 행만.

사용: python3 app/server/mock_server.py [포트=8766]
  원장 이메일  owner@parkchan.kr (schema.sql 의 OWNER_EMAIL_HERE 에 해당) · 가입은 아무 이메일이나 됨
  anon 키      anon · 출석 씨앗 mock-secret
"""
import json, sys, time, hashlib, uuid, datetime as dt
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs, unquote

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8766
OWNER_EMAIL, ANON, SECRET = 'owner@parkchan.kr', 'anon', 'mock-secret'
DB = {}
USERS = {}    # id → {id, email, pw}
TOKENS = {}   # access_token → user id
PK = {'students': ['code'], 'attendance': ['code', 'date'], 'notices': ['id'], 'sched': ['id'], 'posts': ['id'], 'comments': ['id'], 'notice_reads': ['notice_id', 'code'], 'progress': ['code'],
      'classes': ['cls'], 'profiles': ['id'], 'passes': ['code']}


def reset():
    for k in PK: DB[k] = []
    DB['classes'] = [{'cls': '월목반', 'start_time': '18:00:00'}, {'cls': '화금반', 'start_time': '18:00:00'}, {'cls': '수토반', 'start_time': '14:00:00'}]
    USERS.clear(); TOKENS.clear()
    u = {'id': str(uuid.uuid4()), 'email': OWNER_EMAIL, 'pw': 'owner-pass'}; USERS[u['id']] = u
    DB['profiles'].append({'id': u['id'], 'role': 'owner', 'name': '원장', 'phone': '', 'student_code': None, 'child_code': None, 'pass_until': None, 'created_at': now()})


def attend_code(win):
    h = hashlib.md5(f'{SECRET}:{win}'.encode()).hexdigest()[:8]
    return f'{int(h, 16) % 10000:04d}'
def now(): return dt.datetime.now(dt.timezone.utc).isoformat()
def now_hms(): return dt.datetime.now().strftime('%H:%M:%S')
def today(): return dt.date.today().isoformat()
def class_start(cls): return next((c['start_time'][:5] for c in DB['classes'] if c['cls'] == cls), '18:00')
reset()


def match(row, filters):
    for k, v in filters:
        if k == 'or':
            inner = v.strip('()').split(',')
            if not any(str(row.get(c.split('.')[0])) == c.split('.', 2)[2] for c in inner): return False
            continue
        op, _, val = v.partition('.')
        x = row.get(k)
        if op == 'eq' and str(x) != val: return False
        if op == 'gte' and not (x is not None and str(x) >= val): return False
        if op == 'lte' and not (x is not None and str(x) <= val): return False
        if op == 'not' and val.startswith('like.'):
            pat = val[5:].replace('*', '')
            if str(x).startswith(pat): return False
    return True


class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def send(self, code, body=None):
        data = b'' if body is None else json.dumps(body, ensure_ascii=False).encode()
        self.send_response(code)
        for k, v in (('Content-Type', 'application/json'), ('Access-Control-Allow-Origin', '*'), ('Access-Control-Allow-Headers', '*'),
                     ('Access-Control-Allow-Methods', 'GET,POST,PATCH,DELETE,OPTIONS'), ('Content-Length', str(len(data)))): self.send_header(k, v)
        self.end_headers(); self.wfile.write(data)

    def do_OPTIONS(self): self.send(204)

    def body(self):
        n = int(self.headers.get('Content-Length') or 0)
        return json.loads(self.rfile.read(n) or b'null') if n else None

    # ── 누구인가: (role, uid, codes) ──
    def who(self):
        tok = self.headers.get('Authorization', '').replace('Bearer ', '')
        hdr = self.headers.get('x-student-code', '')
        codes = {hdr} if hdr else set()
        if tok in TOKENS:
            uid = TOKENS[tok]; p = self.profile(uid)
            if USERS[uid]['email'] == OWNER_EMAIL: return ('owner', uid, codes)
            if p:
                if p.get('student_code'): codes.add(p['student_code'])
                if p.get('child_code'): codes.add(p['child_code'])
            return ('user', uid, codes)
        return ('anon', None, codes)

    def profile(self, uid): return next((p for p in DB['profiles'] if p['id'] == uid), None)

    def visible(self, table, role, uid, codes):
        rows = DB[table]
        if role == 'owner': return rows
        if table == 'classes': return rows
        if table == 'profiles': return [r for r in rows if r['id'] == uid] if uid else []
        if table == 'passes': return []
        if table == 'students': return [r for r in rows if r['code'] in codes and r['until'] >= today()]
        if table == 'attendance': return [r for r in rows if r['code'] in codes]
        if table in ('notices', 'sched'):
            cls = {s['cls'] for s in DB['students'] if s['code'] in codes}
            return [r for r in rows if r['cls'] == '전체' or r['cls'] in cls]
        if table in ('posts', 'comments'): return [r for r in rows if not r.get('deleted')] if uid else []
        if table == 'notice_reads': return [r for r in rows if r['code'] in codes]
        if table == 'progress': return [r for r in rows if r['code'] in codes or (uid and r['code'] == 'u:' + uid)]
        return []

    def can_write(self, table, role, uid, codes, row):
        if role == 'owner': return True
        if table == 'profiles': return uid and row.get('id') == uid and row.get('role') != 'owner'
        if table in ('posts', 'comments'): return bool(uid)
        if table == 'notice_reads': return row.get('code') in codes
        if table == 'progress':
            p = self.profile(uid) if uid else None
            return row.get('code') in codes and (not uid or row.get('code') == (p or {}).get('student_code') or not p or not p.get('student_code')) or (uid and row.get('code') == 'u:' + uid)
        return False

    def token_for(self, u):
        t = uuid.uuid4().hex; TOKENS[t] = u['id']
        return {'access_token': t, 'refresh_token': 'r-' + t, 'user': {'id': u['id'], 'email': u['email'], 'user_metadata': {}}}

    def do_POST(self):
        u = urlparse(self.path); qs = parse_qs(u.query); b = self.body() or {}; role, uid, codes = self.who()
        if u.path == '/__reset': reset(); return self.send(200, {'ok': True})
        # ── Auth ──
        if u.path == '/auth/v1/signup':
            em = (b.get('email') or '').lower()
            if any(x['email'] == em for x in USERS.values()): return self.send(400, {'msg': '이미 가입된 이메일입니다. 로그인해 주세요.'})
            if len(b.get('password') or '') < 6: return self.send(400, {'msg': '비밀번호는 6자 이상이어야 합니다.'})
            usr = {'id': str(uuid.uuid4()), 'email': em, 'pw': b['password']}; USERS[usr['id']] = usr
            return self.send(200, self.token_for(usr))
        if u.path == '/auth/v1/token':
            if qs.get('grant_type') == ['password']:
                usr = next((x for x in USERS.values() if x['email'] == (b.get('email') or '').lower() and x['pw'] == b.get('password')), None)
                if not usr: return self.send(400, {'error_description': '이메일 또는 비밀번호가 다릅니다.'})
                return self.send(200, self.token_for(usr))
            if qs.get('grant_type') == ['refresh_token']:
                old = (b.get('refresh_token') or '')[2:]
                if old not in TOKENS: return self.send(400, {'error_description': 'invalid refresh'})
                return self.send(200, self.token_for(USERS[TOKENS[old]]))
            return self.send(400, {'error_description': 'unsupported'})
        if u.path == '/auth/v1/recover':
            if not any(x['email'] == (b.get('email') or '').lower() for x in USERS.values()): return self.send(400, {'msg': '가입되지 않은 이메일입니다.'})
            return self.send(200, {})
        if u.path == '/auth/v1/logout':
            tok = self.headers.get('Authorization', '').replace('Bearer ', ''); TOKENS.pop(tok, None); return self.send(204)
        # ── RPC ──
        if u.path.startswith('/rest/v1/rpc/'):
            fn = u.path.rsplit('/', 1)[1]
            if fn == 'mark_attend':
                s = next((x for x in DB['students'] if x['code'] == b.get('p_code') and x['until'] >= today()), None)
                if not s: return self.send(200, {'ok': False, 'why': '등록되지 않았거나 만료된 코드입니다.'})
                w = int(time.time() // 30)
                if b.get('p_entered') not in (attend_code(w), attend_code(w - 1)):
                    return self.send(200, {'ok': False, 'why': '코드가 맞지 않습니다. 입구 화면의 지금 숫자를 다시 봐 주세요.'})
                return self.send(200, self.attend(s, False))
            if fn == 'redeem_pass':
                if not uid: return self.send(200, {'ok': False, 'why': '로그인이 필요합니다.'})
                p = next((x for x in DB['passes'] if x['code'] == b.get('p_code')), None)
                if not p: return self.send(200, {'ok': False, 'why': '없는 이용권 코드입니다.'})
                if p.get('used_by'): return self.send(200, {'ok': False, 'why': '이미 사용된 코드입니다.'})
                pr = self.profile(uid); base = max(pr.get('pass_until') or today(), today())
                until = (dt.date.fromisoformat(base) + dt.timedelta(days=p['days'])).isoformat()
                pr['pass_until'] = until; p['used_by'] = uid; p['used_at'] = today()
                return self.send(200, {'ok': True, 'until': until})
            if fn in ('like_toggle', 'report_item'):
                if not uid: return self.send(401, {'message': 'login required'})
                tbl = 'posts' if b.get('p_kind') == 'post' else 'comments'
                row = next((x for x in DB[tbl] if x['id'] == b.get('p_id')), None)
                if not row: return self.send(200, 0 if fn == 'report_item' else None)
                key = 'likes' if fn == 'like_toggle' else 'reports'
                row.setdefault(key, [])
                if fn == 'like_toggle':
                    row[key].remove(uid) if uid in row[key] else row[key].append(uid)
                    return self.send(200, None)
                if uid not in row[key]: row[key].append(uid)
                return self.send(200, len(row[key]))
            if fn == 'pick_comment':
                if not uid: return self.send(401, {'message': 'login required'})
                post = next((x for x in DB['posts'] if x['id'] == b.get('p_post')), None)
                if not post or post.get('author') != uid: return self.send(401, {'message': '글쓴이만 채택할 수 있습니다'})
                for c in DB['comments']:
                    if c['post_id'] == post['id']: c['picked'] = (c['id'] == b.get('p_comment'))
                post['solved'] = True
                return self.send(200, None)
            if fn == 'delete_my_account':
                if not uid: return self.send(401, {'message': 'login required'})
                DB['profiles'] = [p for p in DB['profiles'] if p['id'] != uid]; DB['progress'] = [p for p in DB['progress'] if p['code'] != 'u:' + uid]
                USERS.pop(uid, None); [TOKENS.pop(t) for t in [t for t, v in TOKENS.items() if v == uid]]
                return self.send(200, None)
            if role != 'owner': return self.send(401, {'message': 'owner only'})
            if fn == 'current_attend_code':
                w = int(time.time() // 30); return self.send(200, {'code': attend_code(w), 'win': w})
            if fn == 'mark_attend_manual':
                s = next((x for x in DB['students'] if x['code'] == b.get('p_code')), None)
                if not s: return self.send(200, {'ok': False, 'why': '학생을 찾을 수 없습니다.'})
                return self.send(200, self.attend(s, True))
            return self.send(404, {'message': 'no rpc ' + fn})
        # ── REST insert / upsert ──
        if u.path.startswith('/rest/v1/'):
            table = u.path.split('/')[3]
            if table not in DB: return self.send(404, {'message': 'no table'})
            prefer = self.headers.get('Prefer', '')
            if role == 'anon' and not codes: return self.send(401, {'message': 'no auth'})
            row = dict(b)
            if not self.can_write(table, role, uid, codes, row): return self.send(401, {'message': 'RLS: not allowed'})
            if table == 'notices': row.setdefault('id', str(uuid.uuid4())); row.setdefault('at', now()); row.setdefault('body', '')
            if table in ('posts', 'comments'):
                row.setdefault('id', str(uuid.uuid4())); row.setdefault('at', now()); row.setdefault('author', uid)
                row.setdefault('nick', (self.profile(uid) or {}).get('nick') or '익명')
                for k, dv in (('likes', []), ('reports', []), ('deleted', False)): row.setdefault(k, list(dv) if isinstance(dv, list) else dv)
                if table == 'posts': row.setdefault('board', 'qna'); row.setdefault('body', ''); row.setdefault('solved', False); row.setdefault('attach', None)
                else: row.setdefault('picked', False)
            if table == 'sched': row.setdefault('id', str(uuid.uuid4())); row.setdefault('at', now()); row.setdefault('memo', ''); row.setdefault('kind', 'etc')
            if table == 'students': row.setdefault('joined', today()); row.setdefault('phone', '')
            if table in ('notice_reads', 'progress'): row.setdefault('at', now())
            if table == 'profiles': row.setdefault('created_at', now()); row.setdefault('nick', ''); [row.setdefault(k, None) for k in ('student_code', 'child_code', 'pass_until')]; row.setdefault('phone', '')
            if table == 'passes': row.setdefault('issued', today()); row.setdefault('used_by', None); row.setdefault('used_at', None)
            if table == 'classes' and len(row.get('start_time', '')) == 5: row['start_time'] += ':00'
            key = tuple(row.get(k) for k in PK[table])
            dup = next((r for r in DB[table] if tuple(r.get(k) for k in PK[table]) == key), None)
            if dup is not None:
                if 'ignore-duplicates' in prefer: return self.send(201, [] if 'representation' in prefer else None)
                if 'merge-duplicates' in prefer: dup.update(row); row = dup
                else: return self.send(409, {'message': 'duplicate key'})
            else: DB[table].append(row)
            return self.send(201, [row] if 'representation' in prefer else None)
        self.send(404, {'message': 'not found'})

    def do_PATCH(self):
        u = urlparse(self.path); b = self.body() or {}; role, uid, codes = self.who()
        table = u.path.split('/')[3]
        filters = [(unquote(k), unquote(v[0])) for k, v in parse_qs(u.query).items() if k not in ('select', 'order')]
        rows = [r for r in self.visible(table, role, uid, codes) if match(r, filters)]
        for r in rows:
            if not self.can_write(table, role, uid, codes, {**r, **b}): return self.send(401, {'message': 'RLS: not allowed'})
            r.update(b)
        self.send(204)

    def attend(self, s, manual):
        d = today(); r = next((a for a in DB['attendance'] if a['code'] == s['code'] and a['date'] == d), None)
        if r: return {'ok': True, 'dup': True, 'time': r['time'][:5], 'late': r['late']}
        t = now_hms(); late = t[:5] > class_start(s['cls'])
        DB['attendance'].append({'code': s['code'], 'date': d, 'time': t, 'late': late, 'manual': manual})
        return {'ok': True, 'time': t[:5], 'late': late}

    def do_GET(self):
        u = urlparse(self.path); role, uid, codes = self.who()
        if not u.path.startswith('/rest/v1/'): return self.send(404, {'message': 'not found'})
        table = u.path.split('/')[3]
        if table not in DB: return self.send(404, {'message': 'no table'})
        if role == 'anon' and not codes and table != 'classes': return self.send(401, {'message': 'no auth'})
        q = parse_qs(u.query, keep_blank_values=True)
        filters = [(unquote(k), unquote(v[0])) for k, v in q.items() if k not in ('select', 'order')]
        rows = [r for r in self.visible(table, role, uid, codes) if match(r, filters)]
        order = q.get('order', [''])[0]
        if order:
            for part in reversed(order.split(',')):
                k, _, d = part.partition('.'); rows.sort(key=lambda r: str(r.get(k, '') or ''), reverse=(d == 'desc'))
        self.send(200, rows)

    def do_DELETE(self):
        u = urlparse(self.path); role, uid, codes = self.who()
        if role != 'owner': return self.send(401, {'message': 'owner only'})
        table = u.path.split('/')[3]
        filters = [(unquote(k), unquote(v[0])) for k, v in parse_qs(u.query).items()]
        gone = [r for r in DB[table] if match(r, filters)]; DB[table] = [r for r in DB[table] if not match(r, filters)]
        if table == 'students':
            cs = {r['code'] for r in gone}
            for t in ('attendance', 'notice_reads', 'progress'): DB[t] = [r for r in DB[t] if r['code'] not in cs]
            for p in DB['profiles']:
                if p.get('student_code') in cs: p['student_code'] = None
                if p.get('child_code') in cs: p['child_code'] = None
        self.send(204)


if __name__ == '__main__':
    print(f'mock supabase v2 on http://127.0.0.1:{PORT}  owner={OWNER_EMAIL}/owner-pass anon={ANON}')
    ThreadingHTTPServer(('127.0.0.1', PORT), H).serve_forever()

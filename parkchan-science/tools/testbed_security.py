#!/usr/bin/env python3
"""서버 보안 시험 — 진짜 Postgres·PostgREST 시험대(tools/testbed_up.sh)에 대고, 막혀야 할 일이 실제로 막히는지 두드려 본다.

사용: bash tools/testbed_up.sh && python3 tools/testbed_security.py
"""
import json, sys, datetime as dt, urllib.request, urllib.error
from zoneinfo import ZoneInfo
GW = 'http://127.0.0.1:8767'
OK, BAD = [], []


def call(m, path, body=None, tok=None, prefer=None, ip=None):
    h = {'Content-Type': 'application/json', 'apikey': ANON, 'Authorization': 'Bearer ' + (tok or ANON)}
    if prefer: h['Prefer'] = prefer
    if ip: h['X-Forwarded-For'] = ip
    req = urllib.request.Request(GW + path, data=None if body is None else json.dumps(body).encode(), method=m, headers=h)
    try:
        with urllib.request.urlopen(req) as r: t = r.read(); return r.status, (json.loads(t) if t else None)
    except urllib.error.HTTPError as e:
        t = e.read()
        try: return e.code, json.loads(t)
        except Exception: return e.code, t.decode()


def check(name, cond, info=''):
    (OK if cond else BAD).append(name); print(('  ✓ ' if cond else '  ✗ ') + name + ('' if cond else f'   ← {info}'))


def signup(email, name, role='student', **meta):
    s, j = call('POST', '/auth/v1/signup', {'email': email, 'password': 'pw123456', 'data': {'name': name, 'role': role, **meta}})
    assert s == 200 and j.get('access_token'), (s, j); return j['access_token'], j['user']['id']
def login(email, pw):
    s, j = call('POST', '/auth/v1/token?grant_type=password', {'email': email, 'password': pw}); assert s == 200, j; return j['access_token'], j['user']['id']
def rpc(fn, body, tok, ip=None): return call('POST', f'/rest/v1/rpc/{fn}', body, tok, ip=ip)
def me(tok, uid): return call('GET', f'/rest/v1/profiles?id=eq.{uid}&select=*', tok=tok)[1][0]


ANON = json.loads(urllib.request.urlopen(GW + '/__anon').read())['anon']
call('POST', '/__reset')
OWN, OWN_ID = login('owner@parkchan.kr', 'owner-pass')
print('▸ 원장 · 가입 트리거')
check('원장 계정은 원장 역할', me(OWN, OWN_ID)['role'] == 'owner')
s, st = call('POST', '/rest/v1/students?select=code,name,cls,until', {'code': 'MON123', 'name': '박○○', 'cls': '월목반', 'until': '2099-02-28'}, OWN, 'return=representation')
check('원장이 학생 코드 발급', s == 201, st)
call('POST', '/rest/v1/students', {'code': 'OLD111', 'name': '졸업생', 'cls': '월목반', 'until': '2020-02-28'}, OWN)
A, A_ID = signup('a@test.kr', '학생A', phone='010', terms_ver='2026-09-29')
pa = me(A, A_ID)
check('가입하면 프로필이 저절로 생김(역할·연락처·약관 동의 시각)', pa['role'] == 'student' and pa['phone'] == '010' and pa['agreed_at'], pa)
X, X_ID = signup('x@test.kr', '사칭', role='owner')
check('가입할 때 역할을 owner 로 보내도 학생이 됨', me(X, X_ID)['role'] == 'student')

print('▸ 프로필 칸 권한')
s, _ = call('PATCH', f'/rest/v1/profiles?id=eq.{A_ID}', {'pass_until': '2099-12-31'}, A)
check('학생이 자기 이용권 만료일을 못 고침', s in (401, 403) and me(A, A_ID)['pass_until'] is None, s)
s, _ = call('PATCH', f'/rest/v1/profiles?id=eq.{A_ID}', {'role': 'owner'}, A); check('학생이 자기 역할을 못 바꿈', s in (401, 403), s)
s, _ = call('PATCH', f'/rest/v1/profiles?id=eq.{A_ID}', {'student_code': 'MON123'}, A); check('학원 코드를 직접 못 써 넣음(함수로만)', s in (401, 403), s)
s, _ = call('PATCH', f'/rest/v1/profiles?id=eq.{A_ID}', {'name': '학생에이', 'nick': '에이'}, A); check('이름·닉네임은 고칠 수 있음', s == 204 and me(A, A_ID)['nick'] == '에이', s)
s, j = call('GET', '/rest/v1/profiles?select=id', tok=A); check('남의 프로필은 안 보임', s == 200 and len(j) == 1, j)

print('▸ 학원 코드 연결')
s, j = call('GET', '/rest/v1/students?select=*', tok=A); check('연결 전에는 학생 명단이 안 보임', j == [], j)
s, j = call('GET', '/rest/v1/students?code=eq.MON123&select=*', tok=ANON); check('비로그인은 코드로 조회해도 안 보임', j == [], j)
r = rpc('link_code', {'p_kind': 'student', 'p_code': 'OLD111'}, A)[1]; check('수강 끝난 코드는 거절', not r['ok'] and '끝났' in r['why'], r)
r = rpc('link_code', {'p_kind': 'student', 'p_code': 'mon123'}, A)[1]; check('맞는 코드(소문자도)로 연결', r['ok'] and r['student']['cls'] == '월목반', r)
s, j = call('GET', '/rest/v1/students?select=code', tok=A); check('연결 뒤 내 코드만 보임', [x['code'] for x in j] == ['MON123'], j)
B, B_ID = signup('b@test.kr', '학생B')
r = rpc('link_code', {'p_kind': 'student', 'p_code': 'MON123'}, B)[1]; check('같은 코드를 다른 학생 계정에 못 씀(돌려쓰기)', not r['ok'] and '다른 학생' in r['why'], r)
for i in range(10): rpc('link_code', {'p_kind': 'student', 'p_code': f'ZZZ{i:03d}'}, B)
r = rpc('link_code', {'p_kind': 'student', 'p_code': 'ZZZ999'}, B)[1]; check('틀린 코드 10번 뒤 1시간 잠김', not r['ok'] and '여러 번' in r['why'], r)
P, P_ID = signup('p@test.kr', '보호자', role='parent')
r = rpc('link_code', {'p_kind': 'student', 'p_code': 'OLD111'}, X)[1]
cur0 = __import__('psycopg2').connect('host=127.0.0.1 port=54329 user=postgres dbname=pcs').cursor()
cur0.execute("select count(*) from private.attempts where uid = %s and kind = 'code' and not ok", (X_ID,)); check('끝난 코드를 대 봐도 틀린 횟수로 셈', cur0.fetchone()[0] == 1)
IPS = [signup(f'ip{i}@test.kr', f'같은IP{i}') for i in range(4)]
for t, _u in IPS[:3]:
    for i in range(10): rpc('link_code', {'p_kind': 'student', 'p_code': f'IP{i:04d}'}, t, ip='203.0.113.7')
r = rpc('link_code', {'p_kind': 'student', 'p_code': 'MON123'}, IPS[3][0], ip='203.0.113.7')[1]; check('같은 곳(IP)에서 계정을 바꿔 30번 틀리면 새 계정도 잠김', not r['ok'] and '여러 번' in r['why'], r)
r = rpc('link_code', {'p_kind': 'student', 'p_code': 'IPX001'}, IPS[3][0], ip='198.51.100.9')[1]; check('  └ 다른 곳에서는 그대로 시도 가능', '여러 번' not in r.get('why', ''), r)
cur0.execute("insert into private.attempts(uid, kind, ok, ip) select null, 'code', false, '192.0.2.' || g from generate_series(1, 300) g"); cur0.connection.commit()
r = rpc('link_code', {'p_kind': 'student', 'p_code': 'MON123'}, P, ip='198.51.100.10')[1]; check('학원 전체로 1시간 300번 틀리면 잠시 모두 멈춤(대량 추측 차단)', not r['ok'] and '여러 번' in r['why'], r)
cur0.execute("delete from private.attempts where uid is null and ip like '192.0.2.%%'"); cur0.connection.commit()
r = rpc('link_code', {'p_kind': 'student', 'p_code': 'MON123'}, P)[1]; check('보호자 계정은 학생 코드 등록 불가', not r['ok'], r)
r = rpc('link_code', {'p_kind': 'child', 'p_code': 'MON123'}, P)[1]; check('보호자가 자녀 연결', r['ok'], r)
s, _ = call('POST', '/rest/v1/guardian_links', {'uid': P_ID, 'code': 'OLD111'}, P); check('보호자가 자녀 연결 표를 직접 못 씀(함수로만)', s in (401, 403), s)
s, j = call('GET', '/rest/v1/guardian_links?select=code', tok=P); check('보호자는 자기 자녀 연결만 봄', [x['code'] for x in j] == ['MON123'], j)
s, j = call('GET', '/rest/v1/guardian_links?select=code', tok=A); check('학생은 남의 보호자 연결을 못 봄', j == [], j)
s, n = rpc('release_code', {'p_code': 'MON123'}, A); check('학생은 코드 풀기 함수를 못 씀', s >= 400, s)

print('▸ 출석(30초 코드 · 한국 시간)')
code = rpc('current_attend_code', {}, OWN)[1]['code']
s, _ = rpc('current_attend_code', {}, A); check('학생은 지금 출석 코드를 못 봄', s >= 400, s)
r = rpc('mark_attend', {'p_code': 'MON123', 'p_entered': code}, B)[1]; check('남의 코드로 출석 못 함', not r['ok'], r)
for i in range(6): rpc('mark_attend', {'p_code': 'MON123', 'p_entered': '0000' if code != '0000' else '1111'}, A)
r = rpc('mark_attend', {'p_code': 'MON123', 'p_entered': code}, A)[1]; check('틀린 출석 코드 6번 뒤 잠김(원격 대입 방지)', not r['ok'] and '여러 번' in r['why'], r)
r = rpc('mark_attend_manual', {'p_code': 'MON123'}, OWN)[1]
kst = dt.datetime.now(ZoneInfo('Asia/Seoul'))
hh, mm = map(int, r['time'].split(':')); diff = abs((hh * 60 + mm) - (kst.hour * 60 + kst.minute))
check('출석 시각이 한국 시간으로 기록됨', r['ok'] and min(diff, 1440 - diff) <= 1, (r, kst.strftime('%H:%M')))
s, j = call('GET', '/rest/v1/attendance?select=date', tok=P); check('보호자는 자녀 출석을 봄', len(j) == 1 and j[0]['date'] == kst.date().isoformat(), j)
s, j = call('GET', '/rest/v1/attendance?select=date', tok=B); check('다른 학생은 못 봄', j == [], j)

print('▸ 진도')
s, _ = call('POST', '/rest/v1/progress?on_conflict=code', {'code': f'u:{B_ID}', 'state': {'done': [1]}}, B, 'resolution=merge-duplicates,return=minimal')
check('학원 밖 이용자 진도(u:계정) 저장됨', s == 201, s)
s, _ = call('POST', '/rest/v1/progress?on_conflict=code', {'code': 'MON123', 'state': {'done': [1, 2]}}, A, 'resolution=merge-duplicates,return=minimal'); check('학생 진도 저장', s == 201, s)
s, _ = call('POST', '/rest/v1/progress?on_conflict=code', {'code': 'MON123', 'state': {'done': []}}, P, 'resolution=merge-duplicates,return=minimal'); check('보호자는 자녀 진도를 못 고침', s >= 400, s)
s, _ = call('DELETE', '/rest/v1/progress?code=eq.MON123', tok=P)
s, j = call('GET', '/rest/v1/progress?code=eq.MON123&select=state', tok=P); check('보호자는 자녀 진도를 보되 못 지움', len(j) == 1 and j[0]['state']['done'] == [1, 2], j)
s, j = call('GET', '/rest/v1/progress?select=code', tok=B); check('남의 진도는 안 보임', [x['code'] for x in j] == [f'u:{B_ID}'], j)

print('▸ 이용권 · 결제')
call('POST', '/rest/v1/passes', {'code': 'PASS01', 'days': 30}, OWN)
r = rpc('redeem_pass', {'p_code': 'pass01'}, B)[1]; check('이용권 등록', r['ok'], r)
r = rpc('redeem_pass', {'p_code': 'PASS01'}, X)[1]; check('쓴 이용권은 다시 못 씀', not r['ok'], r)
cur0.execute("select count(*) from private.attempts where uid = %s and kind = 'pass' and not ok", (X_ID,)); check('  └ 이미 쓴 이용권을 대 봐도 틀린 횟수로 셈', cur0.fetchone()[0] == 1)
s, _ = rpc('grant_purchase', {'p_uid': B_ID, 'p_token': 't', 'p_product': 'y1', 'p_order': 'o', 'p_days': 365, 'p_raw': {}}, B)
check('앱에서 결제 반영 함수를 직접 못 부름(서버 검증 전용)', s >= 400, s)
s, _ = call('POST', '/rest/v1/passes', {'code': 'FREE99', 'days': 365}, B); check('학생이 이용권 코드를 못 만듦', s >= 400, s)

print('▸ 이야기')
s, j = call('POST', '/rest/v1/posts', {'board': 'qna', 'title': '질문', 'body': '효소 질문', 'author': B_ID}, A)
check('남의 이름(author)으로 글을 못 씀', s in (401, 403), s)
s, j = call('POST', '/rest/v1/posts?select=id,nick,author', {'board': 'qna', 'title': '질문', 'body': '효소 질문', 'nick': '원장'}, A, 'return=representation')
check('닉네임을 사칭해도 막힘', s in (401, 403), s)
s, j = call('POST', '/rest/v1/posts', {'board': 'qna', 'title': '선생님인 척', 'body': '...', 'staff': True}, A); check('학생이 선생님 표시를 달 수 없음', s in (401, 403), s)
s, _ = call('PATCH', f'/rest/v1/profiles?id=eq.{A_ID}', {'nick': '박찬선생님'}, A); check('닉네임으로 선생님 사칭 불가', s >= 400 and me(A, A_ID)['nick'] != '박찬선생님', s)
s, j = call('POST', '/rest/v1/posts?select=id,nick,author', {'board': 'qna', 'title': '질문', 'body': '효소 질문'}, A, 'return=representation')
check('글쓴이·닉네임은 서버가 채움', s == 201 and j[0]['nick'] == '에이' and j[0]['author'] == A_ID, j)
pid = j[0]['id']
s, j = call('GET', '/rest/v1/posts?select=reports', tok=B); check('누가 신고했는지는 안 보임', s >= 400, s)
s, j = call('POST', '/rest/v1/posts', {'board': 'qna', 'title': 't', 'body': 'b'}, ANON); check('비로그인은 글 못 씀', s >= 400, s)
s, j = call('GET', '/rest/v1/posts?select=id', tok=ANON); check('비로그인은 글 못 봄', s >= 400 or j == [], j)
for tok in (B, P): call('POST', '/rest/v1/comments', {'post_id': pid, 'body': '답'}, tok)
s, j = call('GET', f'/rest/v1/posts?id=eq.{pid}&select=comment_n', tok=B); check('댓글 수가 서버에서 셈', j[0]['comment_n'] == 2, j)
s, _ = call('PATCH', f'/rest/v1/posts?id=eq.{pid}', {'title': '남이 고침'}, B)
s, j = call('GET', f'/rest/v1/posts?id=eq.{pid}&select=title', tok=A); check('남의 글은 못 고침', j[0]['title'] == '질문', j)
s, _ = call('PATCH', f'/rest/v1/posts?id=eq.{pid}', {'likes': [B_ID, B_ID]}, A); check('좋아요 칸을 직접 못 고침', s >= 400, s)
for tok in (B, P, X): rpc('report_item', {'p_kind': 'post', 'p_id': pid}, tok)
s, j = call('GET', f'/rest/v1/posts?id=eq.{pid}&select=id', tok=B); check('신고 3건이면 다른 사람에게 가려짐(서버에서)', j == [], j)
s, j = call('GET', f'/rest/v1/posts?id=eq.{pid}&select=report_n', tok=A); check('글쓴이에게는 보임', len(j) == 1 and j[0]['report_n'] == 3, j)
s, j = call('GET', f'/rest/v1/posts?id=eq.{pid}&select=report_n', tok=OWN); check('원장에게는 보임', len(j) == 1, j)
call('PATCH', f'/rest/v1/posts?id=eq.{pid}', {'deleted': True}, OWN)
s, _ = call('PATCH', f'/rest/v1/posts?id=eq.{pid}', {'deleted': False}, A)
import psycopg2
cur = psycopg2.connect('host=127.0.0.1 port=54329 user=postgres dbname=pcs').cursor(); cur.execute('select deleted from posts where id=%s', (pid,))
check('원장이 지운 글을 글쓴이가 되살리지 못함', cur.fetchone()[0] is True)
codes = [call('POST', '/rest/v1/posts', {'board': 'talk', 'title': f'도배{i}', 'body': '...'}, B)[0] for i in range(6)]
check('글 도배 제한(10분에 5개)', codes[:5] == [201] * 5 and codes[5] >= 400, codes)

print('▸ 원장 판정 · 오류 기록 · 계정 삭제')
cur.execute("update auth.users set email_confirmed_at = null where email = 'owner@parkchan.kr'"); cur.connection.commit()
s, _ = rpc('current_attend_code', {}, OWN); check('메일 인증 안 된 원장 이메일은 원장 아님', s >= 400, s)
cur.execute("update auth.users set email_confirmed_at = now() where email = 'owner@parkchan.kr'"); cur.connection.commit()
cur.execute("insert into private.config values ('owner_uid', %s) on conflict (k) do update set v = excluded.v", (OWN_ID,)); cur.connection.commit()
s, _ = rpc('current_attend_code', {}, OWN); check('원장 계정을 못 박은 뒤에도 원장은 그대로', s == 200, s)
cur.execute("update private.config set v = %s where k = 'owner_uid'", (A_ID,)); cur.connection.commit()
s, _ = rpc('current_attend_code', {}, OWN); check('못 박은 계정이 아니면 원장 이메일이어도 원장 아님', s >= 400, s)
cur.execute("delete from private.config where k = 'owner_uid'"); cur.connection.commit()
s, _ = call('POST', '/rest/v1/client_errors', {'ver': '1', 'msg': 'TypeError x'}, ANON); check('앱 오류는 비로그인도 남김', s == 201, s)
s, j = call('GET', '/rest/v1/client_errors?select=id', tok=A); check('오류 기록은 원장만 봄', j == [], j)
s, j = call('GET', '/rest/v1/client_errors?select=id', tok=OWN); check('  └ 원장은 봄', len(j) == 1, j)
s, _ = rpc('register_push', {'p_token': 'tokA', 'p_platform': 'android'}, A); check('푸시 기기 등록', s in (200, 204), s)
s, j = call('GET', '/rest/v1/push_tokens?select=token', tok=B); check('남의 푸시 기기는 안 보임', j == [], j)
cur.execute("insert into purchases(purchase_token, uid, product, days, until) values ('keep-5y', %s, 'pass_m1', 30, current_date + 30)", (B_ID,)); cur.connection.commit()
s, _ = rpc('delete_my_account', {}, B); check('계정 삭제', s in (200, 204), s)
cur.execute("select uid from purchases where purchase_token = 'keep-5y'"); row = cur.fetchone(); check('  └ 결제 기록은 남기고 계정 연결만 끊음(5년 보관)', row is not None and row[0] is None, row)
s, _ = call('POST', '/auth/v1/token?grant_type=password', {'email': 'b@test.kr', 'password': 'pw123456'}); check('  └ 삭제한 계정으로 로그인 불가', s == 400, s)

print('▸ 만 14세 미만 · 보호자 동의')
K, K_ID = signup('kid@test.kr', '어린이', under14=True, guardian='김보호 01011112222')
check('14세 미만은 가입 직후 동의 전 상태', me(K, K_ID)['guardian_ok'] is False)
s, _ = call('PATCH', f'/rest/v1/profiles?id=eq.{K_ID}', {'guardian_ok': True}, K); check('동의 칸을 스스로 못 켬', s in (401, 403), s)
s, _ = call('POST', '/rest/v1/posts', {'board': 'talk', 'title': '안녕', 'body': '처음 왔어요'}, K); check('동의 전에는 글을 못 씀', s >= 400, s)
s, j = call('GET', '/rest/v1/posts?select=id', tok=K); check('동의 전에는 이야기를 못 봄', j == [], j)
s, _ = call('POST', '/rest/v1/progress?on_conflict=code', {'code': f'u:{K_ID}', 'state': {}}, K, 'resolution=merge-duplicates,return=minimal'); check('동의 전에는 진도를 서버에 못 남김', s >= 400, s)
r = rpc('consent_request', {}, K)[1]; tok = r.get('token', ''); check('동의 요청 링크 발급', r['ok'] and len(tok) == 36, r)
r = rpc('consent_request', {}, A)[1]; check('14세 이상은 동의 요청 불가', not r['ok'], r)
r = rpc('consent_info', {'p_token': tok}, ANON)[1]; check('동의 페이지는 로그인 없이 열리고 아이 이름은 가림', r['ok'] and r['child'].startswith('어') and '린' not in r['child'], r)
r = rpc('consent_info', {'p_token': 'x' * 36}, ANON)[1]; check('없는 링크는 거절', not r['ok'], r)
r = rpc('consent_give', {'p_token': tok, 'p_name': '김'}, ANON)[1]; check('보호자 성함 없이 동의 불가', not r['ok'], r)
r = rpc('consent_give', {'p_token': tok, 'p_name': '김보호'}, ANON)[1]; check('보호자가 동의 표시', r['ok'], r)
pk = me(K, K_ID); check('  └ 동의 표시만으로는 아직 안 열림 · 방법 web · 연락처 유지', not pk['guardian_ok'] and pk['guardian_how'] == 'web' and pk['guardian_at'] and '01011112222' in pk['guardian'], pk)
r = rpc('consent_info', {'p_token': tok}, ANON)[1]; check('  └ 동의 페이지를 다시 열면 "동의함"으로 보임', r['ok'] and r.get('done'), r)
r = rpc('consent_give', {'p_token': tok, 'p_name': '김보호'}, ANON)[1]; check('한 번 쓴 링크는 다시 못 씀', not r['ok'], r)
s, _ = call('POST', '/rest/v1/posts', {'board': 'talk', 'title': '안녕', 'body': '아직이에요'}, K); check('확인 문자 전에는 아직 글을 못 씀', s >= 400, s)
r = rpc('consent_request', {}, K)[1]; check('  └ 아이 앱은 "보호자가 동의함"을 앎', r.get('given'), r)
s, j = rpc('consent_list', {}, A); check('원장 아닌 사람은 동의 목록이 비어 보임', s == 200 and j == [], j)
s, _ = rpc('consent_mark', {'p_uid': K_ID, 'p_what': 'paper'}, A); check('원장 아닌 사람은 서면 동의 표시 불가', s >= 400, s)
s, _ = rpc('consent_mark', {'p_uid': K_ID, 'p_what': 'notified'}, A); check('원장 아닌 사람은 확인 문자 표시 불가', s >= 400 and not me(K, K_ID)['guardian_ok'], s)
s, j = rpc('consent_list', {}, OWN); check('원장은 동의 표시된 목록을 봄', s == 200 and any(x['id'] == K_ID and x['guardian_how'] == 'web' and x['guardian_at'] and not x['guardian_ok'] for x in j), j)
rpc('consent_mark', {'p_uid': K_ID, 'p_what': 'notified'}, OWN)
check('원장이 확인 문자 보냄 → 동의 확인 완료', rpc('consent_list', {}, OWN)[1][0]['notified_at'] is not None and me(K, K_ID)['guardian_ok'])
s, _ = call('POST', '/rest/v1/posts', {'board': 'talk', 'title': '안녕', 'body': '이제 써져요'}, K); check('확인 문자 뒤에는 글을 씀', s == 201, s)
K4, K4_ID = signup('kid4@test.kr', '표시없음', under14=True, guardian='최보호 01077778888')
rpc('consent_mark', {'p_uid': K4_ID, 'p_what': 'notified'}, OWN); check('보호자 동의 표시가 없으면 확인 문자 표시로 열리지 않음', not me(K4, K4_ID)['guardian_ok'])
K7, K7_ID = signup('kid7@test.kr', '번호틀림', under14=True, guardian='한보호 01012340000')
t7 = rpc('consent_request', {}, K7)[1]['token']; rpc('consent_give', {'p_token': t7, 'p_name': '한보호'}, ANON)
s, _ = rpc('consent_mark', {'p_uid': K7_ID, 'p_what': 'reset'}, A); check('원장 아닌 사람은 동의 표시를 못 지움', s >= 400 and me(K7, K7_ID)['guardian_how'] == 'web', s)
rpc('consent_mark', {'p_uid': K7_ID, 'p_what': 'reset'}, OWN); p7 = me(K7, K7_ID)
check('원장이 "번호가 달라요" → 동의 표시가 지워지고 잠김 유지', p7['guardian_how'] == 'reset' and not p7['guardian_ok'], p7)
rpc('consent_mark', {'p_uid': K7_ID, 'p_what': 'notified'}, OWN); check('  └ 지운 뒤에는 확인 문자 표시로 안 열림', not me(K7, K7_ID)['guardian_ok'])
r = rpc('consent_request', {'p_phone': '1234'}, K7)[1]; check('  └ 휴대전화가 아닌 번호로는 다시 요청 못 함', not r['ok'], r)
r = rpc('consent_request', {'p_phone': '010-5555-6666'}, K7)[1]; check('  └ 고친 번호로 새 링크 · 보호자 번호가 바뀜', r['ok'] and r['token'] and r['guardian'] == '한보호 01055556666', r)
rpc('consent_give', {'p_token': r['token'], 'p_name': '한보호'}, ANON); check('  └ 보호자가 다시 동의 표시', me(K7, K7_ID)['guardian_how'] == 'web')
r = rpc('consent_request', {'p_phone': '01099999999'}, K7)[1]; check('  └ 동의 표시 뒤에는 아이가 번호를 못 바꿈', r.get('given') and '01055556666' in me(K7, K7_ID)['guardian'], r)
K2, K2_ID = signup('kid2@test.kr', '늦은아이', under14=True, guardian='이보호 01033334444')
rpc('consent_mark', {'p_uid': K2_ID, 'p_what': 'paper'}, OWN); check('서면 동의 표시 → 동의 확인', me(K2, K2_ID)['guardian_how'] == 'paper')
K3, K3_ID = signup('kid3@test.kr', '방치', under14=True, guardian='박보호 01055556666')
K6, K6_ID = signup('kid6@test.kr', '문자대기', under14=True, guardian='정보호 01099990000')
t6 = rpc('consent_request', {}, K6)[1]['token']; rpc('consent_give', {'p_token': t6, 'p_name': '정보호'}, ANON)
cur.execute("update profiles set created_at = now() - interval '8 days' where id in (%s, %s, %s)", (K3_ID, K4_ID, K6_ID)); cur.execute('select private.purge_old()'); cur.connection.commit()
cur.execute('select count(*) from auth.users where id in (%s, %s)', (K3_ID, K4_ID)); check('7일 안에 동의 없는 계정은 지움', cur.fetchone()[0] == 0)
cur.execute('select count(*) from auth.users where id in (%s, %s)', (K_ID, K2_ID)); check('  └ 동의한 계정은 남김', cur.fetchone()[0] == 2)
cur.execute('select count(*) from auth.users where id = %s', (K6_ID,)); check('  └ 보호자가 동의를 표시하고 확인 문자만 남은 계정은 남김', cur.fetchone()[0] == 1)

print('▸ 공부 노트 — 나만 본다')
import uuid as _uuid
N1, N1_ID = signup('note1@test.kr', '노트하나'); N2, N2_ID = signup('note2@test.kr', '노트둘')
nid = str(_uuid.uuid4()); UP = 'resolution=merge-duplicates,return=minimal'
s, _ = call('POST', '/rest/v1/notes?on_conflict=id', {'id': nid, 'date': '2026-09-30', 'title': '비밀 메모', 'body': '나만 봄', 'cids': ['1101-01']}, N1, UP); check('내 노트 저장', s in (200, 201), s)
s, j = call('GET', '/rest/v1/notes?select=id,uid', tok=N1); check('  └ 내 노트는 내가 읽음 · 주인은 서버가 채움', len(j) == 1 and j[0]['uid'] == N1_ID, j)
s, j = call('GET', '/rest/v1/notes?select=id', tok=N2); check('다른 학생은 내 노트를 못 읽음', j == [], j)
s, j = call('GET', '/rest/v1/notes?select=id', tok=OWN); check('원장도 학생 노트를 못 읽음', j == [], j)
s, j = call('GET', '/rest/v1/notes?select=id', tok=ANON); check('로그인 안 하면 못 읽음', s >= 400 or j == [], j)
s, _ = call('POST', '/rest/v1/notes?on_conflict=id', {'id': nid, 'date': '2026-09-30', 'title': '덮어쓰기', 'body': 'x', 'cids': []}, N2, UP); check('남의 노트 id 로 덮어쓰기 불가', s >= 400, s)
s, j = call('PATCH', f'/rest/v1/notes?id=eq.{nid}', {'title': '남이 고침'}, N2, 'return=representation'); check('남의 노트 고치기 불가', j == [], j)
s, j = call('DELETE', f'/rest/v1/notes?id=eq.{nid}', None, N2, 'return=representation'); check('남의 노트 지우기 불가', j == [], j)
s, _ = call('POST', '/rest/v1/notes', {'id': str(_uuid.uuid4()), 'uid': N1_ID, 'date': '2026-09-30', 'title': '남 이름으로', 'body': '', 'cids': []}, N2); check('남의 계정 이름으로 노트 넣기 불가', s >= 400, s)
s, _ = call('POST', '/rest/v1/notes', {'id': str(_uuid.uuid4()), 'date': '2026-09-30', 'title': 'x' * 81, 'body': '', 'cids': []}, N1); check('제목 80자 넘으면 거절', s >= 400, s)
s, _ = call('POST', '/rest/v1/notes', {'id': str(_uuid.uuid4()), 'date': '2026-09-30', 'title': '', 'body': 'x' * 5001, 'cids': []}, N1); check('내용 5,000자 넘으면 거절', s >= 400, s)
K5, K5_ID = signup('kid5@test.kr', '동의전', under14=True, guardian='최보호 01077778888')
s, _ = call('POST', '/rest/v1/notes', {'id': str(_uuid.uuid4()), 'date': '2026-09-30', 'title': '동의 전', 'body': '', 'cids': []}, K5); check('보호자 동의 전에는 노트를 서버에 못 남김', s >= 400, s)
# 나중에 고친 쪽이 이긴다 — 옛 기기가 늦게 올린 더 오래된 수정은 버린다
s, _ = call('POST', '/rest/v1/notes?on_conflict=id', {'id': nid, 'date': '2026-09-30', 'title': '새 제목', 'body': '나만 봄', 'cids': [], 'updated_at': '2026-10-01T10:05:00+09:00'}, N1, UP)
s, _ = call('POST', '/rest/v1/notes?on_conflict=id', {'id': nid, 'date': '2026-09-30', 'title': '옛 제목', 'body': '나만 봄', 'cids': [], 'updated_at': '2026-10-01T10:00:00+09:00'}, N1, UP)
s, j = call('GET', f'/rest/v1/notes?id=eq.{nid}&select=title', tok=N1); check('더 오래된 수정은 새 수정을 덮지 않음', j and j[0]['title'] == '새 제목', (s, j))
call('PATCH', f'/rest/v1/notes?id=eq.{nid}', {'title': '비밀 메모', 'updated_at': '2026-10-01T11:00:00+09:00'}, N1)
# 3,000개 제한: 가득 차도 이미 있는 노트는 고칠 수 있고, 새로 넣기만 막힌다
cur.execute("insert into notes (id, uid, date, title) select gen_random_uuid(), %s, date '2026-01-01', 'bulk' from generate_series(1, 2999)", (N1_ID,)); cur.connection.commit()
s, _ = call('POST', '/rest/v1/notes?on_conflict=id', {'id': nid, 'date': '2026-09-30', 'title': '비밀 메모', 'body': '가득 차도 고침', 'cids': [], 'updated_at': '2026-10-01T12:00:00+09:00'}, N1, UP); check('3,000개가 차도 기존 노트 고치기는 됨', s in (200, 201), s)
s, _ = call('POST', '/rest/v1/notes?on_conflict=id', {'id': str(_uuid.uuid4()), 'date': '2026-09-30', 'title': '하나 더', 'body': '', 'cids': []}, N1, UP); check('3,000개를 넘는 새 노트는 거절', s >= 400, s)
cur.execute("delete from notes where uid = %s and title = 'bulk'", (N1_ID,)); cur.connection.commit()
cur.execute('select count(*) from notes where title = %s', ('비밀 메모',)); before = cur.fetchone()[0]
rpc('delete_my_account', {}, N1); cur.connection.commit()
cur.execute('select count(*) from notes where title = %s', ('비밀 메모',)); check('계정 삭제하면 노트도 지워짐', before == 1 and cur.fetchone()[0] == 0)

print('▸ 이야기 안전장치(도움이 필요해 보이는 글)')
s, j = call('POST', '/rest/v1/posts?select=id,care', {'board': 'talk', 'title': '힘들어요', 'body': '요즘 죽고 싶다는 생각이 들어요'}, N2, 'return=representation'); cid = j[0]['id'] if s == 201 else None
check('힘든 마음의 글은 서버가 care 표시', s == 201 and j[0].get('care') is True, (s, j))
s, j = call('PATCH', f'/rest/v1/posts?id=eq.{cid}', {'care': False}, N2, 'return=representation'); check('care 표시를 스스로 못 끔', s >= 400, (s, j))
s, j = call('POST', '/rest/v1/posts?select=id,care', {'board': 'qna', 'title': '세포 자살', 'body': '아폽토시스를 세포 자살이라 하나요? 유서 깊은 실험'}, N2, 'return=representation'); check('과학 용어는 care 아님', s == 201 and j[0].get('care') is False, (s, j))
s, j = call('POST', '/rest/v1/posts', {'board': 'talk', 'title': '괜찮아', 'body': '그냥 궁금해서', 'care': False}, N2); check('글쓸 때 care 칸을 직접 못 넣음', s >= 400, (s, j))
s, j = call('POST', '/rest/v1/posts?select=id,care', {'board': 'talk', 'title': '109 안내', 'body': '친구가 죽고 싶다고 하면 109로 연락하세요'}, OWN, 'return=representation'); oid = j[0]['id'] if s == 201 else None
check('원장이 쓴 안내 글도 care 판정은 됨', s == 201 and j[0].get('care') is True, (s, j))
s, j = call('POST', '/rest/v1/posts?select=id,care', {'board': 'qna', 'title': '세포의 자살', 'body': '세포가 자살한다는 게 무슨 뜻? 자살예방 캠페인 과제도 있어요'}, N2, 'return=representation'); check('세포의 자살·자살예방 과제는 care 아님', s == 201 and j[0].get('care') is False, (s, j))
s, j = rpc('care_list', {}, N2); check('학생은 먼저 살펴볼 목록을 못 받음', s == 200 and j == [], j)
s, j = rpc('care_list', {}, OWN); check('원장은 이름과 함께 받음', s == 200 and any(x['post_id'] == cid and x['name'] == '노트둘' for x in j), j)
check('  └ 원장이 쓴 글은 먼저 살펴볼 목록에 안 뜸', not any(x['post_id'] == oid for x in j), j)
s, j = call('PATCH', f'/rest/v1/posts?id=eq.{cid}&select=id,care', {'body': '이제 괜찮아요. 고마워요'}, N2, 'return=representation'); check('  └ 고쳐 쓰면 다시 판정', s == 200 and j and j[0].get('care') is False, (s, j))

print(f'\n보안 시험 {len(OK)}/{len(OK) + len(BAD)} 통과')
sys.exit(1 if BAD else 0)

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
def member(*uids):   # 이야기에 쓰려면 학원 코드나 이용권이 있어야 한다(2026-10) — 시험용 계정에 이용권 기간을 넣는다
    for u in uids: cur0.execute("update profiles set pass_until = current_date + 30, first_ok_at = coalesce(first_ok_at, now()) where id = %s", (u,))   # 첫 글 검토는 아래 '첫 글 검토'에서 따로 시험
    cur0.connection.commit()
cur0.execute("select count(*) from private.attempts where uid = %s and kind = 'code' and not ok", (X_ID,)); check('끝난 코드를 대 봐도 틀린 횟수로 셈', cur0.fetchone()[0] == 1)
IPS = [signup(f'ip{i}@test.kr', f'같은IP{i}') for i in range(4)]
for t, _u in IPS[:3]:
    for i in range(10): rpc('link_code', {'p_kind': 'student', 'p_code': f'IP{i:04d}'}, t, ip='203.0.113.7')
r = rpc('link_code', {'p_kind': 'student', 'p_code': 'MON123'}, IPS[3][0], ip='203.0.113.7')[1]; check('같은 곳(IP)에서 계정을 바꿔 30번 틀리면 새 계정도 잠김', not r['ok'] and '여러 번' in r['why'], r)
r = rpc('link_code', {'p_kind': 'student', 'p_code': 'IPX001'}, IPS[3][0], ip='198.51.100.9')[1]; check('  └ 다른 곳에서는 그대로 시도 가능', '여러 번' not in r.get('why', ''), r)
cur0.execute("select count(*) from private.attempts where ok and ip is not null"); check('  └ 맞게 넣은 기록에는 IP 를 남기지 않음(최소 수집)', cur0.fetchone()[0] == 0)
cur0.execute("insert into private.attempts(uid, kind, ok, ip, at) values (null, 'code', false, '192.0.2.250', now() - interval '2 days')"); cur0.connection.commit()
cur0.execute('select private.purge_old()'); cur0.connection.commit()
cur0.execute("select count(*) from private.attempts where ip = '192.0.2.250'"); check('  └ 코드 입력 기록(IP)은 하루 지나면 지움', cur0.fetchone()[0] == 0)
cur0.execute("insert into private.attempts(uid, kind, ok, ip) select null, 'code', false, '192.0.2.' || g from generate_series(1, 300) g"); cur0.connection.commit()
r = rpc('link_code', {'p_kind': 'student', 'p_code': 'MON123'}, P, ip='198.51.100.10')[1]; check('학원 전체로 1시간 300번 틀리면 잠시 모두 멈춤(대량 추측 차단)', not r['ok'] and '여러 번' in r['why'], r)
cur0.execute("delete from private.attempts where uid is null and ip like '192.0.2.%%'"); cur0.connection.commit()
r = rpc('link_code', {'p_kind': 'student', 'p_code': 'MON123'}, P)[1]; check('보호자 계정은 학생 코드 등록 불가', not r['ok'], r)
r = rpc('link_code', {'p_kind': 'child', 'p_code': 'MON123'}, P)[1]; check('보호자가 자녀 연결 요청 · 원장 확인 전에는 자녀 이름도 안 줌', r['ok'] and r.get('pending') and 'student' not in r, r)
s, j = call('GET', '/rest/v1/students?select=name,phone', tok=P); check('  └ 확인 전에는 자녀 정보·연락처를 못 봄', j == [], j)
s, j = rpc('guardian_requests', {}, A); check('  └ 원장 아닌 사람은 연결 요청 목록이 비어 보임', j == [], j)
s, _ = rpc('guardian_decide', {'p_uid': P_ID, 'p_code': 'MON123', 'p_ok': True}, P); check('  └ 보호자가 스스로 확인 못 함', s >= 400, s)
s, j = rpc('guardian_requests', {}, OWN); check('  └ 원장은 요청을 봄(보호자 이름·이메일·학생)', any(x['uid'] == P_ID and x['code'] == 'MON123' and x['email'] == 'p@test.kr' for x in j), j)
rpc('guardian_decide', {'p_uid': P_ID, 'p_code': 'MON123', 'p_ok': True}, OWN)
r = rpc('link_code', {'p_kind': 'child', 'p_code': 'MON123'}, P)[1]; check('원장이 확인하면 자녀가 열림', r['ok'] and r.get('student', {}).get('cls') == '월목반', r)
SP, SP_ID = signup('stalker@test.kr', '반친구', role='parent')
rpc('link_code', {'p_kind': 'child', 'p_code': 'MON123'}, SP); rpc('guardian_decide', {'p_uid': SP_ID, 'p_code': 'MON123', 'p_ok': False}, OWN)
s, j = call('GET', '/rest/v1/guardian_links?select=code', tok=SP); check('  └ 원장이 거절하면 연결이 지워짐', j == [], j)
s, j = rpc('my_guardians', {}, A); check('학생은 자기에게 연결된 보호자를 봄', s == 200 and [x['name'] for x in j] == ['보호자'], j)
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
cur0.execute("update profiles set first_ok_at = now() where role = 'student'"); cur0.connection.commit()   # 이 절은 첫 글 검토를 지난 학생으로(검토는 아래 절에서)
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
for tok in (B, A): call('POST', '/rest/v1/comments', {'post_id': pid, 'body': '답'}, tok)
s, j = call('POST', '/rest/v1/comments', {'post_id': pid, 'body': '보호자 답'}, P); check('보호자 계정은 댓글을 못 씀(읽기만)', s == 403 and '보호자' in str(j), (s, j))
s, j = call('GET', f'/rest/v1/posts?id=eq.{pid}&select=comment_n', tok=B); check('댓글 수가 서버에서 셈', j[0]['comment_n'] == 2, j)
s, _ = call('PATCH', f'/rest/v1/posts?id=eq.{pid}', {'title': '남이 고침'}, B)
s, j = call('GET', f'/rest/v1/posts?id=eq.{pid}&select=title', tok=A); check('남의 글은 못 고침', j[0]['title'] == '질문', j)
s, _ = call('PATCH', f'/rest/v1/posts?id=eq.{pid}', {'likes': [B_ID, B_ID]}, A); check('좋아요 칸을 직접 못 고침', s >= 400, s)
s, j = rpc('report_item', {'p_kind': 'post', 'p_id': pid}, B); check('가입 하루 안 된 계정은 신고 못 함(가짜 계정으로 글 가리기 방지)', s >= 400 and '하루' in str(j), j)
cur1 = __import__('psycopg2').connect('host=127.0.0.1 port=54329 user=postgres dbname=pcs').cursor(); cur1.execute("update profiles set created_at = now() - interval '2 days'"); cur1.connection.commit()
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
s, j = call('POST', '/rest/v1/posts', {'board': 'talk', 'title': '안녕', 'body': '이제 써져요'}, K); check('  └ 동의가 끝나도 학원 코드·이용권이 없으면 읽기만', s == 403 and '학원 코드나 이용권' in str(j), (s, j))
member(K_ID); s, _ = call('POST', '/rest/v1/posts', {'board': 'talk', 'title': '안녕', 'body': '이제 써져요'}, K); check('확인 문자 뒤에는 글을 씀(이용권 있음)', s == 201, s)
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
N1, N1_ID = signup('note1@test.kr', '노트하나'); N2, N2_ID = signup('note2@test.kr', '노트둘'); member(N2_ID)
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
# (시각은 지금 기준으로 — 고정 시각을 쓰면 그 시각이 지난 뒤엔 '새 수정'도 처음 만든 시각보다 옛것이 되어 시험이 틀렸다, 2026-10-01)
# 노트 틀·칸·마음·이해(2026-10-07) — 선택 칸. 값은 정해진 것만, 남은 못 읽는다
s, _ = call('POST', '/rest/v1/notes?on_conflict=id', {'id': nid, 'date': '2026-09-30', 'title': '', 'body': '질문\n왜?\n\n핵심\n그래서', 'cids': [], 'tpl': 'cornell', 'parts': ['왜?', '그래서'], 'mood': 'calm', 'grasp': 2}, N1, UP)
check('틀·칸·마음·이해를 같이 저장', s in (200, 201), s)
s, j = call('GET', f'/rest/v1/notes?id=eq.{nid}&select=tpl,parts,mood,grasp', tok=N1); check('  └ 내가 읽음', j == [{'tpl': 'cornell', 'parts': ['왜?', '그래서'], 'mood': 'calm', 'grasp': 2}], j)
s, j = call('GET', '/rest/v1/notes?select=mood,grasp,parts', tok=N2); check('  └ 다른 학생은 마음·이해·칸을 못 읽음', j == [], j)
s, j = call('GET', '/rest/v1/notes?select=mood,grasp', tok=OWN); check('  └ 원장도 마음·이해를 못 읽음', j == [], j)
for bad, why in [({'tpl': 'diary'}, '없는 틀'), ({'mood': 'angry'}, '없는 마음'), ({'grasp': 4}, '이해 4단계'), ({'parts': ['a', 'b', 'c', 'd', 'e']}, '칸 5개'),
                 ({'parts': {'a': 1}}, '칸이 목록이 아님'), ({'parts': ['a', 3]}, '칸에 글이 아닌 값'), ({'parts': ['가' * 12001]}, '칸 글이 너무 김')]:
    s, _ = call('POST', '/rest/v1/notes', {'id': str(_uuid.uuid4()), 'date': '2026-09-30', 'title': 'x', 'body': '', 'cids': [], **bad}, N1); check(f'  └ {why}이면 거절', s >= 400, s)
s, _ = call('POST', '/rest/v1/notes?on_conflict=id', {'id': nid, 'date': '2026-09-30', 'title': '비밀 메모', 'body': '나만 봄', 'cids': []}, N1, UP)
s, j = call('GET', f'/rest/v1/notes?id=eq.{nid}&select=body,tpl,parts', tok=N1); check('옛 앱처럼 새 칸 없이 올려도 됨(새 칸은 그대로 — 앱이 본문과 어긋나면 본문을 씀)', s == 200 and j and j[0]['body'] == '나만 봄' and j[0]['tpl'] == 'cornell', j)
call('PATCH', f'/rest/v1/notes?id=eq.{nid}', {'tpl': '', 'parts': [], 'mood': '', 'grasp': 0}, N1)
import datetime as _dt
_t = lambda m: (_dt.datetime.now(_dt.timezone.utc) + _dt.timedelta(minutes=m)).isoformat()
s, _ = call('POST', '/rest/v1/notes?on_conflict=id', {'id': nid, 'date': '2026-09-30', 'title': '새 제목', 'body': '나만 봄', 'cids': [], 'updated_at': _t(10)}, N1, UP)
s, _ = call('POST', '/rest/v1/notes?on_conflict=id', {'id': nid, 'date': '2026-09-30', 'title': '옛 제목', 'body': '나만 봄', 'cids': [], 'updated_at': _t(5)}, N1, UP)
s, j = call('GET', f'/rest/v1/notes?id=eq.{nid}&select=title', tok=N1); check('더 오래된 수정은 새 수정을 덮지 않음', j and j[0]['title'] == '새 제목', (s, j))
call('PATCH', f'/rest/v1/notes?id=eq.{nid}', {'title': '비밀 메모', 'updated_at': _t(20)}, N1)
# 3,000개 제한: 가득 차도 이미 있는 노트는 고칠 수 있고, 새로 넣기만 막힌다
cur.execute("insert into notes (id, uid, date, title) select gen_random_uuid(), %s, date '2026-01-01', 'bulk' from generate_series(1, 2999)", (N1_ID,)); cur.connection.commit()
s, _ = call('POST', '/rest/v1/notes?on_conflict=id', {'id': nid, 'date': '2026-09-30', 'title': '비밀 메모', 'body': '가득 차도 고침', 'cids': [], 'updated_at': _t(30)}, N1, UP); check('3,000개가 차도 기존 노트 고치기는 됨', s in (200, 201), s)
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

print('▸ 의견 보내기 · 교재 오류 신고')
FBP = 'return=minimal'
F1, F1_ID = signup('fb1@test.kr', '의견하나'); F2, F2_ID = signup('fb2@test.kr', '의견둘')
s, _ = call('POST', '/rest/v1/feedback', {'kind': 'content', 'body': '해설 단위가 틀린 것 같아요', 'ref': 'concept:1101-01', 'ver': '1.0'}, F1, FBP); check('학생이 의견 보냄', s == 201, s)
s, j = call('GET', '/rest/v1/feedback?select=uid,kind,body,care,done_at', tok=F1); check('  └ 보낸 사람은 자기 의견을 봄 · 주인은 서버가 채움', len(j) == 1 and j[0]['uid'] == F1_ID and j[0]['done_at'] is None, j)
s, j = call('GET', '/rest/v1/feedback?select=id', tok=F2); check('다른 학생은 남의 의견을 못 봄', j == [], j)
s, _ = call('POST', '/rest/v1/feedback', {'kind': 'bug', 'body': '비로그인 도배'}, None, FBP); check('로그인 안 하면 못 보냄', s in (401, 403), s)
s, _ = call('POST', '/rest/v1/feedback', {'kind': 'bug', 'body': '남인 척', 'uid': F2_ID}, F1, FBP); check('남의 이름으로 못 보냄(uid 칸 못 씀)', s >= 400, s)
s, _ = call('POST', '/rest/v1/feedback', {'kind': 'bug', 'body': '처리 표시 조작', 'done_at': '2026-01-01T00:00:00Z'}, F1, FBP); check('처리 표시를 스스로 못 넣음', s >= 400, s)
s, _ = call('POST', '/rest/v1/feedback', {'kind': 'hack', 'body': '없는 종류'}, F1, FBP); check('없는 종류는 거절', s >= 400, s)
s, _ = call('POST', '/rest/v1/feedback', {'kind': 'bug', 'body': 'x' * 1001}, F1, FBP); check('1,000자 넘으면 거절', s >= 400, s)
s, _ = call('POST', '/rest/v1/feedback', {'kind': 'bug', 'body': '링크', 'ref': 'javascript:alert(1)'}, F1, FBP); check('이상한 참조(ref)는 거절', s >= 400, s)
s, _ = call('PATCH', '/rest/v1/feedback?uid=eq.' + F1_ID, {'body': '고쳐 쓰기'}, F1); check('보낸 의견은 못 고침', s >= 400 or call('GET', '/rest/v1/feedback?select=body', tok=F1)[1][0]['body'] != '고쳐 쓰기', s)
s, _ = call('POST', '/rest/v1/feedback', {'kind': 'other', 'body': '요즘 너무 힘들어서 죽고 싶어요'}, F2, FBP)
s, j = rpc('feedback_list', {}, F2); check('학생은 받은 의견 목록을 못 받음', s == 200 and j == [], j)
s, j = rpc('feedback_list', {}, OWN); fbs = j if isinstance(j, list) else []
check('원장은 이름과 함께 받음', len(fbs) == 2 and all(x.get('name') for x in fbs), j)
check('  └ 힘든 마음이 담긴 의견은 care 표시', any(x['care'] for x in fbs if '죽고' in x['body']) and not any(x['care'] for x in fbs if '단위' in x['body']), fbs)
fid = next(x['id'] for x in fbs if '단위' in x['body'])
s, _ = rpc('feedback_done', {'p_id': fid}, F1); check('학생은 처리 표시 못 함', s >= 400, s)
rpc('feedback_done', {'p_id': fid}, OWN); check('원장이 처리함 표시', call('GET', '/rest/v1/feedback?select=done_at', tok=F1)[1][0]['done_at'] is not None)
codes = [call('POST', '/rest/v1/feedback', {'kind': 'idea', 'body': f'제안 {i}'}, F1, FBP)[0] for i in range(10)]
check('하루 10건까지(도배 제한)', codes[:9] == [201] * 9 and codes[9] >= 400, codes)
s, _ = call('POST', '/rest/v1/feedback', {'kind': 'bug', 'body': '동의 전 아이'}, K6, FBP); check('보호자 동의 전 14세 미만은 서버에 못 보냄', s >= 400, s)
cur.execute("update feedback set at = now() - interval '13 months' where uid = %s and body = '요즘 너무 힘들어서 죽고 싶어요'", (F2_ID,)); cur.execute('select private.purge_old()'); cur.connection.commit()
cur.execute("select count(*) from feedback where uid = %s", (F2_ID,)); check('1년 지난 의견은 지움', cur.fetchone()[0] == 0)
rpc('delete_my_account', {}, F1); cur.execute("select count(*) from feedback where uid = %s", (F1_ID,)); check('계정을 지우면 의견도 지워짐', cur.fetchone()[0] == 0)

print('▸ 2026-10-01 점검에서 나온 구멍')
cur.execute("update profiles set created_at = now() - interval '2 days'"); cur.connection.commit()
G1, G1_ID = signup('g1@test.kr', '일반1'); G2, G2_ID = signup('g2@test.kr', '일반2'); G3, G3_ID = signup('g3@test.kr', '일반3')
cur.execute("update profiles set created_at = now() - interval '2 days'"); cur.connection.commit(); member(G1_ID, G2_ID, G3_ID)
s, j = call('POST', '/rest/v1/posts?select=id', {'board': 'talk', 'title': '원장 안내', 'body': '안내합니다'}, OWN, 'return=representation'); spid = j[0]['id']
for t in (G1, G2, G3): rpc('report_item', {'p_kind': 'post', 'p_id': spid}, t)
s, j = call('GET', f'/rest/v1/posts?id=eq.{spid}&select=id', tok=G1); check('선생님 글은 신고로 가려지지 않음', len(j) == 1, j)
s, j = call('POST', '/rest/v1/posts?select=id', {'board': 'talk', 'title': '보통 글', 'body': '내용'}, G1, 'return=representation'); gpid = j[0]['id']
call('POST', '/rest/v1/comments', {'post_id': gpid, 'body': '댓글'}, G2)
for t in (G2, G3, OWN): rpc('report_item', {'p_kind': 'post', 'p_id': gpid}, t)
s, j = call('GET', f'/rest/v1/comments?post_id=eq.{gpid}&select=id', tok=G3); check('가려진 글의 댓글도 가려짐', j == [], j)
rpc('clear_reports', {'p_kind': 'post', 'p_id': gpid}, OWN); s, j = call('GET', f'/rest/v1/posts?id=eq.{gpid}&select=id', tok=G3); check('원장이 잘못된 신고를 되돌리면 다시 보임', len(j) == 1, j)
s, _ = rpc('clear_reports', {'p_kind': 'post', 'p_id': gpid}, G3); check('  └ 학생은 신고를 못 지움', s >= 400, s)
s, j = rpc('report_item', {'p_kind': 'post', 'p_id': gpid}, G3); cur.execute('select report_n from posts where id = %s', (gpid,))
check('  └ 되돌린 뒤 같은 학생이 다시 신고해도 다시 세지 않음(다시 가려지지 않음)', j.get('again') and j.get('checked') and cur.fetchone()[0] == 0, j)
G4, G4_ID = signup('g4@test.kr', '일반4'); cur.execute("update profiles set created_at = now() - interval '2 days' where id = %s", (G4_ID,)); cur.connection.commit()
s, j = rpc('report_item', {'p_kind': 'post', 'p_id': gpid, 'p_reason': 'bully'}, G4); check('  └ 새로 신고한 학생은 셈', j.get('n') == 1, j)
rpc('like_toggle', {'p_kind': 'post', 'p_id': gpid}, G3)
rpc('delete_my_account', {}, G4); rpc('delete_my_account', {}, G3); cur.execute('select report_n, %s = any(likes) from posts where id = %s', (G3_ID, gpid)); row = cur.fetchone()
cur.execute('select count(*) from reports where uid in (%s, %s)', (G3_ID, G4_ID)); nrep = cur.fetchone()[0]
check('탈퇴하면 남의 글에 남은 도움됨·신고도 지워짐(신고 수도 다시 맞춤)', row == (0, False) and nrep == 0, (row, nrep))
s, j = rpc('consent_ok', {'u': K6_ID}, ANON); check('남의 계정으로 동의 여부를 캐묻지 못함', s >= 400, (s, j))
s, _ = rpc('like_toggle', {'p_kind': 'post', 'p_id': gpid}, K6); cur.execute('select %s = any(likes) from posts where id = %s', (K6_ID, gpid)); check('동의 전 14세 미만은 도움됨을 못 누름', cur.fetchone()[0] is False, s)
codes = [call('POST', '/rest/v1/client_errors', {'ver': '1', 'msg': f'e{i}'}, ANON)[0] for i in range(310)]
cur.execute("select count(*) from client_errors where uid is null and at > now() - interval '1 hour'"); check('로그인 없이 넣는 오류 기록은 시간당 300건까지(DB 채우기 막기)', cur.fetchone()[0] <= 300)
s, _ = call('POST', '/rest/v1/posts', {'board': 'talk', 'title': '첨부', 'body': 'x', 'attach': {'kind': 'concept', 'id': '1101-01', 'junk': 'y' * 5000}}, G1); check('이상한 첨부(큰 덩어리)는 거절', s >= 400, s)
s, _ = call('POST', '/rest/v1/posts', {'board': 'talk', 'title': '첨부', 'body': 'x', 'attach': {'kind': 'concept', 'id': '1101-01'}}, G1); check('  └ 정상 첨부는 됨', s == 201, s)
s, _ = call('PATCH', f'/rest/v1/posts?id=eq.{gpid}', {'body': '고침', 'edited': '1999-01-01T00:00:00Z'}, G1); cur.execute('select edited from posts where id = %s', (gpid,)); e = cur.fetchone()[0]
check('수정 시각은 서버가 적음(아무 날짜 못 넣음)', e is not None and e.year >= 2026, e)
s, _ = call('POST', '/rest/v1/progress?on_conflict=code', {'code': f'u:{G1_ID}', 'state': {'x': 'y' * 600000}}, G1, 'resolution=merge-duplicates,return=minimal'); check('진도 한 덩어리는 500KB 까지', s >= 400, s)
s, _ = call('PATCH', f'/rest/v1/profiles?id=eq.{G1_ID}', {'nick': 'x' * 200}, G1); check('닉네임 12자 넘으면 거절', s >= 400, s)
for nk in ('Teacher', '쌤', '선 생 님', '관리 자', '운영진', 'ADMIN_박'):
    s, _ = call('PATCH', f'/rest/v1/profiles?id=eq.{G1_ID}', {'nick': nk}, G1)
    if s < 400: check(f'선생님 사칭 닉네임 막음: {nk}', False, s); break
else: check('선생님 사칭 닉네임(띄어쓰기·영문·쌤) 막음', True)
for i in range(8): rpc('register_push', {'p_token': f'tok-many-{i}', 'p_platform': 'android'}, G1)
cur.execute('select count(*) from push_tokens where uid = %s', (G1_ID,)); check('한 사람 푸시 기기는 5대까지', cur.fetchone()[0] == 5)
cur.execute("select count(*) from pg_proc p join pg_namespace n on n.oid = p.pronamespace where n.nspname = 'private' and has_function_privilege('authenticated', p.oid, 'execute')"); check('private 함수는 앱이 직접 못 부름(전부)', cur.fetchone()[0] == 0)

D1, D1_ID = signup('del1@test.kr', '지울사람')
call('POST', '/rest/v1/progress?on_conflict=code', {'code': f'u:{D1_ID}', 'state': {'done': [1]}}, D1, 'resolution=merge-duplicates,return=minimal')
s, j = rpc('delete_user', {'p_email': 'del1@test.kr'}, G1); check('원장 아닌 사람은 남의 계정을 못 지움', s >= 400, s)
s, j = rpc('delete_user', {'p_email': 'del1@test.kr'}, OWN); cur.execute('select count(*) from auth.users where id = %s', (D1_ID,)); n1 = cur.fetchone()[0]
cur.execute("select count(*) from progress where code = %s", (f'u:{D1_ID}',)); check('원장이 삭제 요청 계정을 지움 · 진도까지', j.get('ok') and n1 == 0 and cur.fetchone()[0] == 0, j)
s, j = rpc('delete_user', {'p_email': 'owner@parkchan.kr'}, OWN); check('  └ 원장 자기 계정은 여기서 못 지움', not j.get('ok'), j)
s, j = call('POST', '/rest/v1/progress?on_conflict=code&select=state', {'code': f'u:{G1_ID}', 'state': {'at': '1999-01-01T00:00:00.000Z', 'done': []}}, G1, 'resolution=merge-duplicates,return=representation')
check('진도 저장 시각은 서버 시계(기기 시계를 믿지 않음)', s in (200, 201) and j[0]['state']['at'] > '2026', j)
cur.execute('update posts set deleted = true where id = %s', (gpid,)); cur.connection.commit()
cur.execute("update posts set deleted_at = now() - interval '7 months' where id = %s", (gpid,)); cur.execute('select private.purge_old()'); cur.connection.commit()
cur.execute('select count(*) from posts where id = %s', (gpid,)); check('지운 글은 6개월 뒤 실제로 지움(처리방침 3③)', cur.fetchone()[0] == 0)

print('▸ 앱과 서버 규칙 맞춤(개인정보·위기어·닉네임 금지어 — 같은 문장 묶음을 양쪽에)')
import re as _re, subprocess as _sp, os as _os
_src = open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', 'app', 'app-shell.html'), encoding='utf-8').read()
_blk = _src[_src.index('/* @rules —'):_src.index('/* @rules-end */')]
SENT = ['제 번호 010-1234-5678 로 연락', '01012345678로 문자', '010 1234 5678', '011.234.5678', 'x=010123456789', '전화 02-123-4567',
        '주민번호 990101-1234567', '990101 – 2234567', '9901011234567', '학번 202612-1234',
        '메일 a.b+c@test.co.kr', '카톡 아이디: abc_123', '인스타 @hello.world', '텔레그램 id hi', '101동 1203호', '3 동 4 호실', '1동',
        '한빛중 2학년 김민수예요', '서울고등학교 1학년 3반 박지훈', '중학교 2학년 때 배운 것', '고 1학년 수학', '대한초 6학년 이서',
        '죽고 싶다', '세포 자살(아폽토시스)', '세포의 자살', '자살 예방 포스터', '자살률 통계', '유서 깊은 실험', '유서를 썼어', '자해하고 싶어',
        '시험 망해서 뒤지고 싶다', '서랍을 뒤져 보니', '이번엔 진짜 죽어야겠다', '배고파 죽겠다', '태어나지 말았어야 했어', '살 의미가 없어', '살기 싫어', '그만 살고 싶어',
        '수학쌤', '선 생 님', 'ADMIN_박', 'Teacher', '운영진', '과학러버', '원장', '관리', 'staff1', '물리하는가', '매니저', 'o.f.f.i.c.i.a.l']
# 욕설·비하(docs/11 §12-14): 0 = 그냥 · 1 = 한 번 더 묻기 · 2 = 서버도 거절. 과학 용어·일상어 오탐을 함께 본다
ABUSE = {'아 씨발 망했다': 1, 'ㅅㅂ 진짜': 1, '병신같이': 1, '존나 어렵다': 1, '개새끼': 1, '지랄하네': 1, '미친놈아': 1, '닥쳐': 1, '등신아': 1, '찐따': 1, '급식충': 1, 'Fuck this': 1, 'WTF': 1, '썅': 1,
         '느금마': 2, '느 금 마': 2, '니애미': 2, '니.애.미': 2, '좆같네': 2, '씹새끼': 2, '애미 없는': 2, '엠창': 2,
         '벡터의 시발점': 0, '시발역에서 출발': 0, '수박 씨 발라 먹기': 0, '음식을 씹어 먹으면 소화가 잘 된다': 0, '미친 듯이 공부했다': 0, '위기가 닥쳐온다': 0, '닥쳐올 시험': 0,
         '등신대 판넬': 0, '전기 애자는 절연체': 0, '기생충과 곤충': 0, '고자질하지 마': 0, '보지 못했다': 0, '잠을 자지 못했다': 0, '허리띠를 졸라 맨다': 0, '보존나무': 0,
         '개의 새끼는 강아지': 0, '살이 찐다': 0, '호모 사피엔스': 0, '자위권': 0, '시발점탐험': 0, 'shift 키': 0, '니 엄마가 부르셔': 0}
SENT += list(ABUSE)
_js = _blk + "\nconst out = " + json.dumps(SENT, ensure_ascii=False) + ".map(t => ({ k: PII.filter(([re]) => re.test(t)).map(x => x[3]), c: careCheck(t), n: nickBad(t), m: piiMask(t), a: abuseLevel(t) }));\nprocess.stdout.write(JSON.stringify(out));"
_app = json.loads(_sp.run(['node', '-e', _js], capture_output=True, text=True, check=True).stdout)
_bad = []
for t, a in zip(SENT, _app):
    cur.execute('select private.pii_kinds(%s), private.care_hit(%s), private.nick_bad(%s), private.pii_mask(%s), private.abuse_level(%s)', (t, t, t, t, t)); k, c, n, m, ab = cur.fetchone()
    if (list(k), c, n, m, ab) != (a['k'], a['c'], a['n'], a['m'], a['a']): _bad.append((t, a, (k, c, n, m, ab)))
check(f'같은 {len(SENT)}문장에서 앱(PII·CARE_RE·NICK_BAN·가림·욕설)과 서버 판정이 같음', not _bad, _bad[:3])
_ab = {t: x['a'] for t, x in zip(SENT, _app)}; _miss = [(t, _ab[t], v) for t, v in ABUSE.items() if _ab[t] != v]
check(f'  └ 욕설 {sum(1 for v in ABUSE.values() if v)}문장은 걸리고(아주 심한 욕은 띄어 써도 2), 과학 용어·일상어 {sum(1 for v in ABUSE.values() if not v)}문장은 안 걸림', not _miss, _miss)
_by = dict(zip(SENT, _app))
check('  └ 은어(뒤지고 싶·죽어야겠·태어나지 말았·살 의미가 없)는 걸리고, 뒤져 보니·죽겠다·세포 자살은 안 걸림',
      all(_by[t]['c'] for t in ('시험 망해서 뒤지고 싶다', '이번엔 진짜 죽어야겠다', '태어나지 말았어야 했어', '살 의미가 없어'))
      and not any(_by[t]['c'] for t in ('서랍을 뒤져 보니', '배고파 죽겠다', '세포 자살(아폽토시스)', '자살 예방 포스터', '유서 깊은 실험')))
check("  └ '○○중 2학년 김○○'은 걸리고 '중학교 2학년 때'는 안 걸림", 'school' in _by['한빛중 2학년 김민수예요']['k'] and 'school' not in _by['중학교 2학년 때 배운 것']['k'])
check('  └ 휴대전화는 010-****-5678 모양으로', _by['제 번호 010-1234-5678 로 연락']['m'] == '제 번호 010-****-5678 로 연락' and _by['01012345678로 문자']['m'] == '010-****-5678로 문자')

print('▸ 개인정보 — 서버가 직접 검사(앱을 거치지 않은 글도)')
T1, T1_ID = signup('t1@test.kr', '이야기1'); T2, T2_ID = signup('t2@test.kr', '이야기2'); T3, T3_ID = signup('t3@test.kr', '손님')
cur.execute("update profiles set created_at = now() - interval '2 days' where id in (%s, %s, %s)", (T1_ID, T2_ID, T3_ID)); cur.connection.commit(); member(T1_ID, T2_ID)
s, j = call('POST', '/rest/v1/posts?select=id,body', {'board': 'talk', 'title': '안녕', 'body': '주민번호 990101-1234567'}, T1, 'return=representation')
check('주민등록번호가 든 글은 서버가 거절', s >= 400 and '주민등록번호' in str(j), (s, j))
s, j = call('POST', '/rest/v1/posts?select=id,title,body', {'board': 'talk', 'title': '연락 01099998888', 'body': '문자 010-1234-5678 주세요'}, T1, 'return=representation')
check('휴대전화는 가운데를 가려 저장(제목·본문)', s == 201 and j[0]['body'] == '문자 010-****-5678 주세요' and j[0]['title'] == '연락 010-****-8888', j)
tpid = j[0]['id']
s, j = call('PATCH', f'/rest/v1/posts?id=eq.{tpid}&select=body', {'body': '고침 010 5555 6666'}, T1, 'return=representation'); check('  └ 고쳐 쓸 때도 가림', s == 200 and j[0]['body'] == '고침 010-****-6666', j)
s, j = call('POST', '/rest/v1/comments?select=body', {'post_id': tpid, 'body': '제 번호는 01011112222 예요'}, T2, 'return=representation'); check('  └ 댓글도 가림', s == 201 and j[0]['body'] == '제 번호는 010-****-2222 예요', j)
s, j = call('POST', '/rest/v1/comments', {'post_id': tpid, 'body': '990101-2234567'}, T2); check('  └ 댓글의 주민등록번호도 거절', s >= 400, s)
s, j = call('POST', '/rest/v1/posts?select=body', {'board': 'talk', 'title': '학원 안내', 'body': '학원 전화 010-2222-3333'}, OWN, 'return=representation'); check('  └ 원장 글(학원 연락처)은 그대로', j[0]['body'] == '학원 전화 010-2222-3333', j)
s, _ = call('PATCH', f'/rest/v1/profiles?id=eq.{T1_ID}', {'nick': '한빛중2학년김민수'}, T1); check('닉네임에 학교·학년·이름은 서버가 거절', s >= 400, s)
s, _ = call('PATCH', f'/rest/v1/profiles?id=eq.{T1_ID}', {'nick': '0101234567'}, T1); s2, _ = call('PATCH', f'/rest/v1/profiles?id=eq.{T1_ID}', {'nick': '과학러버'}, T1)
check('  └ 닉네임 전화번호 거절 · 보통 닉네임은 됨', s >= 400 and s2 == 204, (s, s2))

print('▸ 이야기 쓰기 권한 — 학원생·이용권 학생만(보호자·손님은 읽기만)')
s, j = call('POST', '/rest/v1/posts', {'board': 'talk', 'title': '손님', 'body': '코드도 이용권도 없음'}, T3); check('코드·이용권 없는 학생은 글 못 씀', s == 403 and '학원 코드나 이용권' in str(j), (s, j))
s, j = call('POST', '/rest/v1/comments', {'post_id': tpid, 'body': '손님 댓글'}, T3); check('  └ 댓글도 못 씀', s == 403, s)
s, j = call('GET', f'/rest/v1/posts?id=eq.{tpid}&select=id', tok=T3); check('  └ 읽기는 됨', len(j) == 1, j)
s, j = rpc('my_talk', {}, T3); check('  └ 내 상태: member', j['block'] == 'member' and not j['ok'], j)
s, j = rpc('my_talk', {}, P); check('보호자 계정 상태: parent(읽기만)', j['block'] == 'parent', j)
s, _ = rpc('like_toggle', {'p_kind': 'post', 'p_id': tpid}, P); cur.execute('select %s = any(likes) from posts where id = %s', (P_ID, tpid)); check('  └ 보호자는 도움됨도 못 누름', cur.fetchone()[0] is False and s >= 400, s)
rpc('link_code', {'p_kind': 'student', 'p_code': 'MON123'}, A); s, j = rpc('my_talk', {}, A); check('학원 코드(수강 중) 학생은 씀', j['ok'], j)
s, j = rpc('my_talk', {}, OWN); check('원장은 씀', j['ok'], j)

print('▸ 이야기 이용 제한(7일 · 30일 · 중지 · 풀기) — 원장만, 서버가 막음')
s, j = rpc('talk_limit', {'p_uid': T2_ID, 'p_days': 7}, T1); check('학생은 남을 제한하지 못함', s >= 400, (s, j))
s, j = rpc('talk_limits', {}, T1); check('  └ 학생은 제한 목록을 못 받음', j == {'active': [], 'log': [], 'guard': []}, j)
s, j = rpc('talk_limit', {'p_uid': OWN_ID, 'p_days': 7}, OWN); check('원장 계정은 제한할 수 없음', not j['ok'] and '원장' in j['why'], j)
s, j = rpc('talk_limit', {'p_uid': T2_ID, 'p_days': 3}, OWN); check('7·30·중지·풀기 말고는 거절', not j['ok'], j)
s, j = rpc('talk_limit', {'p_uid': T2_ID, 'p_days': 7, 'p_reason': '친구를 놀렸어요', 'p_memo': '비방 2건 · 통화함'}, OWN)
kst = dt.datetime.now(ZoneInfo('Asia/Seoul')).date()
check('원장이 7일 제한 → 한국 날짜 +7일까지', j['ok'] and j['until'] == str(kst + dt.timedelta(days=7)), j)
s, j = call('POST', '/rest/v1/posts', {'board': 'talk', 'title': '제한중', 'body': '써 봅니다'}, T2); check('제한 중 글쓰기 거절(남은 기간 안내)', s == 403 and '쉬는 중' in str(j), (s, j))
s, j = call('POST', '/rest/v1/comments', {'post_id': tpid, 'body': '제한 중 댓글'}, T2); check('  └ 댓글 거절', s == 403, s)
s, _ = rpc('like_toggle', {'p_kind': 'post', 'p_id': tpid}, T2); check('  └ 도움됨 거절', s >= 400, s)
cur.execute("select id from comments where author = %s limit 1", (T2_ID,)); t2c = cur.fetchone()[0]
s, j = rpc('delete_item', {'p_kind': 'comment', 'p_id': t2c}, T2); cur.execute('select deleted from comments where id = %s', (t2c,)); check('  └ 자기 댓글 지우기는 됨', j is True and cur.fetchone()[0] is True, (s, j))
s, j = rpc('report_item', {'p_kind': 'post', 'p_id': tpid, 'p_reason': 'worry'}, T2); check('  └ 제한 중에도 신고(걱정돼요)는 됨', j.get('ok'), j)
s, j = rpc('my_talk', {}, T2); check('학생에게 보이는 상태: 기간·사유·이의 제기 기한(7일)', j['block'] == 'limit' and j['until'] == str(kst + dt.timedelta(days=7)) and j['reason'] == '친구를 놀렸어요' and j['appeal_until'] == str(kst + dt.timedelta(days=7)) and j['guardian'] is False, j)
s, j = call('GET', f'/rest/v1/profiles?id=eq.{T2_ID}&select=talk_until', tok=T2); s2, _ = call('PATCH', f'/rest/v1/profiles?id=eq.{T2_ID}', {'talk_until': None}, T2)
check('  └ 학생이 자기 제한을 못 지움', s2 in (401, 403), s2)
s, j = call('POST', '/rest/v1/feedback', {'kind': 'other', 'body': '다시 살펴봐 주세요', 'ref': 'talk:appeal'}, T2); check('  └ 이의 제기(의견 보내기 talk:appeal)는 됨', s == 201, (s, j))
s, j = rpc('talk_limits', {}, OWN); a = [x for x in j['active'] if x['uid'] == T2_ID]
check('원장은 제한 중 목록(사유·메모)과 기록을 봄', a and a[0]['reason'] == '친구를 놀렸어요' and a[0]['memo'] == '비방 2건 · 통화함' and j['log'][0]['action'] == 'd7' and j['log'][0]['uid'] == T2_ID, j)
s, j = rpc('talk_limit', {'p_uid': None, 'p_days': -1, 'p_reason': '보호자가 요청했어요', 'p_guardian': True, 'p_code': 'mon123'}, OWN)
s2, j2 = rpc('my_talk', {}, A); check('학원 코드로 중지(보호자 요청) → 이의 제기 대신 보호자', j['ok'] and j2['block'] == 'limit' and j2['until'] == 'stop' and j2['guardian'] is True and '멈춰' in j2['msg'], (j, j2))
s, j = call('POST', '/rest/v1/posts', {'board': 'talk', 'title': '중지', 'body': '써 봅니다'}, A); check('  └ 중지된 학생 글쓰기 거절', s == 403, s)
t1p = call('POST', '/rest/v1/posts?select=id', {'board': 'talk', 'title': '고칠 글', 'body': '제한 전에 쓴 글'}, T1, 'return=representation')[1][0]['id']   # 뒤 시험이 쓰는 tpid 와 다른 글
rpc('talk_limit', {'p_uid': T1_ID, 'p_days': 30}, OWN)
s, _ = call('PATCH', f'/rest/v1/posts?id=eq.{t1p}', {'body': '제한 중에 몰래 고침'}, T1); cur.execute('select body from posts where id = %s', (t1p,)); check('제한 중에는 자기 글을 고치지도 못함', s >= 400 and cur.fetchone()[0] != '제한 중에 몰래 고침', s)
s, j = rpc('delete_item', {'p_kind': 'post', 'p_id': t1p}, T1); cur.execute('select deleted from posts where id = %s', (t1p,)); check('  └ 지우기는 됨', cur.fetchone()[0] is True, (s, j))
s, j = rpc('delete_item', {'p_kind': 'post', 'p_id': tpid}, T2); cur.execute('select deleted from posts where id = %s', (tpid,)); check('  └ 남의 글은 못 지움', j is False and cur.fetchone()[0] is False, (s, j))
for u in (T1_ID, T2_ID, A_ID): rpc('talk_limit', {'p_uid': u, 'p_days': 0}, OWN)
s, j = call('POST', '/rest/v1/posts?select=id', {'board': 'talk', 'title': '풀림', 'body': '다시 씁니다'}, T2, 'return=representation'); check('풀면 다시 씀', s == 201, (s, j))
cur.execute("select count(*) from talk_log where uid in (%s, %s, %s) and action in ('d7','d30','stop','lift') and actor = %s", (T1_ID, T2_ID, A_ID, OWN_ID)); check('  └ 걸기·풀기가 모두 기록됨(6건 · 한 사람은 원장)', cur.fetchone()[0] == 6)

print("▸ 신고 사유 · '친구가 걱정돼요' · 신고한 학생에게 결과")
s, j = rpc('report_item', {'p_kind': 'post', 'p_id': tpid, 'p_reason': 'spam!'}, T3); check('없는 사유는 거절', s >= 400, s)
N1, N1x = signup('new1@test.kr', '새학생')
s, j = rpc('report_item', {'p_kind': 'post', 'p_id': tpid, 'p_reason': 'bully'}, N1); check('가입 첫날은 보통 신고 못 함', s >= 400 and '하루' in str(j), (s, j))
s, j = rpc('report_item', {'p_kind': 'post', 'p_id': tpid, 'p_reason': 'worry'}, N1); check("  └ '걱정돼요'는 첫날에도 됨", j.get('ok') and j.get('worry'), j)
cur.execute('select report_n from posts where id = %s', (tpid,)); check("'걱정돼요'는 가림 수에 안 들어감(글은 그대로)", cur.fetchone()[0] == 0)
s, j = rpc('care_list', {}, OWN); w = [x for x in j if x['id'] == tpid]; check("  └ 1건이어도 원장 '먼저 살펴볼 글'(쓴 사람 이름과)", w and w[0]['worry'] == 2 and w[0]['name'] == '이야기1', j)
s, j = rpc('care_list', {}, T1); check('  └ 학생은 이 목록을 못 받음', j == [], j)
for t in (T3, P): rpc('report_item', {'p_kind': 'post', 'p_id': tpid, 'p_reason': 'privacy'}, t)
s, j = rpc('report_item', {'p_kind': 'post', 'p_id': tpid, 'p_reason': 'ad'}, OWN)
s, j = rpc('reported_list', {}, OWN); r = [x for x in j if x['id'] == tpid]; check('원장 목록에 사유별 건수', r and r[0]['reasons'] == {'privacy': 2, 'ad': 1} and r[0]['report_n'] == 3, j)
s, j = rpc('reported_list', {}, T1); check('  └ 학생은 신고 목록을 못 받음', j == [], j)
s, j = call('GET', '/rest/v1/reports?select=*', tok=T1); check('신고 표는 API 로 안 보임(누가 신고했는지)', s >= 400 or j == [], (s, j))
s, j = call('GET', f'/rest/v1/posts?id=eq.{tpid}&select=id', tok=T2); check('보통 신고 3건 → 가림', j == [], j)
rpc('care_done', {'p_kind': 'post', 'p_id': tpid}, OWN); rpc('clear_reports', {'p_kind': 'post', 'p_id': tpid}, OWN)
s, j = call('GET', f'/rest/v1/posts?id=eq.{tpid}&select=id', tok=T2); check('되돌리면 다시 보임', len(j) == 1, j)
s, j = rpc('my_reports', {}, T3); check('신고한 학생에게 결과(그대로 둠) — 글 내용은 없이', len(j) == 1 and j[0]['state'] == 'kept' and j[0]['reason'] == 'privacy' and 'body' not in j[0], j)
s, j = rpc('my_reports', {}, N1); check("  └ '걱정돼요'를 알린 학생에게도(원장님이 살펴봄)", len(j) == 1 and j[0]['reason'] == 'worry' and j[0]['state'] == 'kept', j)
rpc('my_reports_seen', {}, T3); s, j = rpc('my_reports', {}, T3); check('  └ 확인하면 다시 안 뜸', j == [], j)
for t in (T3, P, OWN): rpc('report_item', {'p_kind': 'post', 'p_id': tpid, 'p_reason': 'privacy'}, t)
cur.execute('select report_n from posts where id = %s', (tpid,)); check('되돌린 뒤 같은 학생들이 다시 눌러도 다시 가려지지 않음', cur.fetchone()[0] == 0)
c2 = call('POST', '/rest/v1/comments?select=id', {'post_id': tpid, 'body': '지워질 댓글'}, T1, 'return=representation')[1][0]['id']
rpc('report_item', {'p_kind': 'comment', 'p_id': c2, 'p_reason': 'bully'}, T2); call('PATCH', f'/rest/v1/comments?id=eq.{c2}', {'deleted': True}, OWN)
s, j = rpc('my_reports', {}, T2); check('원장이 지우면 신고한 학생에게 "지움"', any(x['state'] == 'removed' and x['kind'] == 'comment' for x in j), j)

print('▸ 보관 기간 — 처리 끝난 신고·제한 기록 6개월 · 끝난 제한 사유 · 밤 알림 2일')
cur.execute("update reports set resolved_at = now() - interval '7 months' where post_id = %s and state <> 'open'", (tpid,))
cur.execute("insert into reports (post_id, uid, reason, at) values (%s, %s, 'other', now() - interval '8 months') on conflict do nothing", (t1p, T3_ID))
cur.execute("update talk_log set at = now() - interval '7 months' where uid = %s", (T1_ID,))
cur.execute("update profiles set talk_until = current_date - 1, talk_reason = '지난 사유' where id = %s", (T3_ID,))
cur.execute("insert into push_later (uid, post_id, at) values (%s, %s, now() - interval '3 days'), (%s, %s, now())", (T1_ID, tpid, T2_ID, tpid))
cur.execute('select private.purge_old()'); cur.connection.commit()
cur.execute("select count(*) from reports where post_id = %s and state <> 'open'", (tpid,)); n_done = cur.fetchone()[0]
cur.execute("select count(*) from reports where post_id = %s and state = 'open'", (t1p,)); n_open = cur.fetchone()[0]
check('처리 끝난 신고는 6개월 뒤 파기 · 열린 신고는 남김', n_done == 0 and n_open == 1, (n_done, n_open))
cur.execute("select count(*) from talk_log where uid = %s", (T1_ID,)); a1 = cur.fetchone()[0]; cur.execute("select count(*) from talk_log where uid = %s", (T2_ID,))
check('이용 제한 기록 6개월 뒤 파기(최근 것은 남김)', a1 == 0 and cur.fetchone()[0] == 2)
cur.execute("select talk_until, talk_reason from profiles where id = %s", (T3_ID,)); check('끝난 제한은 사유까지 지움', cur.fetchone() == (None, ''))
cur.execute("select uid from push_later"); check('보내지 못한 밤 알림은 2일 뒤 지움', [r[0] for r in cur.fetchall()] == [T2_ID])
rpc('delete_my_account', {}, T2); cur.execute("select (select count(*) from talk_log where uid = %s) + (select count(*) from reports where uid = %s) + (select count(*) from push_later where uid = %s)", (T2_ID, T2_ID, T2_ID))
check('탈퇴하면 제한 기록·신고·밤 알림도 함께 지움', cur.fetchone()[0] == 0)


def ago(sql_interval, table, idv, col='at'):
    cur.execute(f"update {table} set {col} = now() - interval '{sql_interval}' where id = %s", (idv,)); cur.connection.commit()
def pass_only(*uids):   # 이용권만(첫 글 검토는 아직)
    for u in uids: cur.execute("update profiles set pass_until = current_date + 30, created_at = now() - interval '2 days' where id = %s", (u,))
    cur.connection.commit()
def mkpost(tok, uid, title, body, board='talk'):   # 도배 제한(10분에 5개)에 걸리지 않게 그 사람의 최근 글 시각을 11분 앞으로
    cur.execute("update posts set at = at - interval '11 minutes' where author = %s and at > now() - interval '10 minutes'", (uid,)); cur.connection.commit()
    s_, j_ = call('POST', '/rest/v1/posts?select=id,review', {'board': board, 'title': title, 'body': body}, tok, 'return=representation')
    assert s_ == 201, (s_, j_); return j_[0]['id']
def get_post(pid, tok): return call('GET', f'/rest/v1/posts?id=eq.{pid}&select=id,review,review_why,likes,report_n', tok=tok)[1]

print('▸ 첫 글 사전 검토(docs/11 §12-6) — 학생 첫 글은 쓴 사람·원장만 · 원장 승인 뒤 공개 · 댓글은 바로')
R1, R1_ID = signup('r1@test.kr', '새학생'); R2, R2_ID = signup('r2@test.kr', '헌학생'); R3, R3_ID = signup('r3@test.kr', '댓글학생')
RP, RP_ID = signup('rp@test.kr', '읽는보호자', role='parent'); RG, RG_ID = signup('rg@test.kr', '손님학생')
pass_only(R1_ID, R2_ID, R3_ID); member(R2_ID)
s, j = rpc('my_talk', {}, R1); check('새 학생: 다음 글이 첫 글 검토를 거친다고 앎(review)', j.get('ok') and j.get('review') is True, j)
s, j = rpc('my_talk', {}, R2); check('  └ 첫 글을 지난 학생은 review 아님', j.get('review') is False, j)
s, j = call('POST', '/rest/v1/posts?select=id,review', {'board': 'qna', 'title': '첫 질문', 'body': '반응 속도 질문입니다'}, R1, 'return=representation')
check('새 학생 첫 글은 "검토 중"으로 올라감(쓴 사람은 봄)', s == 201 and j[0]['review'] == 'wait', (s, j)); fp1 = j[0]['id']
for nm, t in (('첫 글 검토를 지난 학생', R2), ('보호자', RP), ('손님', RG)):
    check(f'  └ {nm}에게는 안 보임', get_post(fp1, t) == [])
s, j = call('GET', f'/rest/v1/posts?id=eq.{fp1}&select=id', tok=ANON); check('  └ 로그인 안 한 사람에게도 안 보임', s >= 400 or j == [], j)
s, j = call('GET', f'/rest/v1/posts?id=eq.{fp1}&select=review', tok=OWN); check('  └ 원장은 봄', len(j) == 1, j)
s, j = call('POST', '/rest/v1/comments', {'post_id': fp1, 'body': '검토 중인 글에 댓글'}, R2); check('  └ 남이 검토 중인 글에 댓글을 못 닮', s >= 400, s)
rpc('like_toggle', {'p_kind': 'post', 'p_id': fp1}, R2); cur.execute('select %s = any(likes) from posts where id = %s', (R2_ID, fp1)); check('  └ 도움됨도 못 누름', cur.fetchone()[0] is False)
s, j = rpc('report_item', {'p_kind': 'post', 'p_id': fp1, 'p_reason': 'ad'}, R2); check('  └ 신고도 못 함(없는 글)', j.get('ok') is False, j)
s, _ = call('PATCH', f'/rest/v1/posts?id=eq.{fp1}', {'review': None}, R1); cur.execute('select review from posts where id = %s', (fp1,)); check('쓴 학생이 검토 표시를 스스로 못 지움', s >= 400 and cur.fetchone()[0] == 'wait', s)
s, _ = call('POST', '/rest/v1/posts', {'board': 'qna', 'title': '검토 건너뛰기', 'body': '검토 칸을 직접 넣기', 'review': None}, R1); check('  └ 올릴 때 검토 칸을 직접 못 넣음', s >= 400, s)
s, j = call('POST', '/rest/v1/posts?select=id,review', {'board': 'talk', 'title': '두 번째 글', 'body': '승인 전에 또 씁니다'}, R1, 'return=representation'); fp2 = j[0]['id']
check('  └ 승인 전 두 번째 글도 검토 중', j[0]['review'] == 'wait', j)
for nm, t in (('학생', R2), ('보호자', RP), ('손님', RG)):
    s, j = rpc('review_list', {}, t); check(f'{nm}은 검토할 글 목록을 못 받음', s == 200 and j == [], j)
s, j = rpc('review_list', {}, OWN); w = [x for x in j if x['uid'] == R1_ID]
check('원장은 검토할 글을 이름·학원 코드와 함께 받음(2건)', len(w) == 2 and w[0]['name'] == '새학생' and w[0]['title'] == '첫 질문', j)
for nm, t in (('학생', R2), ('글쓴 학생', R1), ('보호자', RP), ('손님', RG), ('비로그인', ANON)):
    s, _ = rpc('review_post', {'p_id': fp1, 'p_ok': True}, t); check(f'  └ {nm}은 승인 못 함', s >= 400, s)
cur.execute('select review from posts where id = %s', (fp1,)); check('  └ (아직 검토 중)', cur.fetchone()[0] == 'wait')
s, j = rpc('review_post', {'p_id': fp2, 'p_ok': False, 'p_why': '공부와 상관없는 글이에요'}, OWN); check('원장이 공개하지 않음(사유)', j.get('ok'), j)
g = get_post(fp2, R1); check('  └ 쓴 학생은 사유를 봄', g and g[0]['review'] == 'no' and g[0]['review_why'] == '공부와 상관없는 글이에요', g)
check('  └ 남에게는 여전히 안 보임', get_post(fp2, R2) == [])
s, j = call('PATCH', f'/rest/v1/posts?id=eq.{fp2}&select=review', {'body': '공부 질문으로 고쳤어요'}, R1, 'return=representation'); check('  └ 고쳐 쓰면 다시 검토 중으로', s == 200 and j[0]['review'] == 'wait', (s, j))
s, j = rpc('review_post', {'p_id': fp1, 'p_ok': True}, OWN); check('원장이 첫 글 승인', j.get('ok'), j)
check('  └ 이제 다른 학생에게 보임', len(get_post(fp1, R2)) == 1 and len(get_post(fp1, RG)) == 1)
s, j = rpc('review_post', {'p_id': fp1, 'p_ok': False}, OWN); check('  └ 이미 처리한 글은 다시 처리 안 됨', j.get('ok') is False, j)
s, j = call('POST', '/rest/v1/posts?select=id,review', {'board': 'qna', 'title': '승인 뒤 글', 'body': '이제 바로 보이나요'}, R1, 'return=representation'); fp3 = j[0]['id']
check('승인 뒤 새 글은 바로 공개', j[0]['review'] is None and len(get_post(fp3, R2)) == 1, j)
check('  └ 남은 검토 중 글은 그대로 검토 대기', any(x['id'] == fp2 for x in rpc('review_list', {}, OWN)[1]))
s, j = call('POST', '/rest/v1/comments?select=id', {'post_id': fp3, 'body': '첫 댓글도 바로 보여요'}, R3, 'return=representation'); rc1 = j[0]['id'] if s == 201 else None
s2, j2 = call('GET', f'/rest/v1/comments?id=eq.{rc1}&select=id', tok=R2); check('새 학생 댓글은 검토 없이 바로 공개', s == 201 and len(j2) == 1, (s, j2))
s, j = call('POST', '/rest/v1/posts?select=review', {'board': 'talk', 'title': '원장 글', 'body': '원장 글은 검토 없음'}, OWN, 'return=representation'); check('원장 글은 검토 없음', j[0]['review'] is None, j)
cur.execute("select action, actor from talk_log where uid = %s and action in ('approve','reject') order by at", (R1_ID,)); rows = cur.fetchall()
check('처리 기록: 공개하지 않음 · 승인(누가 했는지까지)', [r[0] for r in rows] == ['reject', 'approve'] and all(r[1] == OWN_ID for r in rows), rows)

print('▸ 선생님 확인 답변(docs/11 §12-7) · 답이 없는 질문(48시간)')
cur.execute('update profiles set first_ok_at = now() where id = %s', (R3_ID,)); cur.connection.commit()   # 아래는 첫 글을 지난 학생으로
q1 = mkpost(R2, R2_ID, '확인받을 질문', '전자기 유도 질문', 'qna')
c1 = call('POST', '/rest/v1/comments?select=id', {'post_id': q1, 'body': '자석을 움직이면 유도 전류가 흘러요'}, R3, 'return=representation')[1][0]['id']
c0 = call('POST', '/rest/v1/comments?select=id', {'post_id': q1, 'body': '먼저 단 다른 답'}, R1, 'return=representation')[1][0]['id']
for nm, t in (('학생', R2), ('댓글 쓴 학생', R3), ('보호자', RP), ('손님', RG), ('비로그인', ANON)):
    s, _ = rpc('check_comment', {'p_id': c1, 'p_on': True}, t); check(f'{nm}은 선생님 확인을 못 닮', s >= 400, s)
s, _ = call('PATCH', f'/rest/v1/comments?id=eq.{c1}', {'checked': True}, R3); check('  └ checked 칸을 직접 못 고침', s >= 400, s)
cur.execute('select checked from comments where id = %s', (c1,)); check('  └ (아직 확인 안 됨)', cur.fetchone()[0] is False)
s, j = rpc('check_comment', {'p_id': c1, 'p_on': True}, OWN); check('원장이 선생님 확인', j.get('ok') and j.get('checked'), j)
s, j = call('GET', f'/rest/v1/comments?post_id=eq.{q1}&select=id,checked,picked', tok=R2); check('  └ 학생에게 checked 로 보임(채택과 따로)', any(x['id'] == c1 and x['checked'] and not x['picked'] for x in j), j)
sc = call('POST', '/rest/v1/comments?select=id', {'post_id': q1, 'body': '선생님 댓글'}, OWN, 'return=representation')[1][0]['id']
s, j = rpc('check_comment', {'p_id': sc, 'p_on': True}, OWN); check('  └ 선생님 댓글에는 따로 달지 않음', j.get('ok') is False, j)
rpc('check_comment', {'p_id': c1, 'p_on': False}, OWN); rpc('check_comment', {'p_id': c1, 'p_on': True}, OWN)
cur.execute("select action from talk_log where target = %s order by at", (f'comment:{c1}',)); check('  └ 처리 기록: 확인·풀기·확인', [r[0] for r in cur.fetchall()] == ['check', 'uncheck', 'check'])
u_old = mkpost(R2, R2_ID, '답 없는 옛 질문', '사흘째 답이 없어요', 'qna')
u_self = mkpost(R2, R2_ID, '혼자 단 댓글', '내가 덧붙임', 'qna')
call('POST', '/rest/v1/comments', {'post_id': u_self, 'body': '덧붙입니다'}, R2)
u_ans = mkpost(R2, R2_ID, '답 달린 질문', '답이 있어요', 'qna')
call('POST', '/rest/v1/comments', {'post_id': u_ans, 'body': '답'}, R3)
u_new = mkpost(R2, R2_ID, '방금 질문', '하루도 안 됨', 'qna')
u_talk = mkpost(R2, R2_ID, '잡담', '질문 아님', 'talk')
for x in (u_old, u_self, u_ans, u_talk): ago('3 days', 'posts', x)
s, j = rpc('unanswered_list', {}, OWN); ids = {x['id'] for x in j}
check('원장: 48시간 지난 답 없는 질문(글쓴이 댓글만 있어도 포함)', u_old in ids and u_self in ids, j)
check('  └ 남이 답한 질문 · 48시간 안 · 잡담 게시판은 뺌', not ids & {u_ans, u_new, u_talk}, ids)
for nm, t in (('학생', R2), ('보호자', RP), ('손님', RG)):
    s, j = rpc('unanswered_list', {}, t); check(f'  └ {nm}은 못 받음', s == 200 and j == [], j)

print('▸ 신고 남용 — 되돌려진 신고가 30일에 3번인 계정의 신고는 가림 수에 안 들어감(docs/11 §12-8)')
M, M_ID = signup('m@test.kr', '자주신고'); V1, V1_ID = signup('v1@test.kr', '신고1'); V2, V2_ID = signup('v2@test.kr', '신고2')
member(M_ID, V1_ID, V2_ID); cur.execute("update profiles set created_at = now() - interval '2 days' where id in (%s, %s, %s)", (M_ID, V1_ID, V2_ID)); cur.connection.commit()
tgt = [mkpost(R2, R2_ID, f'멀쩡한 글{i}', '문제 없는 글', 'talk') for i in range(3)]
py = mkpost(R3, R3_ID, '먼저 신고된 글', '신고 대상', 'talk')
for t in tgt[:2]: rpc('report_item', {'p_kind': 'post', 'p_id': t, 'p_reason': 'bully'}, M); rpc('clear_reports', {'p_kind': 'post', 'p_id': t}, OWN)
for tk in (M, V1, V2): rpc('report_item', {'p_kind': 'post', 'p_id': py, 'p_reason': 'bully'}, tk)
check('  (되돌림 2번까지는 그대로 셈 — 3건이면 가림)', get_post(py, R2) == [])
rpc('report_item', {'p_kind': 'post', 'p_id': tgt[2], 'p_reason': 'bully'}, M); rpc('clear_reports', {'p_kind': 'post', 'p_id': tgt[2]}, OWN)
cur.execute('select report_n from posts where id = %s', (py,)); check('세 번째 되돌림 뒤 그 계정의 다른 열린 신고도 가림 수에서 빠짐(3 → 2, 다시 보임)', cur.fetchone()[0] == 2 and len(get_post(py, R2)) == 1)
px = mkpost(R3, R3_ID, '새 글', '새로 신고될 글', 'talk')
for tk in (M, V1, V2): rpc('report_item', {'p_kind': 'post', 'p_id': px, 'p_reason': 'privacy'}, tk)
cur.execute('select report_n from posts where id = %s', (px,)); check('  └ 새 신고도 가림 수에 안 들어감(3명 신고 → 2, 가려지지 않음)', cur.fetchone()[0] == 2 and len(get_post(px, R2)) == 1)
s, j = rpc('reported_list', {}, OWN); r = [x for x in j if x['id'] == px]; check('  └ 원장 목록에는 남음(신고 3 · 그중 되돌림 많은 계정 1)', r and r[0]['muted'] == 1 and r[0]['reasons'] == {'privacy': 3}, r)
s, j = rpc('muted_reporters', {}, OWN); mm = [x for x in j if x['uid'] == M_ID]; check('원장에게 "신고가 자주 되돌려진 계정" 표시(이름·되돌림 3)', mm and mm[0]['kept'] == 3 and mm[0]['name'] == '자주신고', j)
for nm, t in (('학생', V1), ('보호자', RP), ('신고한 본인', M)):
    s, j = rpc('muted_reporters', {}, t); check(f'  └ {nm}은 못 받음', s == 200 and j == [], j)
cur.execute("select count(*) from talk_log where action = 'keep' and actor = %s and target = any(%s)", (OWN_ID, [f'post:{t}' for t in tgt])); check('처리 기록: 신고 되돌리기 3건', cur.fetchone()[0] == 3)
cur.execute("update reports set resolved_at = now() - interval '31 days' where uid = %s and state = 'kept'", (M_ID,)); cur.execute('select private.purge_old()'); cur.connection.commit()
cur.execute('select report_n from posts where id = %s', (px,)); check('  └ 30일이 지나면 다시 셈(새벽 정리 때 맞춤 → 3, 가림)', cur.fetchone()[0] == 3 and get_post(px, R2) == [])

print('▸ 처리 기록(운영 일지, docs/11 §12-11) — 원장이 지운 것 · 30일치 · 6개월 뒤 파기')
dp = mkpost(R3, R3_ID, '지울 글', '원장이 지움', 'talk')
mp = mkpost(R3, R3_ID, '내가 지울 글', '스스로 지움', 'talk')
rpc('delete_item', {'p_kind': 'post', 'p_id': dp}, OWN); rpc('delete_item', {'p_kind': 'post', 'p_id': mp}, R3)
call('PATCH', f'/rest/v1/comments?id=eq.{c0}', {'deleted': True}, OWN)
cur.execute("select target from talk_log where action = 'del' and uid in (%s, %s) and actor = %s", (R3_ID, R1_ID, OWN_ID)); dl = {r[0] for r in cur.fetchall()}
check('원장이 남의 글·댓글을 지우면 기록(앱 함수든 직접 고치기든)', {f'post:{dp}', f'comment:{c0}'} <= dl, dl)
check('  └ 학생이 자기 글을 지운 것은 기록하지 않음', f'post:{mp}' not in dl)
s, j = rpc('talk_limits', {}, OWN); lg = j['log']; acts = {x['action'] for x in lg}
check('원장 화면 30일 기록: 지우기·신고 되돌리기·첫 글 승인/거절·선생님 확인이 함께', {'del', 'keep', 'approve', 'reject', 'check', 'uncheck'} <= acts, acts)
d = [x for x in lg if x.get('target') == f'post:{dp}']; check('  └ 누가(원장) · 무엇을(지운 글 제목)', d and d[0]['actor_role'] == 'owner' and d[0]['what'] == '지울 글' and d[0]['name'] == '댓글학생', d)
for nm, t in (('학생', R3), ('보호자', RP), ('손님', RG)):
    s, j = rpc('talk_limits', {}, t); check(f'  └ {nm}은 기록을 못 받음', j.get('log') == [] and j.get('guard') == [], j)
s, j = call('GET', '/rest/v1/talk_log?select=*', tok=R3); check('  └ 기록 표는 API 로 안 보임', s >= 400 or j == [], (s, j))
cur.execute("update talk_log set at = now() - interval '40 days' where target = %s", (f'post:{dp}',)); cur.connection.commit()
s, j = rpc('talk_limits', {}, OWN); check('  └ 30일 지난 기록은 화면에서 빠짐(보관은 6개월)', not any(x.get('target') == f'post:{dp}' for x in j['log']))
cur.execute("update talk_log set at = now() - interval '7 months' where target = %s", (f'post:{dp}',)); cur.execute("update posts set reviewed_at = now() - interval '7 months' where id = %s", (fp2,))
cur.execute("update posts set review = 'no' where id = %s", (fp2,)); cur.execute('select private.purge_old()'); cur.connection.commit()
cur.execute("select count(*) from talk_log where target = %s", (f'post:{dp}',)); n1 = cur.fetchone()[0]; cur.execute('select count(*) from posts where id = %s', (fp2,))
check('6개월 지난 처리 기록 · 공개하지 않은 지 6개월 된 첫 글은 파기', n1 == 0 and cur.fetchone()[0] == 0)

print('▸ 욕설·비하 — 아주 심한 욕만 서버가 거절, 보통 거친 말은 앱이 한 번 더 묻기만(docs/11 §12-14)')
s, j = call('POST', '/rest/v1/posts', {'board': 'talk', 'title': '야', 'body': '느 금 마 진짜'}, R3); check('아주 심한 욕(띄어 써도)은 글 거절', s >= 400 and '심한 욕설' in str(j), (s, j))
s, j = call('POST', '/rest/v1/comments', {'post_id': fp3, 'body': '니애미'}, R3); check('  └ 댓글도 거절', s >= 400 and '심한 욕설' in str(j), (s, j))
s, j = call('PATCH', f'/rest/v1/posts?id=eq.{fp3}', {'body': '좆같네'}, R1); check('  └ 고쳐 쓸 때도 거절', s >= 400, s)
s, j = call('POST', '/rest/v1/posts?select=id', {'board': 'talk', 'title': '시험 망함', 'body': '아 씨발 시험 망했다'}, R3, 'return=representation'); check('보통 거친 말은 서버가 막지 않음(앱이 한 번 묻기만)', s == 201, (s, j))
s, j = call('POST', '/rest/v1/posts?select=id', {'board': 'qna', 'title': '시발점', 'body': '벡터의 시발점, 음식을 씹어 먹기, 미친 듯이 공부, 위기가 닥쳐온다, 애자는 절연체'}, R3, 'return=representation'); check('  └ 과학 용어·일상어는 그대로', s == 201, (s, j))
s, j = call('POST', '/rest/v1/posts?select=id', {'board': 'talk', 'title': '안내', 'body': "'느금마' 같은 말은 쓰지 않아요"}, OWN, 'return=representation'); check('  └ 원장 안내 글(인용)은 됨', s == 201, (s, j))
for nk in ('느금마왕', '병신', '개새끼'):
    s, _ = call('PATCH', f'/rest/v1/profiles?id=eq.{R3_ID}', {'nick': nk}, R3)
    if s < 400: check(f'욕설 닉네임 막음: {nk}', False, s); break
else: check('닉네임에는 거친 말도 안 됨(서버)', True)
s, _ = call('PATCH', f'/rest/v1/profiles?id=eq.{R3_ID}', {'nick': '시발점탐험'}, R3); check('  └ "시발점" 닉네임은 됨', s == 204, s)

print("▸ 보호자 '이야기 끄기'(docs/11 §12-15) — 확인된 보호자가 자기 자녀만 · 쓰기만/읽기까지 · 원장 제한과 따로")
call('POST', '/rest/v1/students', {'code': 'GRD001', 'name': '보호대상', 'cls': '월목반', 'until': '2099-02-28'}, OWN)
call('POST', '/rest/v1/students', {'code': 'GRD002', 'name': '아직미등록', 'cls': '월목반', 'until': '2099-02-28'}, OWN)
GS, GS_ID = signup('gs@test.kr', '보호대상학생'); rpc('link_code', {'p_kind': 'student', 'p_code': 'GRD001'}, GS); member(GS_ID)
GP, GP_ID = signup('gp@test.kr', '엄마', role='parent'); GQ, GQ_ID = signup('gq@test.kr', '확인전보호자', role='parent'); GZ, GZ_ID = signup('gz@test.kr', '남의보호자', role='parent')
for t in (GP, GQ): rpc('link_code', {'p_kind': 'child', 'p_code': 'GRD001'}, t)
rpc('link_code', {'p_kind': 'child', 'p_code': 'GRD002'}, GP)
rpc('guardian_decide', {'p_uid': GP_ID, 'p_code': 'GRD001', 'p_ok': True}, OWN); rpc('guardian_decide', {'p_uid': GP_ID, 'p_code': 'GRD002', 'p_ok': True}, OWN)
s, j = rpc('child_talk', {'p_code': 'GRD001'}, GP); check('확인된 보호자는 자녀 이야기 상태를 봄(켜짐)', j.get('ok') and j.get('linked') and j.get('mode') is None, j)
for nm, t in (('확인 전 보호자', GQ), ('다른 집 보호자', GZ), ('학생 본인', GS), ('원장', OWN)):
    s, j = rpc('child_talk', {'p_code': 'GRD001'}, t); check(f'  └ {nm}은 상태를 못 봄', j.get('ok') is False, j)
    s, j = rpc('guardian_talk', {'p_code': 'GRD001', 'p_mode': 'all'}, t); check(f'  └ {nm}은 못 끔', j.get('ok') is False, j)
s, _ = rpc('guardian_talk', {'p_code': 'GRD001', 'p_mode': 'all'}, ANON); check('  └ 비로그인은 못 부름', s >= 400, s)
cur.execute('select guard_talk from profiles where id = %s', (GS_ID,)); check('  └ (아직 켜짐)', cur.fetchone()[0] is None)
s, _ = call('PATCH', f'/rest/v1/profiles?id=eq.{GS_ID}', {'guard_talk': None}, GS); s2, _ = call('PATCH', f'/rest/v1/profiles?id=eq.{GS_ID}', {'guard_talk': 'write'}, GP)
check('  └ 설정 칸을 학생·보호자가 직접 못 고침(함수로만)', s in (401, 403) and s2 in (401, 403), (s, s2))
s, j = rpc('guardian_talk', {'p_code': 'GRD002', 'p_mode': 'write'}, GP); check('자녀가 아직 앱에 코드를 등록하지 않았으면 안내', j.get('ok') is False and '등록' in j.get('why', ''), j)
s, j = rpc('guardian_talk', {'p_code': 'grd001', 'p_mode': 'write'}, GP); check('보호자가 쓰기 끄기', j.get('ok') and j.get('mode') == 'write', j)
s, j = rpc('my_talk', {}, GS); check('  └ 자녀 상태: guardian · 읽기는 됨 · 차분한 문구', j['block'] == 'guardian' and j['read'] is True and '보호자와 정한' in j['msg'], j)
s, j = call('POST', '/rest/v1/posts', {'board': 'talk', 'title': '글', 'body': '써 봅니다'}, GS); check('  └ 서버가 글을 막음', s == 403 and '보호자와 정한' in str(j), (s, j))
s, _ = call('POST', '/rest/v1/comments', {'post_id': fp3, 'body': '댓글'}, GS); check('  └ 댓글도 막음', s == 403, s)
s, _ = rpc('like_toggle', {'p_kind': 'post', 'p_id': fp3}, GS); check('  └ 도움됨도 막음', s >= 400, s)
check('  └ 읽기는 됨', len(get_post(fp3, GS)) == 1)
s, j = rpc('guardian_talk', {'p_code': 'GRD001', 'p_mode': 'all'}, GP); s2, j2 = rpc('my_talk', {}, GS)
check('보호자가 읽기까지 끄기 → 자녀 상태 read=false', j.get('mode') == 'all' and j2['read'] is False and j2['block'] == 'guardian', (j, j2))
s, j = call('GET', '/rest/v1/posts?select=id', tok=GS); s2, j2 = call('GET', f'/rest/v1/comments?post_id=eq.{fp3}&select=id', tok=GS); check('  └ 글·댓글이 서버에서 안 보임', j == [] and j2 == [], (j, j2))
check('  └ 다른 학생·원장은 그대로 봄', len(get_post(fp3, R2)) == 1 and len(get_post(fp3, OWN)) == 1)
s, j = rpc('child_talk', {'p_code': 'GRD001'}, GP); check('  └ 보호자 화면 상태: all · 내가 끔', j.get('mode') == 'all' and j.get('mine') is True and j.get('by') == '엄마', j)
s, j = rpc('talk_limits', {}, OWN); gg = [x for x in j['guard'] if x['uid'] == GS_ID]; check('원장 목록: 보호자가 꺼 둔 학생(누가·어떻게)', gg and gg[0]['mode'] == 'all' and gg[0]['by_name'] == '엄마', j['guard'])
cur.execute("select action, guardian, actor from talk_log where uid = %s order by at", (GS_ID,)); rows = cur.fetchall()
check('  └ 처리 기록(보호자 · 누가)', [r[0] for r in rows] == ['g_write', 'g_all'] and all(r[1] and r[2] == GP_ID for r in rows), rows)
rpc('guardian_talk', {'p_code': 'GRD001', 'p_mode': 'on'}, GP); s, j = call('POST', '/rest/v1/posts?select=id', {'board': 'talk', 'title': '다시', 'body': '켜졌어요'}, GS, 'return=representation'); check('보호자가 다시 켜면 씀', s == 201, (s, j))
rpc('talk_limit', {'p_uid': GS_ID, 'p_days': 7, 'p_reason': '친구를 놀렸어요'}, OWN); rpc('guardian_talk', {'p_code': 'GRD001', 'p_mode': 'write'}, GP); rpc('guardian_talk', {'p_code': 'GRD001', 'p_mode': 'on'}, GP)
s, j = rpc('my_talk', {}, GS); check('보호자가 켜도 원장이 건 제한은 그대로(서로 덮지 않음)', j['block'] == 'limit', j)
rpc('talk_limit', {'p_uid': GS_ID, 'p_days': 0}, OWN)
rpc('guardian_talk', {'p_code': 'GRD001', 'p_mode': 'write'}, GP); rpc('unlink_child', {'p_code': 'GRD001'}, GP)
cur.execute('select guard_talk from profiles where id = %s', (GS_ID,)); check('보호자가 연결을 끊으면 그 보호자의 설정도 풀림', cur.fetchone()[0] is None)
rpc('link_code', {'p_kind': 'child', 'p_code': 'GRD001'}, GP); rpc('guardian_decide', {'p_uid': GP_ID, 'p_code': 'GRD001', 'p_ok': True}, OWN); rpc('guardian_talk', {'p_code': 'GRD001', 'p_mode': 'all'}, GP)
rpc('delete_my_account', {}, GP); cur.execute('select guard_talk, guard_by from profiles where id = %s', (GS_ID,)); check('  └ 보호자가 탈퇴해도 풀림', cur.fetchone() == (None, None))

print('▸ 학원 과제(★4) — 원장만 내고 보고 · 학생은 내 과제만 · 보호자는 확인된 자녀만 · 표는 API 로 안 열림')
T0 = dt.datetime.now(ZoneInfo('Asia/Seoul')).date(); DUE = (T0 + dt.timedelta(days=3)).isoformat()
for c, n, k, u in (('ASG001', '과제학생', '과제반', '2099-02-28'), ('ASG002', '안낸학생', '과제반', '2099-02-28'), ('ASG003', '화금학생', '화금반', '2099-02-28'), ('ASG004', '끝난학생', '과제반', '2020-02-28'), ('ASG005', '어린학생', '어린반', '2099-02-28')):
    call('POST', '/rest/v1/students', {'code': c, 'name': n, 'cls': k, 'until': u, 'phone': '01055556666'}, OWN)
SA, SA_ID = signup('asa@test.kr', '과제학생'); rpc('link_code', {'p_kind': 'student', 'p_code': 'ASG001'}, SA)
SB, SB_ID = signup('asb@test.kr', '화금학생'); rpc('link_code', {'p_kind': 'student', 'p_code': 'ASG003'}, SB)
SG, SG_ID = signup('asg@test.kr', '손님학생')
SK, SK_ID = signup('ask@test.kr', '어린학생', under14=True, guardian='보호 01012341234'); rpc('link_code', {'p_kind': 'student', 'p_code': 'ASG005'}, SK)
PA, PA_ID = signup('apa@test.kr', '과제엄마', role='parent'); rpc('link_code', {'p_kind': 'child', 'p_code': 'ASG001'}, PA); rpc('guardian_decide', {'p_uid': PA_ID, 'p_code': 'ASG001', 'p_ok': True}, OWN)
PQ, PQ_ID = signup('apq@test.kr', '확인전', role='parent'); rpc('link_code', {'p_kind': 'child', 'p_code': 'ASG001'}, PQ)
PZ, PZ_ID = signup('apz@test.kr', '남의엄마', role='parent'); rpc('link_code', {'p_kind': 'child', 'p_code': 'ASG003'}, PZ); rpc('guardian_decide', {'p_uid': PZ_ID, 'p_code': 'ASG003', 'p_ok': True}, OWN)
ITEMS = ['1101-q1', '1101-q2', '1101-q3', '1101-q4']
mk = lambda tok, **kw: rpc('assign_create', {'p_kind': 'bank', 'p_title': '1-01 문제 4개', 'p_ref': '1101', 'p_items': ITEMS, 'p_cls': '과제반', 'p_codes': None, 'p_due': DUE, **kw}, tok)
s, j = mk(OWN); check('원장이 반에 과제를 냄 → 수강 중인 학생만(끝난 학생 빼고 2명)', s == 200 and j['ok'] and j['target'] == 2, (s, j)); A1 = j['id']
for nm, t in (('학생', SA), ('보호자', PA), ('손님', SG)):
    s, j = mk(t); check(f'  └ {nm}은 과제를 못 냄', s >= 400, (s, j))
s, j = mk(ANON); check('  └ 비로그인은 못 부름', s >= 400, (s, j))
s, j = mk(OWN, p_due=(T0 - dt.timedelta(days=1)).isoformat()); check('  └ 지난 날짜 마감은 거절', j.get('ok') is False and '마감일' in j['why'], j)
s, j = mk(OWN, p_items=[]); check('  └ 문항 0개 거절', j.get('ok') is False, j)
s, j = mk(OWN, p_items=[f'1101-q{i}' for i in range(41)]); check('  └ 41문항 거절(40개까지)', j.get('ok') is False, j)
s, j = mk(OWN, p_cls='없는반'); check('  └ 받을 학생이 없으면 안내', j.get('ok') is False and '학생이 없' in j['why'], j)
s, j = mk(OWN, p_cls=None, p_codes=['ASG003', 'NOPE01', 'ASG004'], p_items=['1101-q1', '1101-q1', 'x;drop', '1101-q2'], p_title='화금 개별')
check('학생을 골라 냄 → 있는·수강 중인 코드만 · 같은 문항 한 번 · 이상한 id 뺌', j.get('ok') and j['target'] == 1, j); A2 = j['id']
cur.execute('select items, codes, cls from assignments where id = %s', (A2,)); r = cur.fetchone(); check('  └ 저장: 문항 순서 그대로 · 대상 고정 · 반 없음', r == (['1101-q1', '1101-q2'], ['ASG003'], None), r)
for nm, t in (('원장', OWN), ('학생', SA), ('보호자', PA)):
    s, j = call('GET', '/rest/v1/assignments?select=*', tok=t); s2, j2 = call('GET', '/rest/v1/submissions?select=*', tok=t)
    check(f'  └ 과제·제출 표는 API 로 안 열림({nm})', s >= 400 and s2 >= 400, (s, s2))
s, j = call('POST', '/rest/v1/submissions', {'aid': A1, 'code': 'ASG001', 'done': 4, 'right_n': 4, 'submitted_at': '2020-01-01T00:00:00Z'}, SA); check('  └ 학생이 제출 줄을 직접 못 넣음(함수로만)', s >= 400, (s, j))
s, j = rpc('my_assignments', {}, SA); check('학생: 내 반 과제만 보임(대상 학생 목록은 안 줌)', [x['id'] for x in j] == [A1] and 'codes' not in j[0] and j[0]['n'] == 4 and j[0]['items'] == ITEMS, j)
s, j = rpc('my_assignments', {}, SB); check('  └ 골라 낸 학생은 그 과제만', [x['id'] for x in j] == [A2], j)
for nm, t in (('손님', SG), ('보호자', PA), ('원장', OWN)):
    s, j = rpc('my_assignments', {}, t); check(f'  └ {nm}은 빈 목록', j == [], j)
s, j = rpc('my_assignments', {}, ANON); check('  └ 비로그인은 못 부름', s >= 400, (s, j))
sv = lambda tok, aid=A1, **kw: rpc('assign_save', {'p_id': aid, 'p_done': 2, 'p_right': 1, 'p_secs': 40, 'p_wrong': ['1101-q2'], 'p_submit': False, **kw}, tok)
s, j = sv(SA); check('학생: 진행 저장(2/4)', j.get('ok') and j['done'] == 2 and j['submitted_at'] is None, j)
s, j = sv(SB); check('  └ 남의 반 과제에는 못 씀', j.get('ok') is False and '받은 과제가 아닙' in j['why'], j)
for nm, t in (('보호자', PA), ('손님', SG), ('원장', OWN)):
    s, j = sv(t); check(f'  └ {nm}은 못 씀', j.get('ok') is False, j)
s, j = sv(ANON); check('  └ 비로그인은 못 부름', s >= 400, (s, j))
s, j = sv(SA, p_done=1); check('  └ 더 앞선 진행을 옛 기기가 덮지 않음', j.get('ok') and j['done'] == 2, j)
s, j = sv(SA, p_done=3, p_submit=True); check('  └ 다 풀기 전에는 제출 안 됨', j.get('ok') is False and '다 풀지' in j['why'], j)
s, j = sv(SA, p_done=99, p_right=99, p_secs=10 ** 7, p_wrong=['1101-q3', 'ZZZ-q9', '1101-q3'], p_submit=True)
cur.execute("select done, right_n, secs, wrong, late, submitted_at is not null from submissions where aid = %s and code = 'ASG001'", (A1,)); r = cur.fetchone()
check('제출: 서버가 문항 수 안으로 맞춤(4/4 · 하루 넘는 시간 자름 · 과제 밖 문항 뺌) · 제출 시각은 서버', j.get('ok') and r == (4, 4, 86400, ['1101-q3'], False, True), (j, r))
s, j = sv(SA, p_done=4, p_right=0, p_submit=True); cur.execute("select right_n from submissions where aid = %s and code = 'ASG001'", (A1,))
check('  └ 한 번 낸 과제는 다시 바뀌지 않음', j.get('already') and cur.fetchone()[0] == 4, j)
cur.execute('update profiles set guardian_ok = false where id = %s', (SK_ID,)); cur.connection.commit()
A3 = mk(OWN, p_cls='어린반', p_title='어린반 과제')[1]['id']
s, j = sv(SK, aid=A3, p_done=4, p_submit=True); check('만 14세 미만 보호자 동의 전: 서버에 제출하지 않고 안내(기기에 남김)', j.get('ok') is False and j.get('consent'), j)
cur.execute('select count(*) from submissions where aid = %s', (A3,)); check('  └ 제출 줄이 생기지 않음', cur.fetchone()[0] == 0)
cur.execute("update assignments set due = current_date - 2 where id = %s", (A2,)); cur.connection.commit()
s, j = sv(SB, aid=A2, p_done=2, p_right=1, p_wrong=['1101-q1'], p_submit=True); check('마감 지난 뒤 제출 → 늦은 제출', j.get('ok') and j['late'] is True, j)
s, j = rpc('my_assignments', {}, SB); check('  └ 학생 화면에도 늦은 제출 · 마감 14일 안의 지난 과제는 보임', j and j[0]['late'] is True and j[0]['submitted_at'], j)
s, j = rpc('assign_list', {}, OWN); a1 = next(x for x in j if x['id'] == A1)
check('원장 목록: 대상 2 · 제출 1 · 정답률 100% · 아직 안 낸 학생', a1['target'] == 2 and a1['submitted'] == 1 and a1['rate'] == 100 and a1['missing'] == ['ASG002'], a1)
a2 = next(x for x in j if x['id'] == A2); check('  └ 늦은 제출 수', a2['late'] == 1 and a2['missing'] == [], a2)
for nm, t in (('학생', SA), ('보호자', PA), ('손님', SG)):
    s, j = rpc('assign_list', {}, t); check(f'  └ {nm}은 목록을 못 받음', j == [], j)
    s, j = rpc('assign_report', {'p_id': A1}, t); check(f'  └ {nm}은 제출 현황을 못 받음', j.get('ok') is False, j)
s, j = rpc('assign_list', {}, ANON); check('  └ 비로그인은 못 부름', s >= 400, s)
sv(SA, aid=A1)   # (이미 냄 — 그대로)
s, j = rpc('assign_report', {'p_id': A1}, OWN); rows = {r['code']: r for r in j['rows']}
check('원장 제출 현황: 학생별 맞힌 수·걸린 시간·제출 시각 · 안 낸 학생도 줄로', j['ok'] and rows['ASG001']['right'] == 4 and rows['ASG001']['submitted_at'] and rows['ASG002']['submitted_at'] is None and 'ASG004' not in rows, j)
check('  └ 많이 틀린 문항(틀린 학생 수)', j['top'] == [{'id': '1101-q3', 'n': 1}], j['top'])
s, j = rpc('child_assignments', {'p_code': 'ASG001'}, PA); check('보호자(확인됨): 자녀 과제 · 낸 것 표시(문항 목록은 안 줌)', j.get('ok') and j['list'][0]['submitted_at'] and 'items' not in j['list'][0] and 'right' not in j['list'][0], j)
for nm, t, c in (('확인 전 보호자', PQ, 'ASG001'), ('다른 집 보호자', PZ, 'ASG001'), ('학생 본인', SA, 'ASG001'), ('원장', OWN, 'ASG001'), ('손님', SG, 'ASG001')):
    s, j = rpc('child_assignments', {'p_code': c}, t); check(f'  └ {nm}은 못 봄', j.get('ok') is False, j)
s, j = rpc('child_assignments', {'p_code': 'ASG001'}, ANON); check('  └ 비로그인은 못 부름', s >= 400, s)
for nm, t in (('원장', OWN), ('학생', SA), ('보호자', PA), ('비로그인', ANON)):
    s, j = rpc('weekly_digest', {}, t); check(f'주간 요약 원본(weekly_digest)은 서비스 키 전용 — {nm} 거절', s >= 400, (s, j))
for nm, t in (('학생', SA), ('보호자', PA)):
    s, _ = rpc('assign_delete', {'p_id': A1}, t); check(f'  └ {nm}은 과제를 못 지움', s >= 400)
cur.execute('select count(*) from assignments where id = %s', (A1,)); check('  └ (그대로 있음)', cur.fetchone()[0] == 1)
rpc('delete_my_account', {}, SA); cur.execute("select count(*) from submissions where code = 'ASG001'"); check('학생이 탈퇴하면 그 코드의 제출 기록도 지움', cur.fetchone()[0] == 0)
call('DELETE', '/rest/v1/students?code=eq.ASG003', tok=OWN); cur.execute("select count(*) from submissions where code = 'ASG003'"); check('학생 코드를 지우면 제출도 지움', cur.fetchone()[0] == 0)
cur.execute("update assignments set due = current_date - 366 where id = %s", (A2,)); cur.execute("update assignments set due = current_date - 300 where id = %s", (A3,)); cur.execute('select private.purge_old()'); cur.connection.commit()
cur.execute('select count(*) from assignments where id in (%s, %s)', (A2, A3)); check('마감 1년 지난 과제는 새벽 정리로 파기(1년 안은 남김)', cur.fetchone()[0] == 1)
rpc('assign_delete', {'p_id': A1}, OWN); cur.execute('select count(*) from assignments where id = %s', (A1,)); check('원장은 과제를 지움', cur.fetchone()[0] == 0)

print(f'\n보안 시험 {len(OK)}/{len(OK) + len(BAD)} 통과')
sys.exit(1 if BAD else 0)

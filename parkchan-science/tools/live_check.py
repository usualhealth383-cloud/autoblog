"""실서버(Supabase) 점검 — 서버를 연결한 날과 앱을 새로 낼 때마다 한 번.

    python3 tools/live_check.py                       # app/server/config.json 의 서버를 손님(anon) 키로 점검
    python3 tools/live_check.py --owner 원장@메일      # + 원장 계정으로 로그인해 원장 화면 권한 확인(비밀번호는 물어봄 · LIVE_PW 로도)
    python3 tools/live_check.py --pages               # + 배포된 웹앱(GitHub Pages)이 이 서버로 빌드됐는지
    python3 tools/live_check.py --url http://127.0.0.1:8767 --anon <키>   # 로컬 시험대로 이 점검 자체를 시험

읽기와 '막혀야 하는 호출'만 한다 — 가입·글쓰기·메일 발송처럼 실서버에 흔적을 남기는 일은 하지 않는다.
SQL 쪽(확장·예약 작업·RLS·원장 고정)은 app/server/verify.sql 을 SQL Editor 에서 한 번 돌린다.
끝 줄 'LIVE CHECK OK' 가 아니면 출시하지 않는다.
"""
import argparse, getpass, json, os, ssl, sys, urllib.error, urllib.request as U

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
PAGES = 'https://usualhealth383-cloud.github.io/autoblog/parkchan/'
# schema.sql 의 public 표 — 손님 키로는 한 줄도 읽히면 안 된다(RLS·권한)
TABLES = ['students', 'classes', 'attendance', 'notices', 'notice_reads', 'sched', 'profiles', 'guardian_links', 'progress', 'passes', 'purchases',
          'notes', 'feedback', 'posts', 'comments', 'reports', 'talk_log', 'push_later', 'push_tokens', 'client_errors', 'assignments', 'submissions', 'weekly_notes']
# 일부러 공개한 표와 그 칸 — 가입 화면의 반 고르기(schema.sql classes_read). 다른 칸이 보이면 실패
PUBLIC_OK = {'classes': {'cls', 'start_time'}}
# 로그인해야 하거나 원장만 부르는 함수 — 손님 키로 부르면 거절되거나 빈 값이어야 한다
Z = '00000000-0000-0000-0000-000000000000'
DENY_RPC = {'current_attend_code': {}, 'assign_list': {}, 'feedback_list': {}, 'care_list': {}, 'consent_list': {}, 'guardian_requests': {},
            'reported_list': {}, 'review_list': {}, 'unanswered_list': {}, 'note_get': {'p_code': 'MON123'}, 'my_assignments': {},
            'delete_user': {'p_uid': Z}, 'mark_attend': {'p_code': 'MON123', 'p_entered': '0000'},
            # 손님도 부를 수는 있지만 안에서 로그인을 보고 아무것도 안 하는 함수(2026-10-08 시험대에서 한 번씩 확인)
            'delete_my_account': {}, 'like_toggle': {'p_kind': 'post', 'p_id': Z}, 'link_code': {'p_kind': 'student', 'p_code': 'MON123'},
            'linked_of': {'p_code': 'MON123'}, 'mark_attend_manual': {'p_code': 'MON123'}, 'my_classes': {}, 'my_codes': {}, 'my_student_code': {},
            'pick_comment': {'p_post': Z, 'p_comment': Z}, 'redeem_pass': {'p_code': 'ABCD-EFGH'}, 'release_code': {'p_code': 'MON123'}, 'is_owner': {}}
FAILS, WARNS = [], []


def check(name, ok, info=''):
    print(('  ✓ ' if ok else '  ✗ ') + name + ('' if ok or not info else f'  — {str(info)[:200]}'))
    if not ok: FAILS.append(name)


def warn(name, info=''):
    print('  ! ' + name + (f'  — {info}' if info else '')); WARNS.append(name)


def ctx():
    c = ssl.create_default_context()
    ca = '/root/.ccr/ca-bundle.crt'          # 이 작업 환경의 프록시 인증서(있을 때만) — 검증은 끄지 않는다
    if os.path.exists(ca): c.load_verify_locations(ca)
    return c


def call(base, key, method, path, body=None, tok=None, extra=None):
    h = {'apikey': key, 'Authorization': 'Bearer ' + (tok or key), 'Content-Type': 'application/json'}
    h.update(extra or {})
    r = U.Request(base + path, data=None if body is None else json.dumps(body).encode(), headers=h, method=method)
    try:
        with U.urlopen(r, timeout=20, context=ctx() if base.startswith('https') else None) as res:
            t = res.read().decode('utf-8', 'replace'); s = res.status
    except urllib.error.HTTPError as e:
        t = e.read().decode('utf-8', 'replace'); s = e.code
    except Exception as e:                     # 주소 틀림·연결 안 됨
        return 0, str(e)
    try: return s, json.loads(t) if t else None
    except ValueError: return s, t


def empty(j):
    if isinstance(j, dict) and j.get('ok') is False: return True      # {ok:false, why:'로그인이 필요합니다'}
    return j in (None, [], {}, '', 'null', False) or (isinstance(j, dict) and all(v in (None, [], {}, '', False, 0) for v in j.values()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--url'); ap.add_argument('--anon'); ap.add_argument('--owner'); ap.add_argument('--pages', action='store_true')
    a = ap.parse_args()
    cfg = {}
    p = os.path.join(ROOT, 'app', 'server', 'config.json')
    if os.path.exists(p): cfg = json.load(open(p, encoding='utf-8'))
    base = (a.url or cfg.get('url') or '').rstrip('/'); key = a.anon or cfg.get('anonKey') or ''
    if not base or 'YOUR-PROJECT' in base or not key.startswith('ey') and not key.startswith('sb_'):
        sys.exit('✗ 서버 주소·anon 키가 없습니다 — app/server/config.json 을 먼저 채우세요(config.example.json 참고)')
    local = base.startswith('http://127.') or base.startswith('http://localhost')
    print(f'▸ 서버 {base}' + (' (로컬 시험대)' if local else ''))

    print('▸ 스키마가 깔렸는가')
    s, j = call(base, key, 'POST', '/rest/v1/rpc/app_meta', {})
    check('app_meta 가 답함(schema.sql 실행됨)', s == 200 and isinstance(j, dict), (s, j))

    print('▸ 손님 키로는 표가 하나도 안 읽힘(RLS·권한)')
    leaked = []
    for t in TABLES:
        s, j = call(base, key, 'GET', f'/rest/v1/{t}?select=*&limit=1')
        if s == 0: leaked.append(f'{t}(연결 안 됨)')
        elif s == 200 and j and t in PUBLIC_OK:
            extra = set(j[0]) - PUBLIC_OK[t]
            if extra: leaked.append(f'{t}: 공개 칸 밖 {sorted(extra)}')
        elif s == 200 and j: leaked.append(t)
    check(f'표 {len(TABLES)}개 모두 0줄 또는 거절(반 이름·시작 시각만 공개)', not leaked, leaked)
    s, j = call(base, key, 'GET', '/rest/v1/config?select=*&limit=1', extra={'Accept-Profile': 'private'})
    check('private 스키마(출석 씨앗·원장 고정값)는 밖에서 안 보임', s >= 400 or empty(j), (s, j))

    print('▸ 손님 키로 원장·학생 함수가 막힘')
    opened = []
    for f, body in DENY_RPC.items():
        s, j = call(base, key, 'POST', f'/rest/v1/rpc/{f}', body)
        if 200 <= s < 300 and not empty(j): opened.append((f, s, str(j)[:60]))
    check(f'함수 {len(DENY_RPC)}개 거절 또는 빈 값', not opened, opened)
    s, j = call(base, key, 'POST', '/rest/v1/rpc/consent_info', {'p_token': 'x' * 32})
    check('없는 동의 링크로는 아무것도 안 보임', s >= 400 or empty(j) or (isinstance(j, dict) and not j.get('name')), (s, j))

    print('▸ 로그인 설정')
    s, j = call(base, key, 'GET', '/auth/v1/settings')
    if s == 200 and isinstance(j, dict):
        check('메일 인증 켜짐(Confirm email — 원장 이메일 사칭 방지)', j.get('mailer_autoconfirm') is False, j.get('mailer_autoconfirm'))
        check('이메일 가입 열림', (j.get('external') or {}).get('email') is True and not j.get('disable_signup'), j)
    elif local: print('  · 시험대에는 /auth/v1/settings 가 없음 — 실서버에서만 봄')
    else: check('로그인 설정 읽기', False, (s, j))
    s, j = call(base, key, 'POST', '/auth/v1/token?grant_type=password', {'email': 'nobody@parkchan.invalid', 'password': 'wrong-pass-1'})
    check('틀린 비밀번호는 거절', s in (400, 401, 422), (s, j))

    print('▸ 서버 함수(Edge Function) — 비밀값 없이 부르면 막혀야 함')
    for fn, body in (('push', {'kind': 'notice'}), ('verify-purchase', {'token': 'x', 'product': 'pass_m1'})):
        s, j = call(base, key, 'POST', f'/functions/v1/{fn}', body)
        if local and s == 502: print(f'  · {fn}: 시험대에서는 testbed_functions.py 가 따로 띄움 — 실서버에서만 봄'); continue
        if s == 404: warn(f'{fn} 아직 배포 안 됨', 'README 「결제 · 푸시 알림」 — 앱 스토어 출시 전에만 필요')
        else: check(f'{fn}: 비밀값·로그인 없이 거절', s in (400, 401, 403), (s, j))

    if a.owner:
        print('▸ 원장 계정')
        pw = os.environ.get('LIVE_PW') or getpass.getpass('원장 비밀번호: ')
        s, j = call(base, key, 'POST', '/auth/v1/token?grant_type=password', {'email': a.owner, 'password': pw})
        tok = isinstance(j, dict) and j.get('access_token'); uid = tok and (j.get('user') or {}).get('id')
        check('로그인됨(메일 인증까지 끝난 계정)', bool(tok), (s, j if not isinstance(j, dict) else j.get('msg') or j.get('error_description')))
        if tok:
            s, j = call(base, key, 'GET', f'/rest/v1/profiles?select=role&id=eq.{uid}', tok=tok)
            check('역할이 owner(schema.sql [설정] 두 줄 실행됨)', s == 200 and j and j[0].get('role') == 'owner', j)
            s, j = call(base, key, 'POST', '/rest/v1/rpc/current_attend_code', {}, tok=tok)
            check('원장 함수(출석 숫자)가 열림', s == 200 and isinstance(j, dict) and j.get('code'), (s, j))
            s, j = call(base, key, 'POST', '/rest/v1/rpc/assign_list', {}, tok=tok)
            check('과제 목록 함수가 열림', s == 200, (s, j))

    if a.pages:
        print('▸ 배포된 웹앱')
        try:
            with U.urlopen(U.Request(PAGES, headers={'Cache-Control': 'no-cache'}), timeout=30, context=ctx()) as r: h = r.read().decode('utf-8', 'replace')
        except Exception as e: h = ''; check('웹앱 열림', False, e)
        if h:
            check('웹앱이 이 서버 주소로 빌드됨(서버 모드)', base in h, '로컬 모드 빌드 — config.json 을 채우고 build.py 다시')
            check('옛 아이폰을 멈추는 문법 없음', '(?<=' not in h and '(?<!' not in h)
            check('학원 연락처가 들어감', '"phone": ""' not in h and '"phone":""' not in h, 'CFG.phone 비어 있음')

    print()
    if WARNS: print('알림: ' + ' · '.join(WARNS))
    print('LIVE CHECK OK' if not FAILS else f'LIVE CHECK ✗ {len(FAILS)}건: ' + ' · '.join(FAILS))
    sys.exit(1 if FAILS else 0)


main()

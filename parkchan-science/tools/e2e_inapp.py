"""앱 안 브라우저 안내 — 카카오톡·네이버·인스타그램에서 열면 위에 한 줄(막지 않음), 보통 브라우저에서는 안 보임.

    python3 tools/e2e_inapp.py      # 앱 서버 :8765 필요
"""
import asyncio, sys
from playwright.async_api import async_playwright
sys.path.insert(0, __import__('os').path.dirname(__file__))
from _ui import NO_INTRO

URL = 'http://127.0.0.1:8765/'
AND = 'Mozilla/5.0 (Linux; Android 14; SM-S921N Build/UP1A; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/129.0.0.0 Mobile Safari/537.36'
IOS = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148'
CASES = [  # (이름, UA, 보여야 함, 단추 주소 앞부분, 안내 글)
    ('카카오톡 안드로이드', AND + ' KAKAOTALK 10.8.5', True, 'kakaotalk://web/openExternal?url=http%3A%2F%2F127.0.0.1%3A8765%2F', '크롬으로 열기'),
    ('카카오톡 아이폰', IOS + ' KAKAOTALK 10.8.5', True, 'kakaotalk://web/openExternal?url=', '사파리로 열기'),
    ('네이버 아이폰', IOS + ' NAVER(inapp; search; 2000; 12.6.1)', True, None, '사파리로 열기'),
    ('인스타그램 안드로이드', AND + ' Instagram 350.0.0.0', True, 'intent://127.0.0.1:8765/#Intent;scheme=https;package=com.android.chrome;end', '크롬으로 열기'),
    ('보통 크롬', 'Mozilla/5.0 (Linux; Android 14; SM-S921N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Mobile Safari/537.36', False, None, ''),
    ('보통 사파리', IOS.replace('Mobile/15E148', 'Version/17.6 Mobile/15E148 Safari/604.1'), False, None, ''),
]
FAIL = []


def check(name, ok, info=''):
    print(('  ✓ ' if ok else '  ✗ ') + name + ('' if ok else f'  — {info}'))
    if not ok: FAIL.append(name)


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium'); errs = []
        for name, ua, show, href, txt in CASES:
            for scheme in (('light', 'dark') if name == '카카오톡 안드로이드' else ('light',)):
                ctx = await b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2, user_agent=ua, is_mobile=True, has_touch=True, color_scheme=scheme)
                await ctx.add_init_script(NO_INTRO); pg = await ctx.new_page()
                pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' and 'ERR_' not in m.text else None); pg.on('pageerror', lambda e: errs.append(str(e)))
                await pg.goto(URL); await pg.wait_for_timeout(900)
                vis = await pg.locator('#iab').is_visible()
                check(f'{name}({scheme}): 안내 {"보임" if show else "안 보임"}', vis == show, vis)
                if show:
                    t = await pg.inner_text('#iab'); check(f'  └ 글: {txt}', txt in t, t)
                    h = await pg.get_attribute('#iabGo', 'href') if await pg.locator('#iabGo').count() else None
                    check(f'  └ 여는 단추 {"없음(메뉴 안내)" if href is None else "주소 맞음"}', (h is None) if href is None else (h or '').startswith(href), h)
                    if await pg.locator('#iabGo').count():
                        cr = await pg.evaluate('''() => { const e = document.getElementById('iabGo'), cs = getComputedStyle(e);
                          const L = c => { const v = c.match(/[0-9.]+/g).slice(0, 3).map(x => { x /= 255; return x <= .03928 ? x / 12.92 : ((x + .055) / 1.055) ** 2.4; }); return .2126 * v[0] + .7152 * v[1] + .0722 * v[2]; };
                          const a = L(cs.color), b = L(cs.backgroundColor); return (Math.max(a, b) + .05) / (Math.min(a, b) + .05); }''')
                        check(f'  └ 단추 글자 대비 4.5 이상({cr:.1f})', cr >= 4.5, cr)
                    box = await pg.locator('#iab').bounding_box(); vw = 390
                    check('  └ 가로 넘침 없음', box and box['x'] >= 16 and box['x'] + box['width'] <= vw - 16, box)
                    await pg.screenshot(path=f'/tmp/e2e_inapp_{len(FAIL)}_{name.replace(" ", "_")}_{scheme}.png')
                    if name == '카카오톡 안드로이드' and scheme == 'light':
                        await pg.click('#iabX'); await pg.wait_for_timeout(150)
                        check('  └ × 로 닫힘', not await pg.locator('#iab').is_visible())
                        await pg.reload(); await pg.wait_for_timeout(800)
                        check('  └ 새로고침해도 이번엔 다시 안 뜸', not await pg.locator('#iab').is_visible())
                await ctx.close()
        await b.close()
    check('콘솔 오류 없음', not errs, errs[:3])
    print('INAPP E2E OK' if not FAIL else f'INAPP E2E ✗ {len(FAIL)}: ' + ' · '.join(FAIL))
    sys.exit(1 if FAIL else 0)

asyncio.run(main())

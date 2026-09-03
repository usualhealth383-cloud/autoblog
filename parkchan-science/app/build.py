#!/usr/bin/env python3
"""앱 셸에 개념·문항·그림 데이터를 심어 배포용 한 파일로 만든다."""
import json, pathlib
ROOT = pathlib.Path('/home/user/autoblog/parkchan-science')
SC = pathlib.Path('/tmp/claude-0/-home-user-autoblog/63f2cb13-3be5-5173-9d36-a6477717e614/scratchpad')
shell = (SC / 'app-shell.html').read_text(encoding='utf-8')
concepts = json.loads((ROOT / 'data/concepts.json').read_text(encoding='utf-8'))
quizzes = json.loads((ROOT / 'data/quizzes.json').read_text(encoding='utf-8'))
figs = [f'<div data-id="{c["id"]}">{(ROOT / "data" / c["figure"]["file"]).read_text(encoding="utf-8")}</div>'
        for c in concepts if c.get('figure')]
j = lambda o: json.dumps(o, ensure_ascii=False).replace('</', '<\\/')
out = (shell.replace('<!--CONCEPTS-->', j(concepts))
            .replace('<!--QUIZZES-->', j(quizzes))
            .replace('<!--FIGS-->', '\n'.join(figs)))
(SC / 'parkchan-app.html').write_text(out, encoding='utf-8')
print(f'{len(out)//1024} KB · 개념 {len(concepts)} · 문항 {len(quizzes)} · 그림 {len(figs)}')

#!/usr/bin/env python3
"""제형 갈래 — 약 이름에서 «어떤 모양의 약인지»를 가려낸다.

사진을 붙일 때도, 허가 용법을 나란히 놓을 때도 같은 잣대를 쓴다.
겔 자리에 파스 용법이, 로션 자리에 알약 사진이 붙는 사고를 막는 것이 목적이다.

괄호 안 성분명을 먼저 떼야 한다 — 그러지 않으면 「염**산**염」의 산이 가루약으로 잡힌다.
"""
import re

def norm(s):
    s = re.sub(r'\(.*?\)', '', str(s))
    s = re.sub(r'[\s·,／/]+', '', s).lower()
    s = re.sub(r'(\d+)\s*mg', r'\1밀리그램', s)
    return s.replace('밀리그람', '밀리그램').replace('미리그램', '밀리그램')

FORMPAT = (
    ('eye',    r'점안|안연고'),
    ('nasal',  r'나잘|비강|점비'),
    ('spray',  r'스프레이|분무|네뷸라이저'),
    ('patch',  r'파스|파프|카타플라스마|플라스타|첩부|패치|패취|경고제'),
    ('insert', r'질정$|좌약$|좌제$'),
    ('nail',   r'네일|라카$'),
    ('skin',   r'연고$|크림$|로션$|겔$|외용액$'),
    ('troche', r'트로키$|츄어블'),
    ('liquid', r'시럽$|현탁액$|내복액$|드링크$|액$'),
    ('powder', r'산$|과립$|세립$|건조시럽$'),
)

def formclass(t):
    """정·캡슐 등 «먹는 고형제»가 기본값(solid)."""
    x = re.sub(r'[\d.]+\s*%?$', '', norm(t))
    for name, pat in FORMPAT:
        if re.search(pat, x): return name
    return 'solid'

LABEL = {'eye': '눈에 넣는 약', 'nasal': '코에 뿌리는 약', 'spray': '뿌리는 약', 'patch': '붙이는 약', 'insert': '넣는 약',
         'nail': '바르는 네일', 'skin': '바르는 약', 'troche': '입에서 녹이는 약',
         'liquid': '마시는 약', 'powder': '가루약', 'solid': '먹는 약'}

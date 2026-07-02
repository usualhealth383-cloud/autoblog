"""에이전트 task .output(JSONL 트랜스크립트)에서 기사 JSON을 추출해 data/premium/{slug}.json 저장.
내 컨텍스트로 안 읽고 스크립트가 파싱한다."""
import json
import sys
from pathlib import Path

sys.path.insert(0, "src")
sys.stdout.reconfigure(encoding="utf-8")
from auto_blog import config

TASKS = Path(r"C:\Users\parkh\AppData\Local\Temp\claude\C--Users-parkh-OneDrive-capcut\38e91bef-8408-46a0-a2b3-b8effe998ed4\tasks")
OUT = config.DATA_DIR / "premium"
OUT.mkdir(parents=True, exist_ok=True)


def balanced_json(text):
    """text에서 'slug'+'sections' 가진 균형 잡힌 JSON 오브젝트를 찾아 반환."""
    i = text.find("{")
    while i != -1:
        depth = 0
        for j in range(i, len(text)):
            c = text[j]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    cand = text[i:j + 1]
                    try:
                        obj = json.loads(cand)
                        if isinstance(obj, dict) and "slug" in obj and "sections" in obj:
                            return obj
                    except Exception:
                        pass
                    break
        i = text.find("{", i + 1)
    return None


def texts_from_entry(entry, acc):
    """트랜스크립트 엔트리에서 모든 text 필드 수집."""
    if isinstance(entry, dict):
        for k, v in entry.items():
            if k == "text" and isinstance(v, str):
                acc.append(v)
            else:
                texts_from_entry(v, acc)
    elif isinstance(entry, list):
        for x in entry:
            texts_from_entry(x, acc)


saved = []
for f in sorted(TASKS.glob("*.output")):
    all_texts = []
    for line in f.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except Exception:
            continue
        texts_from_entry(entry, all_texts)
    # 뒤에서부터 slug 가진 텍스트 찾기
    article = None
    for t in reversed(all_texts):
        if '"slug"' in t and '"sections"' in t:
            article = balanced_json(t)
            if article:
                break
    if article:
        slug = article.get("slug", f.stem)
        (OUT / f"{slug}.json").write_text(json.dumps(article, ensure_ascii=False, indent=2), encoding="utf-8")
        n = sum(len(p) for s in article.get("sections", []) for p in s.get("paragraphs", []))
        saved.append((slug, n, len(article.get("sections", [])), bool(article.get("table")), len(article.get("sources", []))))

print("추출 저장:", len(saved), "개")
for slug, n, secs, tbl, src in saved:
    print(f"  {slug}: {n}자, 섹션 {secs}, 표 {'O' if tbl else 'X'}, 출처 {src}개")

"""매일 1회 실행 — 자동 생성 + 엄격검증 + 발행 + 텔레그램 보고.

승인 버튼 없이 바로 발행하므로 writer 의 엄격 게이트(write_article_safe)로 안전성을
최대한 확보한다. GitHub Actions cron 등에서 하루 한 번 호출하도록 설계됨.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import base64 as _b64  # noqa: E402
import os  # noqa: E402

import requests  # noqa: E402

from auto_blog import config, pipeline, publishers, telegram_bot  # noqa: E402


def _host_images_on_github(rec: dict, post_dir):
    """생성 이미지를 GitHub Contents API 로 직접 업로드해 raw 공개 URL 을 만든다.

    git push 가 아니라 API 라서 동시 커밋이 있어도 서버가 순서를 처리 → 푸시 거부(race)가
    구조적으로 발생하지 않는다. Actions 밖이거나 일부라도 실패하면 빈 dict → base64 폴백
    (이미지가 절대 깨지지 않게)."""
    repo = os.environ.get("GITHUB_REPOSITORY")
    token = os.environ.get("GITHUB_TOKEN")
    images = rec.get("images") or {}
    if not repo or not token or not images:
        return {}
    urls = {}
    for idx, rel in images.items():
        src = post_dir / rel
        if not src.exists():
            continue
        path = f"public/{rec['dir']}/{os.path.basename(rel)}"
        try:
            r = requests.put(
                f"https://api.github.com/repos/{repo}/contents/{path}",
                headers={"Authorization": f"token {token}",
                         "Accept": "application/vnd.github+json"},
                json={"message": f"image: {path}",
                      "content": _b64.b64encode(src.read_bytes()).decode(),
                      "branch": "main"},
                timeout=60)
        except requests.RequestException as e:
            print(f"  [경고] 이미지 업로드 오류: {e}")
            r = None
        if r is not None and r.status_code in (200, 201):
            urls[str(idx)] = f"https://raw.githubusercontent.com/{repo}/main/{path}"
        else:
            code = r.status_code if r is not None else "ERR"
            print(f"  [경고] 이미지 업로드 실패({code}) → base64 폴백")
    # 전부 성공해야 URL 사용(일부 실패면 일관성 위해 base64 폴백)
    if len(urls) != len(images):
        return {}
    print(f"  이미지 {len(urls)}장 공개 URL 호스팅 완료(API, 충돌 불가)")
    return urls


def _gh_put_file(repo: str, token: str, path: str, content: str, message: str) -> bool:
    """GitHub Contents API 로 파일을 덮어쓴다(기존 파일이면 sha 조회 후 갱신)."""
    h = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    sha = None
    try:
        g = requests.get(url, headers=h, timeout=30)
        if g.status_code == 200:
            sha = g.json().get("sha")
    except requests.RequestException:
        pass
    body = {"message": message, "branch": "main",
            "content": _b64.b64encode(content.encode("utf-8")).decode()}
    if sha:
        body["sha"] = sha
    try:
        r = requests.put(url, headers=h, json=body, timeout=60)
        return r.status_code in (200, 201)
    except requests.RequestException:
        return False


def _blog_url(results: dict) -> str:
    blog = str(results.get("blogger", ""))
    return blog.split("발행됨:")[-1].strip() if "발행됨:" in blog else ""


def _update_naver_page(rec: dict, results: dict, naver_variant: dict):
    """오늘 글을 '네이버 복붙' 페이지가 읽을 latest_naver.json 으로 올린다(중복회피 변형본 반영)."""
    repo = os.environ.get("GITHUB_REPOSITORY")
    token = os.environ.get("GITHUB_TOKEN")
    if not repo or not token:
        return
    import datetime
    import json
    from auto_blog import formatter
    article = rec["article"]
    imgs = {int(k): v for k, v in (rec.get("image_urls") or {}).items()}
    # 네이버용: 새 제목 + 새 도입문단 + 본문(중복 회피)
    title = naver_variant.get("title") or article.get("title", "")
    lead = naver_variant.get("lead", "")
    lead_html = (f'<p style="font-size:17px;line-height:1.9;margin:0 0 18px">'
                 f'{lead}</p>') if lead else ""
    tags = article.get("tags", []) or []
    hashtags = " ".join("#" + str(t).replace(" ", "") for t in tags)
    # 본문 맨 끝에 해시태그 → '본문 전체 복사' 한 번에 글+사진+태그가 같이 들어감
    tag_html = (f'<p style="color:#1a73e8;margin-top:22px">{hashtags}</p>') if hashtags else ""
    # 네이버는 블로거 원문과 다른 ~2000자 재서술본을 쓴다(중복 콘텐츠 회피).
    nv_sections = naver_variant.get("sections") or []
    if nv_sections:
        url_list = [v for _, v in sorted(imgs.items())]   # 이미지 순서대로 재배치
        nv_imgs = {i: url_list[i] for i in range(min(len(url_list), len(nv_sections)))}
        naver_article = {"title": title, "sections": nv_sections,
                         "tags": tags, "disclaimer": article.get("disclaimer", "")}
        body_core = formatter.render_body(naver_article, nv_imgs, ads=False)
    else:  # 변형 실패 시 원문 본문으로 폴백
        body_core = formatter.render_body(article, imgs, ads=False)
    body_html = lead_html + body_core + tag_html
    tag_line = hashtags
    data = {"title": title, "body_html": body_html, "tags": tag_line,
            "url": _blog_url(results), "date": datetime.date.today().isoformat()}
    ok = _gh_put_file(repo, token, "latest_naver.json",
                      json.dumps(data, ensure_ascii=False), "naver: 최신 글 갱신")
    print("  네이버 복붙 페이지 갱신:", "완료" if ok else "실패")


def main():
    rec = pipeline.run_auto()
    post_dir = config.DATA_DIR / "posts" / rec["dir"]

    # 이미지를 공개 URL 로 호스팅(가능하면) → 본문이 가벼워지고 구글 이미지검색 노출
    rec["image_urls"] = _host_images_on_github(rec, post_dir)

    print("⑥ 발행 중…")
    results = publishers.publish(rec, post_dir)
    rec["status"] = "published"
    rec["publish_results"] = results
    import json
    (post_dir / "article.json").write_text(
        json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    for k, v in results.items():
        print(f"  {k}: {v}")

    # 채널 변형본 생성(스레드·네이버)
    from auto_blog import variants
    from auto_blog.publishers import threads_upload
    from auto_blog.publishers import instagram_upload
    article = rec["article"]
    blog_url = _blog_url(results)
    try:
        nv = variants.make_naver(article)
    except Exception as e:
        print("  [경고] 네이버 변형 실패:", e)
        nv = {"title": article.get("title", ""), "lead": ""}
    try:
        tv = variants.make_threads(article)
        threads_text = (tv["text"] + "\n\n" + blog_url
                        + "\n" + " ".join(tv.get("hashtags", []))).strip()
    except Exception as e:
        print("  [경고] 스레드 변형 실패:", e)
        threads_text = ""
    rec["threads_text"] = threads_text
    try:
        summary = variants.make_summary(article)
    except Exception as e:
        print("  [경고] 요약 실패:", e)
        summary = ""

    # 네이버 복붙 페이지 갱신(변형본 반영)
    _update_naver_page(rec, results, nv)

    # 스레드·인스타 자동 게시(토큰 있을 때만)
    imgs = rec.get("image_urls") or {}
    thumb = imgs.get("0") or (next(iter(imgs.values())) if imgs else None)
    if threads_text and threads_upload.configured():
        msg = threads_upload.post(threads_text, thumb)
        print("  스레드:", msg)
        results["threads"] = msg
    # 인스타는 이미지 필수 + 명시적 활성화(IG_ENABLED=true)일 때만. 현재 OFF(요청).
    if (str(config.get("IG_ENABLED", "")).lower() == "true"
            and threads_text and thumb and instagram_upload.configured()):
        msg = instagram_upload.post(threads_text, thumb)
        print("  인스타:", msg)
        results["instagram"] = msg
    else:
        print("  인스타: 건너뜀(IG_ENABLED 아님)")

    print("⑦ 텔레그램 보고…")
    telegram_bot.send_report(rec, results, threads_text=threads_text, summary=summary)
    print("완료 ✅")


if __name__ == "__main__":
    main()

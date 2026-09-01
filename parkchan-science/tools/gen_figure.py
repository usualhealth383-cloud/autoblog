"""나노바나나(제미나이 이미지)로 교재용 삽화 생성.

사용: GEMINI_API_KEY=... python gen_figure.py <프롬프트파일.txt> <출력.png>
autoblog의 src/auto_blog/images.py와 같은 방식(google-genai SDK, gemini-2.5-flash-image).

역할 분담 원칙:
- 도표·그래프·개념도·실험 장치도 = SVG 직접 제작 (정확성·인쇄 벡터 품질)
- 단원 도입 일러스트, 배경, 실물 묘사(세포·지형·기구 사진풍) = 나노바나나
- 생성 이미지는 반드시 과학적 사실 검수 후 사용 (라벨·글자는 이미지에 넣지 않고
  조판 단계에서 SVG/HTML 텍스트로 얹는다 — AI 이미지의 글자 왜곡 방지)
"""
import os, sys, pathlib

def generate(prompt: str, dest: pathlib.Path, model: str | None = None) -> None:
    from google import genai  # pip install google-genai
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        sys.exit("GEMINI_API_KEY가 없습니다. 환경변수로 설정해 주세요.")
    client = genai.Client(api_key=api_key)
    model = model or os.environ.get("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")
    resp = client.models.generate_content(model=model, contents=prompt)
    for part in resp.candidates[0].content.parts:
        data = getattr(getattr(part, "inline_data", None), "data", None)
        if data:
            dest.write_bytes(data)
            print(f"저장: {dest} ({len(data)} bytes)")
            return
    sys.exit("응답에 이미지가 없습니다.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    prompt = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
    generate(prompt, pathlib.Path(sys.argv[2]))

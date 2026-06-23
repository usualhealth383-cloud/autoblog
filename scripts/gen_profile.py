import base64
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from auto_blog import config
from openai import OpenAI

c = OpenAI(api_key=config.OPENAI_API_KEY)
prompt = (
    "Modern minimal flat logo icon for a friendly lifestyle and money-tips blog. "
    "A cute rounded lightbulb with a small fresh green leaf sprout growing from the top, "
    "symbolizing bright ideas and growth. Warm golden-yellow lightbulb, vivid green leaf. "
    "Soft light mint-cream circular background. Flat vector illustration, clean and simple, "
    "centered, friendly and approachable, app-icon style, no text, no letters, high resolution."
)
r = c.images.generate(model="gpt-image-1", prompt=prompt, size="1024x1024",
                      quality="high", n=1)
data = base64.b64decode(r.data[0].b64_json)
out = ROOT / "data" / "usual_sense_profile.png"
out.write_bytes(data)
print("생성 완료:", out, len(data) // 1024, "KB")

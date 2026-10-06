"""플레이리스트 영상 빌더 — Suno로 받은 곡 폴더 + 커버 이미지 1장 → 유튜브 업로드용 mp4 + 챕터 목록.

사용법 (제작 PC):
    python build_playlist.py --tracks ./001/tracks --image ./001/cover.png --out ./001/playlist_001.mp4
    python build_playlist.py ... --repeat 3          # 수면용: 곡 목록을 3회 반복해 길게
    python build_playlist.py ... --titles ./001/titles.txt   # 한 줄에 곡 제목 하나(파일명 순서와 동일)

- 곡은 파일명 순서대로 이어 붙인다(01_xxx.mp3, 02_xxx.mp3 ...). mp3/wav/m4a/flac 지원.
- 곡 사이 크로스페이드(기본 4초), 끝 10초 페이드아웃, 음량 정규화(기본 -16 LUFS).
- 결과: <out>.mp4 와 <out>_chapters.txt (유튜브 설명란에 그대로 붙여넣으면 챕터 생성).
"""
import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

AUDIO_EXT = {".mp3", ".wav", ".m4a", ".flac", ".ogg"}


def probe_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def fmt_time(sec):
    sec = int(sec)
    h, m, s = sec // 3600, sec % 3600 // 60, sec % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--tracks", required=True)
    p.add_argument("--image", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--titles")
    p.add_argument("--crossfade", type=float, default=4.0)
    p.add_argument("--repeat", type=int, default=1)
    p.add_argument("--lufs", type=float, default=-16.0)
    args = p.parse_args()

    files = sorted(f for f in Path(args.tracks).iterdir() if f.suffix.lower() in AUDIO_EXT)
    if len(files) < 2:
        sys.exit("곡이 2개 이상 필요합니다.")
    if args.titles:
        titles = [t.strip() for t in Path(args.titles).read_text(encoding="utf-8").splitlines() if t.strip()]
        if len(titles) != len(files):
            sys.exit(f"제목 {len(titles)}개 ≠ 곡 {len(files)}개 — 개수를 맞춰주세요.")
    else:
        titles = [f.stem.split("_", 1)[-1] for f in files]

    files, titles = files * args.repeat, titles * args.repeat
    durs = [probe_duration(f) for f in files]
    xf = args.crossfade
    if min(durs) <= xf * 2:
        sys.exit("크로스페이드보다 너무 짧은 곡이 있습니다.")

    # 챕터 시작 시각: 앞 곡들 길이 합 - 겹친 크로스페이드
    starts, t = [], 0.0
    for d in durs:
        starts.append(t)
        t += d - xf
    total = t + xf

    # 오디오: acrossfade 체인 → 끝 페이드아웃 → 음량 정규화
    inputs, chain = [], []
    for f in files:
        inputs += ["-i", str(f)]
    prev = "[0:a]"
    for i in range(1, len(files)):
        label = f"[a{i}]"
        chain.append(f"{prev}[{i}:a]acrossfade=d={xf}:c1=tri:c2=tri{label}")
        prev = label
    chain.append(f"{prev}afade=t=out:st={max(total - 10, 0):.2f}:d=10,"
                 f"loudnorm=I={args.lufs}:TP=-1.5:LRA=11,aresample=48000[aout]")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        audio = Path(tmp) / "mix.m4a"
        subprocess.run(["ffmpeg", "-y", "-v", "error", *inputs,
                        "-filter_complex", ";".join(chain), "-map", "[aout]",
                        "-c:a", "aac", "-b:a", "256k", str(audio)], check=True)
        # 영상: 정지 이미지 1080p, 1fps(긴 영상도 인코딩 빠르고 용량 작음)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-framerate", "1",
                        "-i", args.image, "-i", str(audio),
                        "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,"
                               "pad=1920:1080:(ow-iw)/2:(oh-ih)/2,format=yuv420p",
                        "-c:v", "libx264", "-tune", "stillimage", "-preset", "medium",
                        "-c:a", "copy", "-shortest", "-movflags", "+faststart", str(out)], check=True)

    chapters = "\n".join(f"{fmt_time(s)} {tt}" for s, tt in zip(starts, titles))
    ch_path = out.with_name(out.stem + "_chapters.txt")
    ch_path.write_text(chapters + "\n", encoding="utf-8")
    print(f"완료: {out}  (총 {fmt_time(total)}, {len(files)}곡)\n챕터: {ch_path}\n\n{chapters}")


if __name__ == "__main__":
    main()

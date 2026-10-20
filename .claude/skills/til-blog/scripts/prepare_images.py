"""_inbox 사진을 블로그용으로 변환합니다.

HEIC/JPG/PNG → JPG, 가로 최대 1600px, 약 300KB 이하, EXIF(GPS 포함) 제거.
결과는 assets/images/posts/{slug}/01.jpg, 02.jpg ... 순서로 저장합니다.

사용:
    python prepare_images.py <inbox 폴더> <slug> <저장소 루트> [--order a.jpg,b.jpg,...]

--order를 주지 않으면 파일명 앞 번호 순, 번호가 없으면 촬영 시각 순으로 정렬합니다.
"""

import argparse
import io
import json
import re
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageOps
from pillow_heif import register_heif_opener

register_heif_opener()

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".webp"}
MAX_WIDTH = 1600
TARGET_BYTES = 300 * 1024
EXIF_DATETIME_ORIGINAL = 36867


def taken_at(path: Path) -> datetime:
    """촬영 시각(EXIF)을 읽고, 없으면 파일 수정 시각을 돌려줍니다."""
    try:
        with Image.open(path) as im:
            raw = im.getexif().get_ifd(0x8769).get(EXIF_DATETIME_ORIGINAL)
        if raw:
            return datetime.strptime(raw, "%Y:%m:%d %H:%M:%S")
    except (OSError, ValueError):
        pass
    return datetime.fromtimestamp(path.stat().st_mtime)


def sort_key(path: Path) -> tuple:
    m = re.match(r"^(\d+)", path.stem)
    # 번호가 붙은 파일이 먼저, 그 안에서는 번호순. 번호 없는 파일은 촬영 시각순
    return (0, int(m.group(1)), "") if m else (1, 0, taken_at(path).isoformat())


def to_jpeg_bytes(path: Path) -> tuple[bytes, tuple[int, int]]:
    """회전 보정·리사이즈 후 EXIF 없이 JPEG로 인코딩합니다."""
    with Image.open(path) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
        if im.width > MAX_WIDTH:
            im = im.resize((MAX_WIDTH, round(im.height * MAX_WIDTH / im.width)), Image.LANCZOS)
        for quality in (85, 80, 75, 70, 65, 60):
            buf = io.BytesIO()
            im.save(buf, "JPEG", quality=quality, optimize=True, progressive=True)
            if buf.tell() <= TARGET_BYTES:
                break
        return buf.getvalue(), im.size


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("inbox")
    parser.add_argument("slug")
    parser.add_argument("repo")
    parser.add_argument("--order", help="쉼표로 구분한 원본 파일명 순서")
    args = parser.parse_args()

    inbox = Path(args.inbox)
    files = [p for p in inbox.iterdir() if p.suffix.lower() in IMAGE_EXTS]
    if args.order:
        by_name = {p.name: p for p in files}
        names = [n.strip() for n in args.order.split(",") if n.strip()]
        missing = [n for n in names if n not in by_name]
        if missing:
            raise SystemExit(f"--order에 없는 파일: {missing}")
        unlisted = sorted(set(by_name) - set(names))
        if unlisted:
            raise SystemExit(f"--order에서 빠진 사진: {unlisted} (쓰지 않을 사진은 _inbox에서 옮겨 두세요)")
        files = [by_name[n] for n in names]
    else:
        files.sort(key=sort_key)

    out_dir = Path(args.repo) / "assets" / "images" / "posts" / args.slug
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("*.jpg"):
        old.unlink()

    result = []
    for i, src in enumerate(files, 1):
        try:
            data, size = to_jpeg_bytes(src)
        except OSError as e:
            raise SystemExit(f"변환 실패: {src.name} ({e})") from e
        dst = out_dir / f"{i:02d}.jpg"
        dst.write_bytes(data)
        result.append({
            "source": src.name,
            "output": f"/assets/images/posts/{args.slug}/{dst.name}",
            "size_kb": round(len(data) / 1024),
            "width": size[0],
            "height": size[1],
        })

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

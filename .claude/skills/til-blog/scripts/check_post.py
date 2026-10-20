"""배포 전에 글 파일을 검사합니다. 문제가 있으면 목록을 출력하고 종료 코드 1을 돌려줍니다.

사용:
    python check_post.py <글 파일 경로> <저장소 루트>
"""

import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

KST = timezone(timedelta(hours=9))
SLUG_PERMALINK = re.compile(r"^/[a-z0-9]+(-[a-z0-9]+)+/$")
IMAGE_REF = re.compile(r"""\{\{\s*['"](/assets/[^'"]+)['"]\s*\|\s*relative_url\s*\}\}""")


def front_matter(text: str) -> dict:
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not m:
        raise ValueError("front matter(---)가 없습니다")
    return yaml.safe_load(m.group(1)) or {}


def main() -> None:
    post, repo = Path(sys.argv[1]), Path(sys.argv[2])
    text = post.read_text(encoding="utf-8")
    errors = []

    try:
        fm = front_matter(text)
    except (ValueError, yaml.YAMLError) as e:
        print(f"- {e}")
        sys.exit(1)

    for key in ("title", "date", "categories", "tags", "permalink"):
        if not fm.get(key):
            errors.append(f"front matter에 {key}가 없습니다")

    permalink = str(fm.get("permalink", ""))
    if permalink and not SLUG_PERMALINK.match(permalink):
        errors.append(f"permalink가 영문 슬러그 형식이 아닙니다 (예: /hackathon-2026-review/): {permalink}")

    # 다른 글과 주소 중복 검사
    for other in (repo / "_posts").rglob("*.md"):
        if other.resolve() == post.resolve():
            continue
        m = re.search(r"^permalink:\s*(\S+)", other.read_text(encoding="utf-8"), re.M)
        if m and m.group(1) == permalink:
            errors.append(f"permalink가 다른 글과 겹칩니다: {other.relative_to(repo)}")

    # 날짜가 미래면 Jekyll이 글을 만들지 않음
    date = fm.get("date")
    if isinstance(date, str):
        # "2026-10-20 21:30:00 +0900" 형식은 YAML이 문자열로 읽음
        try:
            date = datetime.strptime(date.strip(), "%Y-%m-%d %H:%M:%S %z")
        except ValueError:
            errors.append(f"date 형식이 'YYYY-MM-DD HH:MM:SS +0900'이 아닙니다: {date}")
    if isinstance(date, datetime):
        if date.tzinfo is None:
            date = date.replace(tzinfo=KST)
        if date > datetime.now(KST):
            errors.append(f"date가 미래 시각이라 글이 게시되지 않습니다: {date}")

    # 본문·대표 이미지 경로가 실제로 있는지
    refs = IMAGE_REF.findall(text)
    teaser = (fm.get("header") or {}).get("teaser")
    if teaser:
        refs.append(teaser)
    for ref in refs:
        if not (repo / ref.lstrip("/")).is_file():
            errors.append(f"이미지 파일이 없습니다: {ref}")

    if errors:
        print("\n".join(f"- {e}" for e in errors))
        sys.exit(1)
    print(f"OK: {post.name} (이미지 {len(refs)}개 확인)")


if __name__ == "__main__":
    main()

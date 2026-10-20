"""초안 글을 로컬 HTML 미리보기로 만듭니다. 배포하지 않으므로 GitHub에 기록이 남지 않습니다.

사용:
    python build_preview.py <글 파일 경로> <저장소 루트> <출력 html 경로>
"""

import html
import re
import sys
from pathlib import Path

import markdown
import yaml

IMAGE_REF = re.compile(r"""\{\{\s*['"](/assets/[^'"]+)['"]\s*\|\s*relative_url\s*\}\}""")

TEMPLATE = """<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>[미리보기] {title}</title>
<style>
  body {{ max-width: 760px; margin: 40px auto; padding: 0 16px; font-family: -apple-system, "Malgun Gothic", sans-serif;
         line-height: 1.8; color: #222; background: #fff; }}
  .meta {{ color: #888; font-size: 0.9em; margin-bottom: 2em; }}
  .banner {{ background: #fff4d6; padding: 8px 12px; border-radius: 6px; font-size: 0.85em; margin-bottom: 1.5em; }}
  img {{ max-width: 100%; border-radius: 6px; display: block; margin: 1em auto; }}
  h4 {{ margin-top: 2em; }}
  code {{ background: #f3f3f3; padding: 1px 4px; border-radius: 3px; }}
</style></head>
<body>
<div class="banner">로컬 미리보기입니다. 실제 블로그 테마와 글꼴·여백은 조금 다를 수 있습니다.</div>
<h1>{title}</h1>
<div class="meta">{date} · {categories} · {tags}<br>{permalink}</div>
{teaser}
{body}
</body></html>
"""


def main() -> None:
    post, repo, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    text = post.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.S)
    fm, body = yaml.safe_load(m.group(1)), m.group(2)

    # Liquid 이미지 경로를 로컬 파일 경로로 바꿈
    body = IMAGE_REF.sub(lambda x: (repo / x.group(1).lstrip("/")).resolve().as_uri(), body)
    teaser = (fm.get("header") or {}).get("teaser")
    teaser_html = ""
    if teaser:
        uri = (repo / teaser.lstrip("/")).resolve().as_uri()
        teaser_html = f'<p class="meta">대표 이미지(목록 썸네일)</p><img src="{uri}" style="max-width:320px">'

    out.write_text(TEMPLATE.format(
        title=html.escape(str(fm.get("title", ""))),
        date=fm.get("date", ""),
        categories=", ".join(fm.get("categories", [])),
        tags=", ".join(fm.get("tags", [])),
        permalink=html.escape(str(fm.get("permalink", ""))),
        teaser=teaser_html,
        body=markdown.markdown(body, extensions=["fenced_code", "tables"]),
    ), encoding="utf-8")
    print(out.resolve())


if __name__ == "__main__":
    main()

"""GA4에서 최근 30일 조회수 상위 글을 가져와 _data/top_posts.yml로 저장합니다.

GitHub Actions(.github/workflows/top-posts.yml)에서 매일 실행됩니다.

환경변수:
    GA_PROPERTY_ID: GA4 속성 ID (숫자)
    GOOGLE_APPLICATION_CREDENTIALS: 인증 정보 파일 경로 (워크플로의 google-github-actions/auth가 설정)
"""

import os
import re
from pathlib import Path

import yaml
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Filter,
    FilterExpression,
    Metric,
    OrderBy,
    RunReportRequest,
)

TOP_N = 5
BASEURL = "/TIL"
# 글 주소만 집계. 홈·카테고리·태그 페이지는 제외
#   코테 풀이: /TIL/{사이트}/{묶음}/{번호}/  (예: /TIL/pgs/basic/78/)
#   블로그 글: /TIL/{영문-슬러그}/          (예: /TIL/hackathon-2026-review/, 하이픈 1개 이상)
POST_PATH_REGEX = rf"^{BASEURL}/((pgs|ssql)/[a-z0-9-]+/[0-9]+|[a-z0-9]+(-[a-z0-9]+)+)/$"
TITLE_SUFFIX = " - Eunalog; Today I Learned"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "_data" / "top_posts.yml"


def fetch_top_posts(property_id: str) -> list[dict]:
    """
    최근 30일 조회수 기준 상위 글 목록을 가져옵니다.

    Args:
        property_id: GA4 속성 ID

    Returns:
        list[dict]: title, url, views를 담은 글 목록 (조회수 내림차순)
    """
    client = BetaAnalyticsDataClient()
    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[Dimension(name="pagePath"), Dimension(name="pageTitle")],
        metrics=[Metric(name="screenPageViews")],
        date_ranges=[DateRange(start_date="30daysAgo", end_date="today")],
        dimension_filter=FilterExpression(
            filter=Filter(
                field_name="pagePath",
                string_filter=Filter.StringFilter(
                    match_type=Filter.StringFilter.MatchType.FULL_REGEXP,
                    value=POST_PATH_REGEX,
                ),
            )
        ),
        order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="screenPageViews"), desc=True)],
        limit=50,
    )
    response = client.run_report(request)

    # 같은 주소가 제목만 바뀌어 여러 줄로 나올 수 있어 주소 기준으로 합칩니다.
    posts: dict[str, dict] = {}
    for row in response.rows:
        path = row.dimension_values[0].value
        title = row.dimension_values[1].value.removesuffix(TITLE_SUFFIX).strip()
        views = int(row.metric_values[0].value)
        url = re.sub(rf"^{BASEURL}", "", path)
        if url in posts:
            posts[url]["views"] += views
        else:
            posts[url] = {"title": title, "url": url, "views": views}

    return sorted(posts.values(), key=lambda p: p["views"], reverse=True)[:TOP_N]


def main() -> None:
    property_id = os.environ.get("GA_PROPERTY_ID")
    if not property_id:
        raise SystemExit("GA_PROPERTY_ID 환경변수가 없습니다.")

    try:
        top_posts = fetch_top_posts(property_id)
    except Exception as e:
        raise SystemExit(f"GA4 조회 실패: {e}") from e

    OUTPUT_PATH.write_text(
        yaml.safe_dump(top_posts, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    print(f"{len(top_posts)}개 저장: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

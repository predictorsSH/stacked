import json
from datetime import date

import httpx
from pydantic import BaseModel, Field, ValidationError

from stacked.core.config import HN_API, HN_HIT_PER_PAGE, HN_NUM_COMMENTS, HN_POINTS, HN_TIMEOUT
from stacked.core.dates import day_bounds


class HNFetchError(Exception):
    """HN(Algolia) 수집이 실패했을 때 나는 예외."""


class HNParseError(Exception):
    """HN(Algolia) 파싱에 실패했을 때 나는 예외."""


class HNArticle(BaseModel):
    object_id: str = Field(description="아티클 ID")
    title: str = Field(description="아티클 제목")
    url: str | None = Field(description="원문 링크")
    created_at: str = Field(description="아티클 등록 시간")
    points: int = Field(description="아티클 점수")
    num_comments: int = Field(description="댓글 수")


def make_parameter(target_date: date, *, points: int = HN_POINTS, comments: int = HN_NUM_COMMENTS) -> dict:

    start, end = day_bounds(target_date)
    numeric_filters = f"created_at_i>={start},created_at_i<{end},(points>={points},num_comments>={comments})"

    return {"tags": "story", "numericFilters": numeric_filters, "hitsPerPage": HN_HIT_PER_PAGE}


def fetch_hackernews(parameter: dict, *, timeout: float = HN_TIMEOUT) -> dict:

    try:
        response = httpx.get(HN_API, params=parameter, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except httpx.TimeoutException as e:
        raise HNFetchError(f"응답 시간이 초과되었습니다 (timeout={timeout}s): {e}") from e
    except httpx.HTTPStatusError as e:
        raise HNFetchError(f"HTTP 에러 응답을 받았습니다 (status={e.response.status_code}): {e}") from e
    except httpx.RequestError as e:
        raise HNFetchError(f"요청에 실패했습니다: {e}") from e
    except json.JSONDecodeError as e:
        raise HNFetchError(f"응답을 JSON으로 해석할 수 없습니다: {e}") from e


def parse_hackernews(response: dict) -> list[HNArticle]:
    parsed = []

    try:
        hits = response["hits"]
    except KeyError as e:
        raise HNParseError(f"hits 목록이 존재하지 않습니다. {e}") from e

    for article in hits:
        try:
            parsed.append(
                HNArticle(
                    object_id=article["objectID"],
                    title=article["title"],
                    url=article.get("url"),
                    created_at=article["created_at"],
                    points=article["points"],
                    num_comments=article["num_comments"],
                )
            )
        except (KeyError, ValidationError) as e:
            raise HNParseError(f"아티클 파싱 실패. {e}") from e
    return parsed


def collect_hackernews(target: date) -> list[HNArticle]:
    parameter = make_parameter(target)
    response = fetch_hackernews(parameter=parameter)
    return parse_hackernews(response)

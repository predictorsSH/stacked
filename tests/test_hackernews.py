import json
from datetime import date

import httpx
import pytest
from pydantic import ValidationError

from stacked.core.config import HN_API, HN_HIT_PER_PAGE
from stacked.pipeline.source import hackernews
from stacked.pipeline.source.hackernews import (
    HNArticle,
    HNFetchError,
    HNParseError,
    fetch_hackernews,
    make_parameter,
    parse_hackernews,
)


def test_make_parameters():

    expected = {
        "tags": "story",
        "numericFilters": "created_at_i>=1794150000,created_at_i<1794236400,(points>=100,num_comments>=50)",
        "hitsPerPage": HN_HIT_PER_PAGE,
    }

    assert make_parameter(target_date=date(2026, 11, 9), points=100, comments=50) == expected


def test_fetch_hackernews_sends_params_and_returns_json(monkeypatch):
    calls = []

    def fake_get(url, **kwargs):
        calls.append((url, kwargs))
        return httpx.Response(200, json={"hits": [], "nHits": 0}, request=httpx.Request("GET", url))

    monkeypatch.setattr(hackernews.httpx, "get", fake_get)
    parameter = {"tags": "story"}
    result = fetch_hackernews(parameter, timeout=3)

    assert result == {"hits": [], "nHits": 0}
    assert calls == [(HN_API, {"params": parameter, "timeout": 3})]


def test_fetch_hackernews_timeout_exception(monkeypatch):

    def fake_get(url, **kwargs):
        raise httpx.ReadTimeout("...")

    monkeypatch.setattr(hackernews.httpx, "get", fake_get)

    with pytest.raises(HNFetchError) as e:
        fetch_hackernews(parameter={})

    assert isinstance(e.value.__cause__, httpx.TimeoutException)


def test_fetch_hackernews_status_error(monkeypatch):

    def fake_get(url, **kwargs):
        return httpx.Response(500, request=httpx.Request("GET", url))

    monkeypatch.setattr(hackernews.httpx, "get", fake_get)

    with pytest.raises(HNFetchError) as e:
        fetch_hackernews(parameter={})

    assert isinstance(e.value.__cause__, httpx.HTTPStatusError)


def test_fetch_hackernews_request_error(monkeypatch):

    def fake_get(url, **kwargs):
        raise httpx.ConnectError("...")

    monkeypatch.setattr(hackernews.httpx, "get", fake_get)

    with pytest.raises(HNFetchError) as e:
        fetch_hackernews(parameter={})

    assert isinstance(e.value.__cause__, httpx.ConnectError)


def test_fetch_hackernews_not_json(monkeypatch):

    def fake_get(url, **kwargs):
        return httpx.Response(200, text="not json", request=httpx.Request("GET", url))

    monkeypatch.setattr(hackernews.httpx, "get", fake_get)

    with pytest.raises(HNFetchError) as e:
        fetch_hackernews(parameter={})

    assert isinstance(e.value.__cause__, json.JSONDecodeError)


def test_parse_hackernews_return_hn_article():

    response = {
        "hits": [
            {
                "objectID": "1",
                "title": "some title",
                "url": "https://example.com",
                "created_at": "2099-99-99",
                "points": 100,
                "num_comments": 10,
                "children": [1, 2, 3],
            }
        ]
    }

    expected = HNArticle(
        object_id="1",
        title="some title",
        url="https://example.com",
        created_at="2099-99-99",
        points=100,
        num_comments=10,
    )

    assert parse_hackernews(response) == [expected]


def test_parse_hackernews_has_no_url():

    response = {
        "hits": [
            {
                "objectID": "1",
                "title": "some title",
                "created_at": "2099-99-99",
                "points": 100,
                "num_comments": 10,
                "children": [1, 2, 3],
            }
        ]
    }

    expected = HNArticle(
        object_id="1",
        title="some title",
        url=None,
        created_at="2099-99-99",
        points=100,
        num_comments=10,
    )

    assert parse_hackernews(response) == [expected]


def test_parse_hackernews_has_empty_hits():

    response = {"hits": []}

    expected = []

    assert parse_hackernews(response) == expected


def test_parse_hackernews_has_no_hits():

    response = {"nohits": []}

    with pytest.raises(HNParseError) as e:
        parse_hackernews(response)

    assert isinstance(e.value.__cause__, KeyError)


def test_parse_hackernews_with_validation_error():

    response = {
        "hits": [
            {
                "objectID": "1",
                "title": "some title",
                "created_at": "2099-99-99",
                "points": None,
                "num_comments": 10,
                "children": [1, 2, 3],
            }
        ]
    }

    with pytest.raises(HNParseError) as e:
        parse_hackernews(response)

    assert isinstance(e.value.__cause__, ValidationError)


def test_parse_hackernews_with_key_error():

    response = {
        "hits": [
            {
                "objectID": "1",
                "title": "some title",
                "created_at": "2099-99-99",
                "num_comments": 10,
                "children": [1, 2, 3],
            }
        ]
    }

    with pytest.raises(HNParseError) as e:
        parse_hackernews(response)

    assert isinstance(e.value.__cause__, KeyError)

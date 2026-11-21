import json
from datetime import date

import httpx
import pytest

from stacked.core.config import HN_API, HN_HIT_PER_PAGE
from stacked.pipeline.source import hackernews
from stacked.pipeline.source.hackernews import HNFetchError, fetch_hackernews, make_parameter


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

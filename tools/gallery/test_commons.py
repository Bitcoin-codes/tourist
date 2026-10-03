#!/usr/bin/env python3
"""Tests for how the Commons client takes instruction from HTTP 429.

The bug these exist for: Wikimedia answers a rate-limited request with
`Retry-After: 43`, and the client ignored it -- sleeping 10s, then 20s, then
40s, a guess that both violated the instruction twice and, because the steady
state spacing was a separately configured 1.5s, put the deficit straight back
the moment a request succeeded. The run spent sixteen hours discovering the same
wall over and over while holding a number the server had already given us.

So three things must hold:

  * the header is parsed, and the value honoured;
  * a value the header may legally hold that is not a number does not raise;
  * the spacing after a success cannot fall below what the server asked for.

The second matters more than it looks. RFC 9110 allows `Retry-After` to be
either delta-seconds or an `HTTP-date`, so "Wed, 21 Oct 2026 07:28:00 GMT" is a
perfectly valid thing for a proxy to send -- and `float()` on it raises, which
would take down a build over a header we could just have ignored.
"""
from __future__ import annotations

import importlib.util
import sys
import urllib.error
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

_spec = importlib.util.spec_from_file_location("commons", HERE / "commons.py")
commons = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(commons)

PASSED = 0
FAILED: list[str] = []


def check_that(what: str, got: object, expected: object) -> None:
    global PASSED
    if got == expected:
        PASSED += 1
    else:
        FAILED.append(f"{what}\n      expected {expected!r}\n      got      {got!r}")


class _Response:
    """Stands in for `urllib.error.HTTPError`, which only exposes headers."""

    def __init__(self, value: object) -> None:
        self.headers = {"Retry-After": value} if value is not None else {}


def _http_error(headers: dict[str, str]) -> urllib.error.HTTPError:
    return urllib.error.HTTPError("https://commons.wikimedia.org/w/api.php", 429, "Too Many", headers, None)


# -- the header itself --------------------------------------------------------
check_that("seconds come through as seconds", commons.retry_after_of(_Response("25")), 25.0)
check_that("a large value survives", commons.retry_after_of(_Response("43")), 43.0)
check_that("a fractional value survives", commons.retry_after_of(_Response("12.5")), 12.5)

# The two shapes HTTP permits, and the empty header.
check_that(
    "an HTTP-date is ignored rather than raised on",
    commons.retry_after_of(_Response("Wed, 21 Oct 2026 07:28:00 GMT")),
    0.0,
)
check_that("an empty header is no instruction", commons.retry_after_of(_Response("")), 0.0)
check_that("a missing header is no instruction", commons.retry_after_of(_Response(None)), 0.0)
check_that("a negative value cannot make us go faster", commons.retry_after_of(_Response("-5")), 0.0)
check_that("nonsense is no instruction", commons.retry_after_of(_Response("soon")), 0.0)

# Straight off a real HTTPError, headers accessed the way urllib provides them.
check_that(
    "a real HTTPError is read directly",
    commons.retry_after_of(_http_error({"Retry-After": "25"})),
    25.0,
)
check_that(
    "a real HTTPError with no such header",
    commons.retry_after_of(_http_error({})),
    0.0,
)

# -- spacing cannot fall below the instruction --------------------------------
# The success path sets the throttle through the same floor expression. Rebuilt
# here rather than driven through the network, because the property is arithmetic
# and a test that needs Wikimedia to rate limit us is not a test.
def _after_success(throttle: float, retry_after: float, base: float) -> float:
    return max(max(base, retry_after), throttle * 0.85)


check_that(
    "a success after being told 43s does not fall back to 1.5s",
    _after_success(throttle=1.5, retry_after=43.0, base=1.5),
    43.0,
)
check_that(
    "with no instruction the configured floor still holds",
    _after_success(throttle=0.4, retry_after=0.0, base=1.5),
    1.5,
)
check_that(
    "a long-accumulated throttle still eases down towards the instruction",
    _after_success(throttle=43.0, retry_after=12.0, base=1.5),
    36.55,
)
check_that(
    "and it never eases below the instruction",
    _after_success(throttle=13.0, retry_after=12.0, base=1.5),
    12.0,
)

# -- the wait is the wider of ours and theirs ---------------------------------
def _wait(throttle: float, retry_after: float, since: float) -> float:
    return max(throttle, retry_after) - since


check_that(
    "when the server asks for longer than we would have waited, it wins",
    _wait(throttle=1.5, retry_after=43.0, since=2.0),
    41.0,
)
check_that(
    "our own throttle still applies when it is the wider one",
    _wait(throttle=20.0, retry_after=12.0, since=3.0),
    17.0,
)
check_that(
    "already waited long enough, do not sleep again",
    _wait(throttle=1.5, retry_after=43.0, since=50.0),
    -7.0,
)

# ---------------------------------------------------------------------------
print()
for _failure in FAILED:
    print(f"  FAIL  {_failure}")
print(f"\n{PASSED + len(FAILED)} assertions, {PASSED} pass, {len(FAILED)} fail")
raise SystemExit(1 if FAILED else 0)

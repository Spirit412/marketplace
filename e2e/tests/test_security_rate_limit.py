"""Rate limiting and abuse protection.

Test IDs (TC-SEC-###) trace back to the QA test-plan artifact. This harness
talks to each service directly on its published port (see conftest.py) —
there is no "gateway" entry in SERVICES, so gateway-level throttling (100
req/min, per PLAN_gateway.md) is out of reach from here by design; it would
need a separate suite driven through the actual gateway process.
"""

from __future__ import annotations

import time
import uuid

import httpx
import pytest
from conftest import TIMEOUT, TRUST_ENV, base_url

# Default RATE_LIMIT_WINDOW_SECONDS (auth-service/.env) plus margin. Not
# discoverable over the public API, so hardcoded — see test_sec_020's comment.
_RATE_LIMIT_WINDOW_SECONDS = 60


class TestLoginBruteForce:
    def test_sec_020_login_is_throttled_after_threshold(self) -> None:
        """TC-SEC-020: POST /auth/login 429s once RATE_LIMIT_MAX_REQUESTS is
        hit for an IP, regardless of whether the credentials are correct.
        E2E confirmation of the auth-service-level unit test — exercised here
        purely over HTTP against the live stack.
        """
        status = httpx.get(
            f"{base_url('auth')}/auth/rate-limit-status",
            timeout=TIMEOUT,
            trust_env=TRUST_ENV,
        ).json()
        remaining_guess = 60 - status["current_count"]

        blocked = None
        # Drain whatever budget is left (bounded loop — the counter resets
        # only via TTL, so this must terminate even if the guess is off).
        for _ in range(max(remaining_guess, 0) + 2):
            resp = httpx.post(
                f"{base_url('auth')}/auth/login",
                json={"email": "nobody@marketplace.invalid", "password": "irrelevant"},
                timeout=TIMEOUT,
                trust_env=TRUST_ENV,
            )
            if resp.status_code == 429:
                blocked = resp
                break

        assert blocked is not None, (
            "expected a 429 once the login budget for this IP is exhausted"
        )

        # This harness is HTTP-only by design (see the module docstring /
        # conftest.py) — no Redis access to clear the counter directly. Every
        # other test file in this suite needs fresh /auth/login calls, so
        # leaving this IP throttled would poison whichever test happens to
        # run next (module/file execution order isn't something to rely on
        # for correctness). Wait out the window instead of racing it.
        time.sleep(_RATE_LIMIT_WINDOW_SECONDS + 1)
        recovered = httpx.post(
            f"{base_url('auth')}/auth/login",
            json={"email": "customer@marketplace.dev", "password": "Customer123!"},
            timeout=TIMEOUT,
            trust_env=TRUST_ENV,
        )
        assert recovered.status_code == 200, (
            "the rate limit window should have reset by now — if this still 429s, "
            "RATE_LIMIT_WINDOW_SECONDS is longer than assumed here"
        )


class TestOrderCreationSpam:
    def test_sec_021_order_creation_spam_is_bounded(
        self, clients: dict[str, httpx.Client]
    ) -> None:
        """TC-SEC-021: rapid, repeated order creation from one account should
        eventually be throttled, not accepted indefinitely.

        Uses customer2, not customer — this test intentionally exhausts the
        per-user order-creation budget, and customer is used for real order
        creation throughout the rest of this suite (see test_buyer_journey.py,
        test_security_idor.py). Isolating the account avoids poisoning those.
        """
        login = httpx.post(
            f"{base_url('auth')}/auth/login",
            json={"email": "customer2@marketplace.dev", "password": "Customer123!"},
            timeout=TIMEOUT,
            trust_env=TRUST_ENV,
        ).json()
        headers = {"Authorization": f"Bearer {login['access_token']}"}

        throttled = False
        for _ in range(35):
            resp = clients["order"].post(
                "/orders/",
                json={
                    "shipping_address": {"city": "Moscow"},
                    "payment_method": "MOCK",
                    "tax_strategy": "RU",
                },
                headers={
                    **headers,
                    "Idempotency-Key": f"e2e-spam-{uuid.uuid4().hex[:10]}",
                },
            )
            if resp.status_code == 429:
                throttled = True
                break
        assert throttled, "expected order creation to be rate-limited eventually"


class TestGatewayRateLimit:
    def test_sec_022_gateway_rate_limit_out_of_scope_for_this_harness(self) -> None:
        """TC-SEC-022: the Gateway's general 100 req/min limiter (see
        PLAN_gateway.md) cannot be exercised here — this harness talks to
        each service directly on its published port (see conftest.py's
        SERVICES map / module docstring), bypassing the gateway entirely by
        design. Would need a dedicated suite pointed at the gateway process.
        """
        pytest.skip(
            "gateway is not in this harness's SERVICES map — hits services directly"
        )

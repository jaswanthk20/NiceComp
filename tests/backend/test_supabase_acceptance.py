"""Run against a freshly seeded local Supabase after migrations. Never point at production."""

import os
import pytest
import httpx


@pytest.mark.skipif(
    not os.getenv("RUN_SUPABASE_ACCEPTANCE"),
    reason="Requires running local Supabase with seeded auth users",
)
def test_supabase_rls_blocks_other_customer_and_raw_storage():
    base = os.environ["ACCEPTANCE_SUPABASE_URL"]
    key = os.environ["ACCEPTANCE_SUPABASE_ANON_KEY"]
    if not base.startswith(("http://127.0.0.1:", "http://localhost:")):
        pytest.fail("Acceptance tests require local Supabase")
    tokens = []
    for email in ["customer@nicecomp.test", "other@nicecomp.test"]:
        response = httpx.post(
            base + "/auth/v1/token?grant_type=password",
            headers={"apikey": key},
            json={"email": email, "password": "Review-Only-2026!"},
        )
        response.raise_for_status()
        tokens.append(response.json()["access_token"])
    headers = [{"apikey": key, "Authorization": "Bearer " + t} for t in tokens]
    other = httpx.get(base + "/rest/v1/purchases?select=id", headers=headers[1]).json()[0]["id"]
    assert httpx.get(base + "/rest/v1/purchases?id=eq." + other, headers=headers[0]).json() == []
    profiles = httpx.get(base + "/rest/v1/customer_profiles?select=id", headers=headers[0]).json()
    response = httpx.patch(
        base + "/rest/v1/customer_profiles?id=eq." + profiles[0]["id"],
        headers=headers[0],
        json={"role": "admin"},
    )
    assert response.status_code in (401, 403)
    listing = httpx.post(
        base + "/storage/v1/object/list/private-support", headers=headers[0], json={"prefix": ""}
    )
    assert listing.status_code in (400, 401, 403) or listing.json() == []

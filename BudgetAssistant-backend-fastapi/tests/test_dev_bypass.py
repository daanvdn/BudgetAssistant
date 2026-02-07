import pytest

from config.settings import settings
from models.user import User


@pytest.mark.asyncio
async def test_dev_bypass_returns_user(client, async_session):
    """When DEV_AUTH_BYPASS is enabled and header is present, /api/auth/me returns a user."""
    # Ensure dev bypass is enabled for this test
    original_value = settings.DEV_AUTH_BYPASS
    settings.DEV_AUTH_BYPASS = True

    # Create a dev user in the test DB
    user = User(name="Dev Test User", email="dev@local.com", is_active=True)
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)

    # Call the protected endpoint with the dev bypass header
    headers = {settings.DEV_BYPASS_HEADER: "1"}
    response = await client.get("/api/auth/me", headers=headers)

    # Restore original setting
    settings.DEV_AUTH_BYPASS = original_value

    assert response.status_code == 200
    data = response.json()
    # Response should contain at least the user's email or name
    assert data.get("email") == "dev@local.com" or data.get("name") == "Dev Test User"


@pytest.mark.asyncio
async def test_dev_bypass_all_endpoints(client, async_session):
    """Test that all protected endpoints work with dev bypass header if a user exists."""
    # Enable dev bypass
    original_value = settings.DEV_AUTH_BYPASS
    settings.DEV_AUTH_BYPASS = True

    # Create a dev user in the test DB
    user = User(name="Dev Test User", email="dev@local.com", is_active=True)
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)

    headers = {settings.DEV_BYPASS_HEADER: "1"}

    # --- Auth endpoints ---
    # GET /api/auth/me
    resp = await client.get("/api/auth/me", headers=headers)
    assert resp.status_code == 200, f"/api/auth/me failed: {resp.status_code} - {resp.text}"

    # POST /api/auth/logout
    resp = await client.post("/api/auth/logout", headers=headers)
    assert resp.status_code == 200, f"/api/auth/logout failed: {resp.status_code} - {resp.text}"

    # --- Bank Accounts endpoints ---
    # GET /api/bank-accounts
    resp = await client.get("/api/bank-accounts", headers=headers)
    assert resp.status_code in (200, 204), f"/api/bank-accounts failed: {resp.status_code} - {resp.text}"

    # POST /api/bank-accounts
    resp = await client.post(
        "/api/bank-accounts",
        headers=headers,
        json={"account_number": "BE12345678901234", "alias": "Test Account"},
    )
    assert resp.status_code in (201, 400, 409), f"POST /api/bank-accounts failed: {resp.status_code} - {resp.text}"

    # GET /api/bank-accounts/{account_number}
    resp = await client.get("/api/bank-accounts/BE12345678901234", headers=headers)
    assert resp.status_code in (200, 404), f"GET /api/bank-accounts/{{id}} failed: {resp.status_code} - {resp.text}"

    # PATCH /api/bank-accounts/{account_number}
    resp = await client.patch(
        "/api/bank-accounts/BE12345678901234",
        headers=headers,
        json={"alias": "Updated Alias"},
    )
    assert resp.status_code in (200, 404), f"PATCH /api/bank-accounts/{{id}} failed: {resp.status_code} - {resp.text}"

    # POST /api/bank-accounts/save-alias
    resp = await client.post(
        "/api/bank-accounts/save-alias",
        headers=headers,
        json={"bank_account": "BE12345678901234", "alias": "New Alias"},
    )
    assert resp.status_code in (200, 404), (
        f"POST /api/bank-accounts/save-alias failed: {resp.status_code} - {resp.text}"
    )

    # DELETE /api/bank-accounts/{account_number}
    resp = await client.delete("/api/bank-accounts/BE12345678901234", headers=headers)
    assert resp.status_code in (200, 404), f"DELETE /api/bank-accounts/{{id}} failed: {resp.status_code} - {resp.text}"

    # --- Categories endpoints ---
    # GET /api/categories
    resp = await client.get("/api/categories", headers=headers)
    assert resp.status_code in (200, 204), f"/api/categories failed: {resp.status_code} - {resp.text}"

    # GET /api/categories/tree (requires query param)
    resp = await client.get("/api/categories/tree?transaction_type=EXPENSES", headers=headers)
    assert resp.status_code in (200, 404), f"/api/categories/tree failed: {resp.status_code} - {resp.text}"

    # GET /api/categories/{category_id}
    resp = await client.get("/api/categories/1", headers=headers)
    assert resp.status_code in (200, 404), f"GET /api/categories/{{id}} failed: {resp.status_code} - {resp.text}"

    # GET /api/categories/by-qualified-name/{qualified_name}
    resp = await client.get("/api/categories/by-qualified-name/test/category", headers=headers)
    assert resp.status_code in (200, 404), (
        f"GET /api/categories/by-qualified-name failed: {resp.status_code} - {resp.text}"
    )

    # --- Transactions endpoints ---
    # POST /api/transactions/page
    resp = await client.post(
        "/api/transactions/page",
        headers=headers,
        json={"query": {}, "page": 0, "size": 10, "sort_order": "asc", "sort_property": "transaction_id"},
    )
    assert resp.status_code in (200, 422), f"POST /api/transactions/page failed: {resp.status_code} - {resp.text}"

    # POST /api/transactions/page-in-context
    resp = await client.post(
        "/api/transactions/page-in-context",
        headers=headers,
        json={
            "query": {
                "bank_account": "BE12345678901234",
                "category_id": 1,
                "transaction_type": "EXPENSES",
                "period": "2023-01",
                "start_date": "2023-01-01",
                "end_date": "2023-01-31",
            },
            "page": 0,
            "size": 10,
            "sort_order": "asc",
            "sort_property": "transaction_id",
        },
    )
    assert resp.status_code in (200, 403, 404, 422), (
        f"POST /api/transactions/page-in-context failed: {resp.status_code} - {resp.text}"
    )

    # POST /api/transactions/page-uncategorized
    resp = await client.post(
        "/api/transactions/page-uncategorized",
        headers=headers,
        json={
            "bank_account": "BE12345678901234",
            "page": 0,
            "size": 10,
            "sort_order": "asc",
            "sort_property": "transaction_id",
            "transaction_type": "EXPENSES",
        },
    )
    assert resp.status_code in (200, 403, 404, 422), (
        f"POST /api/transactions/page-uncategorized failed: {resp.status_code} - {resp.text}"
    )

    # GET /api/transactions/count-uncategorized
    resp = await client.get(
        "/api/transactions/count-uncategorized?bank_account=BE12345678901234",
        headers=headers,
    )
    assert resp.status_code in (200, 403, 404), (
        f"GET /api/transactions/count-uncategorized failed: {resp.status_code} - {resp.text}"
    )

    # POST /api/transactions/save
    resp = await client.post(
        "/api/transactions/save?transaction_id=nonexistent",
        headers=headers,
        json={"category_id": 1},
    )
    assert resp.status_code in (200, 400, 404), f"POST /api/transactions/save failed: {resp.status_code} - {resp.text}"

    # POST /api/transactions/upload (multipart form)
    resp = await client.post(
        "/api/transactions/upload",
        headers=headers,
        files={"files": ("test.csv", b"header\nvalue", "text/csv")},
    )
    assert resp.status_code in (200, 400, 422), (
        f"POST /api/transactions/upload failed: {resp.status_code} - {resp.text}"
    )

    # GET /api/transactions/distinct-counterparty-names
    resp = await client.get(
        "/api/transactions/distinct-counterparty-names?bank_account=BE12345678901234",
        headers=headers,
    )
    assert resp.status_code in (200, 403), (
        f"GET /api/transactions/distinct-counterparty-names failed: {resp.status_code} - {resp.text}"
    )

    # GET /api/transactions/distinct-counterparty-accounts
    resp = await client.get(
        "/api/transactions/distinct-counterparty-accounts?bank_account=BE12345678901234",
        headers=headers,
    )
    assert resp.status_code in (200, 403), (
        f"GET /api/transactions/distinct-counterparty-accounts failed: {resp.status_code} - {resp.text}"
    )

    # --- Analysis endpoints ---
    # POST /api/analysis/revenue-expenses-per-period
    resp = await client.post(
        "/api/analysis/revenue-expenses-per-period",
        headers=headers,
        json={
            "account_number": "BE12345678901234",
            "transaction_type": "EXPENSES",
            "start": "2023-01-01",
            "end": "2023-12-31",
            "grouping": "MONTH",
        },
    )
    assert resp.status_code in (200, 422), (
        f"POST /api/analysis/revenue-expenses-per-period failed: {resp.status_code} - {resp.text}"
    )

    # POST /api/analysis/revenue-expenses-per-period-and-category
    resp = await client.post(
        "/api/analysis/revenue-expenses-per-period-and-category",
        headers=headers,
        json={
            "account_number": "BE12345678901234",
            "transaction_type": "EXPENSES",
            "start": "2023-01-01",
            "end": "2023-12-31",
            "grouping": "MONTH",
        },
    )
    assert resp.status_code in (200, 422), (
        f"POST /api/analysis/revenue-expenses-per-period-and-category failed: {resp.status_code} - {resp.text}"
    )

    # POST /api/analysis/category-details-for-period
    resp = await client.post(
        "/api/analysis/category-details-for-period",
        headers=headers,
        json={
            "account_number": "BE12345678901234",
            "transaction_type": "EXPENSES",
            "start": "2023-01-01",
            "end": "2023-12-31",
            "grouping": "MONTH",
            "category_qualified_name": "test",
        },
    )
    assert resp.status_code in (200, 404, 422), (
        f"POST /api/analysis/category-details-for-period failed: {resp.status_code} - {resp.text}"
    )

    # GET /api/analysis/categories-for-account
    resp = await client.get(
        "/api/analysis/categories-for-account?bank_account=TEST123&transaction_type=EXPENSES",
        headers=headers,
    )
    assert resp.status_code in (200, 204), (
        f"/api/analysis/categories-for-account failed: {resp.status_code} - {resp.text}"
    )

    # POST /api/analysis/track-budget
    resp = await client.post(
        "/api/analysis/track-budget",
        headers=headers,
        json={
            "account_number": "BE12345678901234",
            "transaction_type": "EXPENSES",
            "start": "2023-01-01",
            "end": "2023-12-31",
            "grouping": "MONTH",
        },
    )
    assert resp.status_code in (200, 400, 404, 422), (
        f"POST /api/analysis/track-budget failed: {resp.status_code} - {resp.text}"
    )

    # GET /api/analysis/resolve-date-shortcut
    resp = await client.get("/api/analysis/resolve-date-shortcut?shortcut=previous%20month", headers=headers)
    assert resp.status_code == 200, f"/api/analysis/resolve-date-shortcut failed: {resp.status_code} - {resp.text}"

    # --- Budget endpoints ---
    # POST /api/budget/find-or-create
    resp = await client.post(
        "/api/budget/find-or-create",
        headers=headers,
        json={"bank_account_id": "BE12345678901234"},
    )
    assert resp.status_code in (200, 403, 404, 422), (
        f"POST /api/budget/find-or-create failed: {resp.status_code} - {resp.text}"
    )

    # GET /api/budget/{bank_account}
    resp = await client.get("/api/budget/BE12345678901234", headers=headers)
    assert resp.status_code in (200, 403, 404), (
        f"GET /api/budget/{{bank_account}} failed: {resp.status_code} - {resp.text}"
    )

    # PATCH /api/budget/entry/{node_id}
    resp = await client.patch(
        "/api/budget/entry/1",
        headers=headers,
        json={"amount": 100.0},
    )
    assert resp.status_code in (200, 403, 404), (
        f"PATCH /api/budget/entry/{{node_id}} failed: {resp.status_code} - {resp.text}"
    )

    # --- Rules endpoints ---
    # POST /api/rules/get-or-create
    resp = await client.post(
        "/api/rules/get-or-create",
        headers=headers,
        json={"category_qualified_name": "test/category", "type": "EXPENSES"},
    )
    assert resp.status_code in (200, 404, 422), (
        f"POST /api/rules/get-or-create failed: {resp.status_code} - {resp.text}"
    )

    # POST /api/rules/save
    resp = await client.post(
        "/api/rules/save",
        headers=headers,
        json={"category_id": 1, "rule_set": {}},
    )
    assert resp.status_code in (200, 404, 422), f"POST /api/rules/save failed: {resp.status_code} - {resp.text}"

    # PATCH /api/rules/{rule_set_id}
    resp = await client.patch(
        "/api/rules/1",
        headers=headers,
        json={"rule_set": {}},
    )
    assert resp.status_code in (200, 403, 404), (
        f"PATCH /api/rules/{{rule_set_id}} failed: {resp.status_code} - {resp.text}"
    )

    # GET /api/rules/{rule_set_id}
    resp = await client.get("/api/rules/1", headers=headers)
    assert resp.status_code in (200, 404), f"GET /api/rules/{{rule_set_id}} failed: {resp.status_code} - {resp.text}"

    # POST /api/rules/categorize-transactions
    resp = await client.post("/api/rules/categorize-transactions", headers=headers)
    assert resp.status_code in (200, 422), (
        f"POST /api/rules/categorize-transactions failed: {resp.status_code} - {resp.text}"
    )

    # Restore original setting
    settings.DEV_AUTH_BYPASS = original_value

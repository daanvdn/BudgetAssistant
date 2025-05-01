# How to Send a Request to PageTransactionsView from IntelliJ Ultimate

This guide explains how to send a request to the `PageTransactionsView` endpoint using IntelliJ Ultimate with the Python & Django plugin.

## Prerequisites

1. IntelliJ Ultimate with Python & Django plugin installed
2. BudgetAssistant-backend project opened in IntelliJ

## Steps to Send a Request

### 1. Create an HTTP Request File

1. Right-click on the project directory in IntelliJ
2. Select `New` > `HTTP Request`
3. Name the file (e.g., `page_transactions_request.http`)

### 2. Set Up Authentication

Since `PageTransactionsView` requires authentication (`permission_classes = [IsAuthenticated]`), you need to obtain a JWT token first:

```http
### Get JWT Token
POST http://localhost:8000/api/token/
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}

> {% client.global.set("auth_token", response.body.access); %}
```

### 3. Create the Request to PageTransactionsView

Add the following to your HTTP request file:

```http
### Send request to PageTransactionsView
POST http://localhost:8000/api/transactions/page
Content-Type: application/json
Authorization: Bearer {{auth_token}}

{
  "page": 0,
  "size": 10,
  "sort_order": "asc",
  "sort_property": "transaction_id",
  "query": {
    "transaction_type": "EXPENSES",
    "account_number": "your_account_number",
    "start_date": "2023-01-01",
    "end_date": "2023-12-31"
  }
}
```

### 4. Execute the Request

1. Click the green "Run" button next to either request in the HTTP file
2. First run the token request to authenticate
3. Then run the PageTransactionsView request

## Request Structure Explanation

The request to `PageTransactionsView` requires a JSON body with the following structure:

- `page`: Page number (starting from 0)
- `size`: Number of items per page
- `sort_order`: Sort direction ("asc" or "desc")
- `sort_property`: Field to sort by (options include "transaction_id", "booking_date", "amount", "counterparty", "category", etc.)
- `query`: A TransactionQuery object with the following optional fields:
  - `transaction_type`: "REVENUE", "EXPENSES", or "BOTH"
  - `counterparty_name`: Filter by counterparty name
  - `min_amount`: Minimum transaction amount
  - `max_amount`: Maximum transaction amount
  - `account_number`: Bank account number
  - `category_id`: Filter by category ID
  - `transaction_or_communication`: Search in transaction or communication fields
  - `counterparty_account_number`: Filter by counterparty account number
  - `start_date`: Start date for filtering (YYYY-MM-DD)
  - `end_date`: End date for filtering (YYYY-MM-DD)
  - `upload_timestamp`: Filter by upload timestamp
  - `manually_assigned_category`: Filter by manually assigned category (boolean)

## Response Structure

The response will be a JSON object with the following structure:

```json
{
  "content": [
    {
      "transaction_id": "...",
      "booking_date": "...",
      "amount": 0.0,
      "counterparty": {
        "name": "...",
        "account_number": "..."
      },
      "category": {
        "id": 0,
        "name": "...",
        "qualified_name": "..."
      },
      "manually_assigned_category": false,
      "is_recurring": false,
      "is_advance_shared_account": false,
      "upload_timestamp": "...",
      "is_manually_reviewed": false
    }
  ],
  "number": 0,
  "total_elements": 0,
  "size": 10
}
```

## Using Python Requests Library

Alternatively, you can use Python code with the requests library:

```python
import requests
import json

# Get JWT token
auth_response = requests.post(
    'http://localhost:8000/api/token/',
    json={
        'username': 'your_username',
        'password': 'your_password'
    }
)
token = auth_response.json()['access']

# Send request to PageTransactionsView
headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {token}'
}

data = {
    'page': 0,
    'size': 10,
    'sort_order': 'asc',
    'sort_property': 'transaction_id',
    'query': {
        'transaction_type': 'EXPENSES',
        'account_number': 'your_account_number',
        'start_date': '2023-01-01',
        'end_date': '2023-12-31'
    }
}

response = requests.post(
    'http://localhost:8000/api/transactions/page',
    headers=headers,
    json=data
)

print(json.dumps(response.json(), indent=2))
```
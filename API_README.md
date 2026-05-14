# Processor Language FastAPI

## Run

```bash
cd "C:\Users\user\OneDrive\Desktop\processor-traien\Processor-Assistant"
pip install -r requirements.txt
uvicorn api_server:app --reload --port 8000
```

## API Docs

- Swagger UI: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`
- Usage Dashboard: `http://localhost:8000/dashboard`

## Auth

Send `X-API-Key` header on every `/api/*` request.

## Create test customer

`POST /admin/customers`

```json
{
  "customer_id": "cust_001",
  "name": "Acme Mortgage",
  "plan": "59",
  "api_key": "acme_test_key_12345"
}
```

## Endpoints

- `POST /api/parse-document`
- `POST /api/translate-condition`
- `POST /api/generate-email`

All accept JSON and return JSON.

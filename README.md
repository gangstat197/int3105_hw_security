# Security Homework

## Run

Start Docker Desktop, then create the local configuration:

```sh
cp .env.example .env
```

Set `JWT_SECRET` and `GATEWAY_SECRET` in `.env` to two different values generated
with `openssl rand -hex 32`. Start the services:

```sh
docker compose up --build -d
```

## Test `/dashboard`

Log in through the gateway:

```sh
curl http://localhost:8080/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"password"}'
```

Copy `access_token` from the response, then run:

```sh
export TOKEN='<access_token>'
curl http://localhost:8080/dashboard -H "Authorization: Bearer $TOKEN"
```

Expected response:

```json
{"user":{"id":1,"name":"Alice"},"orders":[{"id":1,"user_id":1,"item":"Notebook"}]}
```

Use the same token to test `/users` and `/orders` at `http://localhost:8080`.
A missing or invalid token returns `401`; excessive requests return `429`.
API documentation is available at `http://localhost:8001/docs` and
`http://localhost:8002/docs`; send authenticated requests through the gateway.

## Test avatar uploads and checks

```sh
docker compose --profile storage up --build -d
```

Open `http://localhost:9001`, log in with the MinIO credentials from `.env`,
and create a private bucket named `avatars`. Default credentials:
`localadmin` / `local-development-password`.

Request an upload URL:

```sh
curl http://localhost:8080/users/me/avatar-upload-url \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"content_type":"image/png"}'
curl -X PUT '<upload_url>' -H 'Content-Type: image/png' --data-binary @avatar.png
```

Measure latency:

```sh
docker compose exec -T user-service python < scripts/benchmark.py
```

Local results (2026-10-27, 30 requests to `/users` per path):

| Path | Mean latency |
| --- | --- |
| Gateway, including JWT validation | 5.66 ms |
| Direct user service | 3.85 ms |

Gateway overhead: **1.81 ms**. Results vary with machine load.

Stop all services:

```sh
docker compose --profile storage down
```

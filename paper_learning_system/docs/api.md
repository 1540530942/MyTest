# API

## Health

```http
GET /api/health
```

## Papers

```http
GET /api/papers
POST /api/papers
GET /api/papers/{paper_id}
POST /api/papers/import
```

`GET /api/papers/{paper_id}` returns:

```json
{
  "paper": {},
  "notes": [],
  "practice_items": []
}
```

## Mining

```http
POST /api/mine
```

Body:

```json
{
  "seed": "attention is all you need transformer",
  "max_results": 8
}
```

When `HERMES_URL` and at least one provider key are configured, mining first asks Hermes to expand the seed into related discovery queries, then searches arXiv with those generated queries. If Hermes is unavailable, mining falls back to deterministic arXiv keyword search.

## Reference Pack

```http
GET /api/reference-papers
POST /api/reference-papers/import
```

`GET /api/reference-papers` returns local `research_notes` reference links normalized into dated paper records, sorted from oldest to newest.

Import selected references:

```json
{
  "ids": ["2604.06170v1"]
}
```

Import the full dated pack:

```json
{
  "ids": []
}
```

## Analysis

```http
POST /api/papers/{paper_id}/analyze
```

Body:

```json
{
  "force_llm": false
}
```

## Question Answering

```http
POST /api/papers/{paper_id}/question
```

Body:

```json
{
  "question": "What is the main contribution?"
}
```

## Practice

```http
POST /api/papers/{paper_id}/practice
```

Body:

```json
{
  "count": 8
}
```

Generated practice items are saved and returned later by `GET /api/papers/{paper_id}` so the study-pack page can reopen previous Q&A.

## Hermes Gateway

The paper app calls Hermes internally. Do not expose Hermes publicly.

```http
GET  http://paper-hermes:8091/api/health
GET  http://paper-hermes:8091/api/providers
POST http://paper-hermes:8091/api/chat-json
POST http://paper-hermes:8091/v1/chat/completions
```

See:

```text
docs/hermes-llm-gateway.md
```

## Authentication

If `API_TOKEN` is unset or equals `change-me-before-public-deploy`, local requests are allowed without auth.

When `API_TOKEN` is set to a real value, send:

```http
Authorization: Bearer <API_TOKEN>
```

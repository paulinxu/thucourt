# THUCourt — Technology Choices

## Proposed stack

The backend choice, Django, comes from `objective.md`. The remaining choices below are proposed for a small-team course project and should be pinned to compatible supported versions at project setup.

| Layer | Technology | Reason |
| --- | --- | --- |
| Backend language | Python 3.12 | Shared language for application logic, media processing, and AI orchestration. |
| Backend framework | Django 5.2 LTS and Django REST Framework | Mature ORM, authentication, permissions, migrations, API serializers, and built-in administration. |
| Frontend | React, TypeScript, Vite | Typed reusable interfaces for filters, grids, messaging, and coaching chat. |
| UI and server state | Tailwind CSS and TanStack Query | Consistent responsive styling and API caching/invalidation without a large custom state layer. |
| Persistent database | PostgreSQL | Relational constraints, transactional match confirmation, filtering, and aggregates. |
| Async work | Celery and Redis | Process uploads and model requests outside HTTP request lifetimes; expose job status to the client. |
| Media storage | Private S3-compatible object storage; local storage in development | Keep large files outside the database and serve authorized short-lived download URLs. |
| Image/video processing | Pillow and FFmpeg | Validate and resize images, inspect video metadata, and extract bounded frame samples. |
| Authentication | Django sessions, CSRF protection, and server-side WeChat OAuth integration | Keep application credentials out of browser storage; support same-origin deployment. |
| API contract | OpenAPI generated with drf-spectacular | Document endpoints and simplify frontend/backend integration. |
| Deployment | Docker Compose on a Linux VM, Nginx, Gunicorn | Simple deployment for the API, worker, database, queue, and frontend assets. |
| Quality checks | pytest/pytest-django, Vitest, Playwright, Ruff, TypeScript checks, GitHub Actions | Cover domain rules, key browser journeys, typing, and formatting/linting. |

Messaging between any verified students and notifications initially use incremental HTTP polling. This avoids introducing WebSocket infrastructure before the core product works. The UI should clearly distinguish pending, sent, and failed messages. Deliver the normal website first; reuse the REST API for a later WeChat Mini Program, with a separate client and platform-specific authentication adapter rather than assuming the React website becomes a Mini Program unchanged.

## AI model selection

**Proposed default: GPT-4.1 mini**, accessed server-side through its provider SDK, for two stages: (1) image/video-frame analysis into structured text observations and (2) coaching that combines those observations with written/numerical friend feedback, own match history, and previous training plans. **Proposed escalation: GPT-4.1** for a small number of harder image-grounded requests when evaluation demonstrates a benefit. These are planned choices, not evidence of an existing integration or guaranteed service availability.

Before implementation, confirm model availability, image support, pricing, network access from the deployment region, and course data-handling requirements. Keep model IDs and endpoints configurable behind a small provider adapter. If the proposed service is unavailable, choose an accessible text-and-image model and rerun the same evaluation set before switching.

### Model input strategy

- Text context: profile level, user goals, private written/numerical friend feedback, media-derived observations, recent training plans, and own official singles/doubles match summaries when relevant. Combine available sources in the same coaching task rather than forcing the student to choose feedback versus media.
- Images: validated user-selected photos or a bounded set of frames from an uploaded clip. Do not send entire video files to a text/image endpoint.
- Output: first a stored, owner-scoped media observation record with frame/time references and uncertainty; then conversational explanation or a validated structured plan with evidence references. Do not treat generated observations as verified facts.
- No custom training, GPU inference server, vector database, or multi-agent framework is required initially. Structured SQL retrieval is sufficient for a student's bounded data history.

### Video scope

For the final version, support short clips up to a proposed 60 seconds and 100 MB, extracting at most eight frames per analysis. The working version prioritizes text coaching and photo upload. Frame-based observations are approximate: they cannot establish precise racket speed, biomechanics, or medical diagnoses. Audio transcription and continuous motion analysis are outside the planned scope.

## Development and integration decisions

- Use a monorepo with `backend/`, `frontend/`, and deployment configuration.
- Keep domain logic in backend services shared by API views and AI tools; do not let the model generate SQL or invoke arbitrary functions.
- Store secrets in environment configuration; commit only example variable names.
- Record model name, prompt version, tool calls, token usage, latency, and redacted errors for reproducibility and cost measurement.
- Test with synthetic accounts and media before using consenting students' data.
- Confirm the correct WeChat application type and approval process early. Website QR login and an in-WeChat browser authorization flow have different prerequisites. A development-only test login supports integration work while approval is pending.

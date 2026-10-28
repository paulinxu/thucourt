# THUCourt — Project Milestones

## Dates and delivery assumptions

This proposed schedule assumes work begins on **October 29, 2026**, with parallel frontend/backend work by a small course team. Team size and the exact November feature priorities remain to be confirmed. The two delivery dates are:

- **Working version: November 13, 2026.** A deployed, demonstrable end-to-end product with core student workflows and text-based AI coaching.
- **Final version: December 15, 2026.** A tested release covering the planned platform features, bounded media coaching, evaluation, and handover documentation.

The November milestone is deliberately narrower than the final release. The final website must combine feedback, photo/video observations, match history, and past plans in private coaching. The later WeChat Mini Program is a separate phase with no committed delivery date. Account approvals, hosting access, and the manual enrollment-check procedure are external dependencies that must be raised immediately.

## Stages and deliverables

| Dates (2026) | Stage | Expected deliverables and completion criteria |
| --- | --- | --- |
| Oct 29–31 | Requirements and foundations | Confirm doubles confirmation policy, set/tiebreak rules, stroke-rating scale, pricing/payment policy, manual verification procedure, WeChat website route, and model access. Establish repository layout, database schema, local containers, CI, frontend shell, and seeded court/slot configuration. |
| Nov 1–5 | Core student platform | Profile and verification states, administrator review, court offers, list/grid views, filters, game requests, and owner deletion. API permission tests and usable mobile layouts. |
| Nov 6–9 | Social and match loop | Friend requests, basic messaging between any verified students, in-app notifications, structured singles/doubles matches, confirmation workflow, idempotent separate rating updates, member-only history, and rankings. Integrate WeChat in an approved environment if credentials are available. |
| Nov 10–12 | AI vertical slice and integration | Text-based coaching with scoped feedback retrieval, basic structured plan generation and explicit save, photo upload/storage, error states, deployment, and end-to-end smoke checks. Seeded demo accounts and walkthrough. |
| **Nov 13** | **Working-version delivery** | Demonstrate login/profile, browsing and posting, contact, match confirmation/ranking, and a grounded text coaching plan on the deployed application. Record limitations and pilot feedback. |
| Nov 14–22 | Complete product behavior | Complete trade UI without court-number requirements, anonymous editable behavior ratings, target-only written/numerical tennis feedback, unrestricted member contact with blocking, fulfilled/cancelled/expired request states, booking-linked game forms, responsive polish, and remaining verification/OAuth integration. |
| Nov 23–Dec 1 | Multimodal coaching | Photo/video-to-text observation pipeline and coaching that combines observations with friend feedback, own match history, and previous plans. Bounded frame extraction, private processing states, evidence references, quotas, retention/deletion, and prompt-injection/permission checks. Compare default and escalation models on representative tasks. |
| Dec 2–8 | Pilot and hardening | Pilot with approximately 10–20 consenting students; fix functional and usability issues. Run concurrency, permission, backup/restore, cost, and latency checks. Produce evaluation results. |
| Dec 9–14 | Release candidate and handover | Feature freeze, critical fixes, final regression run, deployment instructions, API docs, architecture updates, demo video, final report, and presentation. |
| **Dec 15** | **Final delivery** | Tagged release, deployed demo, source code, test/evaluation evidence, operational documentation, and final presentation materials. |

## November 13 acceptance checklist

- A demonstrator can sign in and complete profile/verification review. If WeChat approval is pending, a visibly labeled development-only login is used in the restricted demo and the dependency is reported.
- Court configuration matches the objective: 14/4 courts, four dates, and 14 default hourly slots. Buy/sell grids and one-column game discovery work with filtering and owner deletion.
- Two accounts can create/contact an offer or game request and exchange messages; the basic friend-request flow works.
- Accounts submit and confirm singles and doubles matches under the agreed confirmation policy; only the correct rating track changes, exactly once per player, and confirmed results are immutable in member-only history.
- The AI uses structured tennis feedback to explain a weakness and generate a saveable plan, without accessing another user's private data.
- A deployed URL, seeded data, smoke-test results, and a short demo script are available.

## Final acceptance criteria

- All sections and confirmed clarifications in `objective.md` have implemented website journeys, including dedicated trade offers, booking-linked game requests, anonymous editable behavior ratings, target-only written/numerical tennis feedback, request lifecycle states, messaging between any verified students, and profile management.
- WeChat login and truthful verification status work in the agreed delivery environment; unresolved external approval is explicitly documented rather than presented as complete.
- Private coaching combines photo and bounded video text observations with friend feedback, own singles/doubles history, and prior plans, with permission checks, citations, clear limitations, and failure recovery.
- Tests cover authorization, anonymous rating responses, target-only feedback, date/time boundaries, deletion ownership, request states, singles/doubles confirmation races, independent rating idempotency, confirmed-result immutability, and upload limits. Browser smoke tests cover the main journeys.
- At least 30 documented AI evaluation cases cover grounding, useful plans, missing/contradictory evidence, adversarial feedback, and failure handling. Report actual pass rates, costs, and latency; resolve critical privacy failures before pilot release.
- Deployment, backup restoration, configuration, data retention, and known limitations are documented and reproducible.

## Dependency management

Check progress against milestone acceptance criteria twice weekly. Protect the November 13 text-coaching and marketplace demo before adding video support. If OAuth approval or authoritative verification access is delayed, continue with the restricted demonstration path and track the missing integration as an external blocker. Reduce optional visual polish before reducing core permission, rating, or data-integrity checks.

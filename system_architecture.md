# THUCourt — System Architecture

## Purpose and scope

THUCourt is a web platform for Tsinghua students to exchange tennis court slots, find playing partners, record confirmed match results, message other students, and receive private AI-assisted training advice. Build a mobile-friendly website first; a WeChat Mini Program is a later client using the same backend APIs, with timing still to be agreed. This design translates `objective.md` and its confirmed clarifications into an implementation plan; other choices are proposals.

Related documents: [technology choices](technology_choices.md), [prompt and tool design](prompt_and_tool_design.md), [main workflow](main_workflow.md), [milestones](project_milestones.md), and [resources](additional_resources.md).

## Architecture overview

Use a modular Django backend rather than microservices. A single backend keeps permissions, transactions, and deployment manageable within the course timeline.

```text
Student's browser / WeChat browser
             |
             | HTTPS: web pages, REST API, authenticated uploads
             v
      React + TypeScript frontend
             |
             v
       Django REST API ---------------- WeChat OAuth
             |
             +---- PostgreSQL: accounts, offers, matches, messages, AI records
             +---- Private object storage: photos, videos, derived frames
             +---- Redis: background-job queue and transient job state
             |
             +---- Celery workers
                        +---- Media validation and frame extraction
                        +---- AI orchestration ---- Hosted model API
                        +---- In-app notification jobs
```

The browser never receives model API credentials. Celery workers run the same backend codebase and use the same authorization-aware application services as API endpoints. The frontend and API can share one public origin to simplify session authentication.

## Main components

| Component | Responsibilities and connections |
| --- | --- |
| Accounts and verification | WeChat login, profiles, identity-review state, self-reported level, behavior rating, and skill rating. Student IDs and real names are private. |
| Court marketplace | Buy, sell, and trade offers; filters; list and grid queries; owner-only deletion; links to messaging. |
| Game discovery | Requests to find players, filtered by area, date, time, and level; list view and a one-column time grid. |
| Matches and rankings | Structured singles/doubles score submissions, participant confirmations, immutable confirmed history, transactional updates of separate singles/doubles ratings, and leaderboards. |
| Friends and messaging | Search, friend requests, messaging between any verified students, anonymous editable behavior ratings, private written/numerical tennis feedback, and in-app notifications. |
| AI coaching | Permission-scoped player data retrieval, photo/video-to-text analysis, evidence fusion, private chat, and training-plan generation using feedback, media, own match history, and previous plans. It cannot alter official results or ratings. |
| Administration | Identity review, moderation, configuration of courts/time slots, job inspection, and operational support through Django Admin. |

## Data and domain rules

- **Core entities:** User, PlayerProfile, VerificationRequest, CourtArea, Court, TimeSlot, Offer, GameRequest, Friendship, Conversation, Message, BehaviorRating, TennisFeedback, Match, MatchParticipant, MatchSet, MatchConfirmation, RatingEvent, MediaAsset, MediaAnalysis, AIConversation, AIMessage, and TrainingPlan.
- **Court configuration:** Zijing has 14 courts at RMB 15 per slot; Beiguan has 4 at RMB 120. These are configurable reference prices, not integrated payment amounts.
- **Availability window:** Use `Asia/Shanghai`. Show today and the next three calendar dates. Default slots are 08:00–09:00 through 21:00–22:00: 14 one-hour slots. Store slot definitions as configuration to allow later duration changes.
- **Grids:** Buy/sell grids have 14 rows and either 14 or 4 court columns. Each cell counts active buy and sell offers separately. Find-game grids have 14 rows and one column, grouping all requests at that time for the selected area/date.
- **Ratings:** Each player starts with singles = 1000 and doubles = 1000. Confirmed singles affects only singles ratings; confirmed doubles affects only doubles ratings, with +10 per winning player and −10 per losing player, or no change on a draw. Final confirmation and rating-event creation occur in one transaction, with a unique event per match/player preventing repeated application. Confirmed results cannot be corrected. No lower rating bound is assumed. Proposed doubles policy, pending agreement: all three other participants confirm.
- **Ownership:** Creators may delete their own offers and game requests. Users cannot delete other users' requests. Confirmed official match records follow a separate correction process rather than request deletion.
- **Feedback:** Behavior ratings are separate from tennis-skill feedback and official skill points. Each friend has one editable anonymous 1–5-star behavior rating per target; show average and count without rater identities. Tennis feedback includes written comments and numerical stroke/category ratings, visible only to the target player and their authorized private coaching processor. The numerical feedback scale remains to be agreed.
- **Game requests:** Reference a specific court booking (area, court, date, and time) and include singles/doubles, players needed, and minimum/maximum desired level. This records the student's booking claim, not a university booking verification.
- **Lifecycle:** Offers and game requests have active, fulfilled, cancelled, and expired states; only active unexpired records contribute to discovery counts. Owner deletion remains available independently.

## Access boundaries and assumptions

Authentication identifies a WeChat account; entering a name and student ID does not prove enrollment. An administrator manually approves verification using an agreed enrollment-check method. Until approved, label accounts as pending rather than verified. Restrict member discovery, posting, contact, official history, and rankings to approved student accounts; a signed-in student can still manage their own verification/profile.

Private media, derived observations, training plans, and coaching conversations are accessible only to their owner and explicitly authorized processing jobs. Tennis feedback is visible only to its subject; authoring endpoints may acknowledge submission without exposing target feedback history. Public student profiles expose display names and tennis information, never student IDs. “Public” match history and rankings mean visible only to verified Tsinghua students. Store rating-author identity privately for uniqueness/edit authorization, but never return it in received behavior ratings or coaching evidence.

The platform coordinates offers and internal contact; booking transfers occur elsewhere. Trade offers record offered and desired area/date/time options without requiring court numbers. Payments are proposed to remain external, pending confirmation. University rules and whether reference prices are fixed selling prices still need confirmation before launch.

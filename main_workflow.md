# THUCourt — Main Workflow

## 1. Sign in and establish a profile

1. The student opens the web application and starts WeChat login.
2. The backend validates OAuth state, exchanges the authorization code, and creates an application session linked to the WeChat account.
3. The student submits real name and student ID privately, selects a self-reported tennis level from 1.0 to 5.5+ in half-point steps, and chooses a display name. Deliver this through a normal mobile-friendly website first; Mini Program delivery is a later phase.
4. An administrator checks enrollment using the approved verification method. Until approved, the account remains pending and cannot access member discovery/contact features.
5. The profile starts with 1000 singles points and 1000 doubles points. Behavior rating initially displays “not yet rated,” not an artificial zero-star rating.

## 2. Exchange court slots or find a game

1. The student selects Buy/Sell, Trade, or Find Games, an area, and a date from today through today + 3 in Shanghai time.
2. The API returns filtered list data or aggregate grid data. Buy/sell filters include date, time, and area; game discovery also supports player level.
3. Selecting a grid cell shows matching requests and actions to create a request or contact its owner. Find Games groups all courts into a single time column.
4. On creation, the backend validates the date, configured time slot, relevant court fields, required fields, and student approval. Past start times cannot receive new requests. Trade offers record offered and desired area/date/time options without a court number. Find-game requests reference a specific booked court and include singles/doubles, players needed, and a desired level range.
5. The request appears in lists and grid counts. Contact opens internal messaging; any verified student can message another without friendship or an offer being required, subject to recipient blocking and rate limits.
6. Students arrange the exchange or game directly. The creator can mark a request fulfilled or cancelled, or delete it; the API enforces ownership. Past requests become expired. Only active, unexpired requests appear in active results and grid counts.

Booking transfer happens outside THUCourt; the app does not make university reservations or guarantee booking ownership. Keeping payments external is a planning proposal pending confirmation.

## 3. Manage friends, feedback, and messages

1. A student searches by permitted public profile fields and sends a friend request.
2. The recipient accepts or declines. Friendship permits friend ratings/feedback; messaging is already available between any verified students.
3. A friend can provide one editable anonymous behavior rating from 1 to 5 stars per target and separate tennis feedback containing written comments and numerical ratings by forehand, backhand, serve, slice, volley, movement, or other configured categories. The numerical stroke scale remains to be agreed.
4. Only the target player can view received tennis feedback. Their private AI coaching context can retrieve it as anonymized peer opinion, not an objective skill measurement. Received behavior ratings never reveal the rater's identity.
5. The client polls for new messages and in-app notifications, preserving unread state. Message sends use client request IDs to prevent duplicates on retry.

WeChat push notifications are not required for in-app messaging or the initial release.

## 4. Record an official match

1. Players agree beforehand that a match will count as official.
2. One player chooses singles or doubles, selects the other participants and teams, enters structured per-set game/tiebreak scores, selects winner/draw, and sets the date played.
3. The backend rejects duplicate participants, future dates, invalid teams, or inconsistent score/outcome data, then stores an unconfirmed submission and notifies required confirmers.
4. In singles, the opponent confirms or rejects. Doubles confirmation policy is still to be agreed; the planning proposal requires all three non-submitting players to confirm. Without all required confirmations, the result is not official and cannot affect rankings. Rejected submissions may be replaced; no confirmation deadline is assumed yet.
5. On final required confirmation, a database transaction locks the relevant records, changes the match status, and writes unique per-player rating events. Win = +10, loss = −10, draw = 0, applied only to the match's singles or doubles rating track. Repeated confirmation has no additional effect.
6. The confirmed result appears only to verified Tsinghua students in official history and the corresponding rankings. It cannot be corrected after confirmation. Pending or rejected matches do not appear as official results or contribute to ratings.

Both singles and doubles are required. Detailed legal set/tiebreak formats and draw conventions remain to be agreed during requirements review.

## 5. Process an AI coaching task end to end

Example request: “My friends say my backhand is inconsistent. Build a two-week plan using my feedback and this clip.”

1. **Collect input:** The student asks a question, optionally uploads media, and selects the media to use. The backend checks session, ownership, quota, file type, size, and duration.
2. **Prepare media:** A background job validates and decodes the upload, strips unnecessary metadata from derived images, and extracts at most eight video frames. The UI shows queued, processing, ready, or failed status. The student may proceed with text-only coaching if preparation fails.
3. **Analyze media:** A vision-capable model processes selected photos and sampled video frames into private text observations with frame/time references, confidence, and limitations. Store these separately from human feedback. Ask the student to identify which player to analyze if necessary.
4. **Create context and retrieve evidence:** The server builds the coaching prompt with the student's goal and bounded conversation history. Allowed tools retrieve profile, written/numerical backhand feedback, own singles/doubles history, prior plans, and the media-derived text observations together. Real names, student IDs, and private conversations with friends are excluded.
5. **Generate advice:** The coaching model integrates all available sources, distinguishes peer comments from generated visual observations, explains contradictions or missing evidence, and proposes drills matched to the student's level and available time.
6. **Validate output:** The backend checks structured output, evidence references, and bounds. It records usage and status; transient failures have limited retries.
7. **Present the result:** The UI displays the plan, evidence references, and limitations. If the model provider is unavailable, it shows a retryable failure rather than fabricated analysis.
8. **Save and follow up:** The student explicitly saves the plan or asks for revisions. Saved plans become available in later coaching sessions; private conversations and media remain owner-scoped.

## 6. Retention and operations

Provide controls to delete owned media and coaching conversations. Deleting media also deletes its derived frames and prevents later retrieval; already-saved advice is identified as historical output. Use a proposed 30-day default retention for raw uploads, with the final policy confirmed before pilot use. Operational logs contain IDs and usage metadata rather than raw identity documents or full private prompts. Backups follow the documented retention/deletion schedule.

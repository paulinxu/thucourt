# THUCourt — Additional Resources

## Requested course support

The project uses hosted model inference and a modest web deployment. The following are planning estimates for **October 29–December 15, 2026**, not vendor quotations. Confirm available course infrastructure and current provider pricing before spending.

| Resource | Approximate request | Intended use |
| --- | --- | --- |
| Model API credits | **US$100 total cap**, initially allocate US$50 | Prompt development, automated evaluation, photo/video-to-text analysis followed by evidence-fusing coaching, and a small student pilot. Release the remaining allocation after reviewing actual usage. |
| Application VM | **1 Linux VM, 4 vCPU, 8 GB RAM, 80 GB disk, for about 7 weeks** | Frontend/API, PostgreSQL, Redis, and a low-concurrency Celery worker; media stored separately. |
| Object storage | **20 GB active storage**, up to **50 GB including temporary versions/backups** | Student photos, short clips, extracted frames, and lifecycle-controlled backups. |
| Outbound transfer | **Approximately 50 GB** over the project | Pilot media downloads, model image requests, deployment, and demonstrations. Check whether provider transfer fees are separate. |
| GPU time | **0 GPU hours requested** | Hosted models and CPU frame extraction are sufficient; no fine-tuning is planned. |
| Integration access | One suitable approved WeChat website-login app/account and its credentials | Validate website login first. The later Mini Program needs separate registration/configuration, with support and timing to be agreed. Institutional sponsorship may be needed depending on application type. |
| Verification support | An approved enrollment-check method and designated reviewer | Establish real student verification without pretending self-entered IDs prove enrollment. Prefer status-only checks over copying student records. |
| Test participants | Approximately **10–20 consenting students**, two short sessions each | Usability testing, realistic feedback, and evaluation of coaching usefulness. |
| Instructor/TA feedback | Two design reviews of approximately **30 minutes**, plus milestone feedback | Resolve scope, model-access constraints, verification policy, and assessment expectations early. |

If infrastructure is not supplied, provisionally budget **US$60–120 for hosting** and **US$5–20 for storage/transfer** over the project. Together with the US$100 API cap, the estimated cash request is **US$165–240**, excluding any domain, WeChat account fees, or taxes that require a separate quote. Existing course infrastructure can replace those cash costs.

## API usage estimate

Assume approximately 1,000 coaching-model requests across development, evaluation, and pilot use, averaging 3,000 input tokens and 800 output tokens per request:

- Text-equivalent input: approximately **3 million tokens**.
- Output: approximately **0.8 million tokens**.
- Additionally, budget for around **100–200 separate photo/video-frame analysis requests**, bounded to eight video frames each, tool-call overhead, repair attempts, and retries. A new media-based coaching task normally requires at least two model requests; cached private observations can be reused for later questions while the source remains available.

Image token accounting depends on the selected provider, resolution, and model. Compute the budget using current prices:

```text
estimated cost = input tokens × input rate
               + output tokens × output rate
               + additional image charges, if separately billed
               + retry/evaluation allowance
```

Avoid double-counting image tokens if the provider already includes them in input usage. The US$100 cap is a contingency budget rather than a predicted spend. Log usage per request, set spend alerts at US$50 and US$80, and stop paid requests at the cap. Start with a quota of 10 coaching requests per student per day and at most two simultaneous media jobs, then adjust based on measured usage and available funds.

## Storage estimate

A pilot of 20 students uploading five clips each, averaging 50 MB per clip, needs about **5 GB** for raw video. Allow approximately **2 GB** for photos and derived frames, and additional space for temporary processing, growth, and database backups. This fits within the proposed 20 GB active allocation if raw-media retention and upload limits are enforced. Backups must have explicit expiry rather than retaining deleted private media indefinitely.

## Important early confirmations

By October 31, confirm model/API access from the intended hosting location, website WeChat prerequisites, university rules for court exchanges, the manual verification procedure, and whether the course provides deployment credits. By November 5, measure both stages of a representative media-plus-coaching task to replace estimates with observed cost and latency. Use synthetic data until the relevant student data-handling arrangements are agreed. Private feedback and media may be sent only to the selected authorized model processor, not exposed to other students.

# Data dictionary

## `sessions_all_public.json`

JSON Lines (one session per line). Each session:

| Field | Type | Description |
|---|---|---|
| `session_id` | int | Internal ID used by the ASLO submission platform |
| `session_code` | str | Code like `SS050B`, `CS001P`, `EP013` (P suffix = poster session) |
| `name` | str | Full session title |
| `date` | str | ISO date or DD/MM/YYYY (both formats appear due to scraping source) |
| `time` | str | Session start time |
| `room` | str | Venue room code |
| `description` | str | Session abstract / framing text |
| `lead_organizer` | str | "Name, Institution" (email parenthetical stripped) |
| `co_organizers` | list[str] | Same format |
| `presentations` | list[dict] | Talks/posters in this session |

Each presentation:

| Field | Type | Description |
|---|---|---|
| `abstract_id` | str | Submission ID assigned by the conference platform |
| `title` | str | Presentation title |
| `presenter` | str | Primary presenter name |
| `affiliation` | str | Institutional affiliation string |
| `email_domain` | str | Domain part of the presenter email (the full address has been stripped for privacy) |
| `authors` | str | Full author list (when present in the source) |
| `time` | str | Presentation start time |
| `abstract` | str | Full abstract body (when scraped) |

## `session_metadata.json`

Lightweight session index — same structure as `sessions_all_public.json` but without the per-presentation details. Faster to load when only session-level info is needed.

## `pruned_withdrawals.json`

Eight entries that were in the original scrape but no longer appear on the live conference site as of 11 May 2026 — preserved here for the audit trail.

## `audit_capture_results.json`

Per-session captured-vs-live count comparison from the May 11, 2026 audit. Confirms the inventory is essentially complete.

## Privacy

Presenter emails (the full local-parts) have been removed. Only the email domain is retained, since domain alone is sufficient for country / institution inference and does not constitute personal contact information. If you need the full emails for legitimate research use, contact the corresponding author.

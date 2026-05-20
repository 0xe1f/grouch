# Deferred Tasks

Items from the TODO/FIXME audit that require further investigation or a separate plan before implementation. Each entry captures the problem, the agreed direction (where applicable), and the open questions that must be resolved first.

---

## 3. `sync_subs` memory + first-sync cutoff — `tasks/subscriptions.py`

### iterview migration

`find_metadata_by_user_by_synced` in `dao/subscriptions.py` uses `self.db.view(...)`, which materializes the full result set in memory. Every other DAO method uses `iterview`. For users with many subscriptions this creates unnecessary memory pressure.

**Agreed direction:**
- Rename to `iter_metadata_by_user_by_synced` (matches `iter_*` convention).
- Convert to a generator using `iterview` with `batch_size=40`.
- Must **not** use `include_docs=True` — the method reads from `doc.value`, not the full document.
- Update the call site in `tasks/subscriptions.py`. A long-lived cursor during `sync_subs` processing is acceptable.

### Latent `max_synced` type bug

`max_synced` initializes as `0` (int) and is updated via `max(max_synced, entry.updated or "")`. When `entry.updated` is `None` the fallback becomes `""` (str), which causes a `TypeError` when compared against `0` or a numeric timestamp in Python 3.

**Agreed direction:** Initialize `max_synced = None` and handle `None` explicitly, or filter out entries with no `updated` value. Fix alongside the iterview migration.

### First-sync cutoff

A new subscription (`synced=None`) currently fetches the entire entry history, potentially flooding the user with years of backlog. The agreed direction is a smarter initial cutoff — e.g. "entries from the last 30 days or the top N most recent, whichever is smaller" — but the details are more nuanced than they appear.

**Open questions:**
- Should "top N" be ordered by `entry.published` or `entry.updated`?
- Should "top N" guarantee a minimum number of entries even for infrequent feeds, or is 0 results acceptable when nothing falls within the time window?
- Where does the cutoff logic live — in `sync_subs`, in the DAO, or a dedicated helper?
- Should the constants (30 days, N articles) be hardcoded or configurable?

---

## 4. `articleExtras` dead code — `web/static/js/reader.js`

Two related issues:
- Line ~734: `entry.loadExtras()` is commented out with a bare `// FIXME`.
- Line ~951: `loadExtras()` makes an AJAX call to `articleExtras`, but **that endpoint does not exist** in `serve.py`.

`areExtrasDirty` is always set `true` but never acted upon. This is an incomplete feature.

**Decision needed:** Implement the feature end-to-end, or remove the dead code entirely.

---

## 5. Subscribe to URL with multiple feeds — `tasks/subscriptions.py`

Two TODOs acknowledge that when a page has multiple `<link rel="alternate">` feeds, only the first is used.

**Agreed design direction:**
1. Detect how many feeds are available for the given URL.
2. If more than one, return them to the client with preview metadata and prompt the user to pick.
3. Subscribe to the chosen feed.

Requires backend API changes, a new client interaction flow, and updates to the subscribe task.

---

## 7. `refresh_feeds` time-bounding — `tasks/feeds.py`

`iter_updated_before` can return an unbounded number of feeds. `fetch_batch_max = 40` batches writes but does not cap the total number refreshed per run. The real risk is runs taking longer than the schedule interval, causing task pile-up.

A simple count cap is too crude. Options discussed:

- **Time-boxed runs (recommended):** Stop processing new batches once a deadline is reached (e.g. 90% of the schedule interval). Feeds are already sorted oldest-first, so natural priority is preserved. Requires a `max_runtime_secs` config parameter.
- **Per-feed Celery tasks:** `refresh_feeds` becomes a coordinator that enqueues one task per feed. Most scalable, but a significant refactor — better suited to its own plan.
- **Chunked runs with Redis cursor:** Process the next N feeds per run from a stored position. Adds persistent state to manage.

---

## 8. `::` separator collision in entity keys — `entity/entity.py`

The `::` separator used in all CouchDB `_id` fields can appear inside key components, causing `decompose_key` to produce extra parts and breaking strict `len(parts)` guards in `extract_owner_id`.

**Susceptible entities:**
- `Feed` — key is `feed::{feed_url}`. IPv6 URLs (e.g. `https://[::1]/feed`) inject `::`.
- `Entry` — key is `entry::{feed_url}::{entry_uid}`. `entry_uid` is the raw RSS/Atom `<guid>` field; some publishers use `tag:host,year::path` style GUIDs.
- `Subscription` — key is `sub::{user_uid}::{feed_url}`. Same feed_url exposure.
- `Article` — key is `article::{user_uid}::{feed_url}::{entry_uid}`. Both inner components exposed.

**Safe entities:** `User` and `Folder` (all components are `token_urlsafe` base64url, no `:`).

**Immediate low-risk fix (also deferred):** Relax the strict `len(parts)` guards in `extract_owner_id`:
- `Subscription.extract_owner_id`: `!= 2` → `< 1`
- `Article.extract_owner_id`: `!= 3` → `< 1`

In both cases `parts[0]` is always the user UID regardless of extra segments from `::` collisions.

**Full-fix options:**
- **URL-encode components** (`urllib.parse.quote(val, safe='')` turns `::` → `%3A%3A`). Reversible, human-readable; `%` itself encodes to `%25` so it can't re-introduce `::`. Recommended.
- **Hash components** (SHA-256 hex of `feed_url`, `entry_uid`). Completely collision-free but loses human-readable keys.
- **Unicode sentinel** (e.g. `\ufff0`). Unlikely in practice but not guaranteed to be absent from arbitrary RSS content.

**Migration scope:** Re-keying requires updating all Feed, Entry, Article, and Subscription `_id` fields, plus all foreign-key references stored in related documents (`feed_id`, `entry_id`, `user_id`). Must be done atomically or with a transition period. A migration script with CouchDB bulk updates would be required.

### UUID-based keys (alternative approach)

Rather than encoding URL-derived components, generate a UUID at creation time for each feed/entry/subscription. UUIDs (v4) are fixed-format hex+hyphens with no `::` — the separator collision problem disappears entirely.

**Open questions:**
- **Duplicate safety:** With URL-derived keys, the same URL always maps to the same document implicitly. With UUIDs, a lookup table (`feed_url → feed_id`) is needed to prevent duplicate feed documents for the same URL. Right place for the index: CouchDB view, Redis cache, or separate lookup doc?
- **Entry deduplication:** Entries currently deduplicate on `(feed_id, entry_uid)` via the key. With UUIDs, a view/index on `(feed_id, entry_uid)` must be queried synchronously before assigning a UUID during feed refresh. Is that lookup fast enough?
- **Migration scope:** Same as the URL-encoding migration — all document `_id` values and foreign-key references must be updated.

---

## 9. Favicon URL — `parser/parse.py`

`content.favicon_url = None` is a commented-out placeholder. Feed objects have a `favicon_url` field that is never populated.

**Agreed direction:** Fetch the favicon as part of the feed fetch pipeline. Full implementation scope to be defined in a feed pipeline plan.

---

## 10. TOCTOU race in user registration — `dao/users.py`

The code already contains a comment describing the known mitigation (post-save duplicate check + delete). This is a self-documenting known limitation, not an active bug.

No work planned until user registration volume warrants it.

---

## B. Rate limiting on `/subscribe` and `/importFeeds`

Both endpoints enqueue async tasks without any per-user throttle. A user could spam-enqueue unlimited background jobs. Note: `@per_user` in `celery_app.py` serializes task *execution* (one at a time per user via Redis mutex) but does not prevent unlimited *enqueueing*.

**Options discussed:**
- **Flask-Limiter** — time-window, API-level, requires a new dependency.
- **Task-type-specific Redis counter** — no new dependency, more manual implementation.
- **Task-state-aware check** — most correct; checks for an already-pending task of the same type before enqueueing.

---


## F. Feed fetch atomicity — concurrent subscribe + refresh conflicts

When two users subscribe to the same URL simultaneously, both Celery tasks may find no existing feed document, both proceed to create one with the same deterministic key (`feed::{url}` and no `_rev`), and the second write gets a CouchDB `ResourceConflict` (409).

Separately, `refresh_feeds` (in `refresh.py`) runs as its own process and can concurrently update the same feed/entry documents that a subscribe task is writing.

`@per_user` does not help — it serializes tasks per user, not per feed URL.

**Open questions:**
- Does `BulkUpdateQueue` currently handle `ResourceConflict` gracefully on write, or does it fail silently / raise?
- For concurrent subscribes: would a per-feed Redis lock during the fetch+write window prevent duplicate creation?
- For subscribe vs. refresh conflicts: would a retry-on-conflict strategy (re-fetch current `_rev` and retry) be sufficient, or does the conflict window need to be narrowed further?
- Is conflict frequency high enough at current scale to warrant immediate action?

---

## D. Feed parsing has no timeout — `parser/parse.py`

`parse_url` and `parse_feed` call `feedparser.parse(url)` directly. feedparser 6.0.11 has no `timeout` parameter (the maintainer rejected it). A slow or unresponsive remote server will hold a Celery worker indefinitely.

**Agreed direction:**
- Use `requests.get(url, timeout=FEED_FETCH_TIMEOUT_SECS)` to fetch the content, then pass it to `feedparser.parse()` instead of letting feedparser do the HTTP request.
- Define `FEED_FETCH_TIMEOUT_SECS = 10` in `parser/consts.py`.
- Extract a `_fetch_url(url: str) -> tuple[bytes, dict] | None` helper. Both `parse_url` and `parse_feed` call it, then pass `feedparser.parse(content, response_headers=headers)`.
- Catch `requests.exceptions.RequestException` (covers `Timeout`, `ConnectionError`, etc.) — log and return `None`.
- Pass `response_headers=dict(response.headers)` to `feedparser.parse()` for correct charset/encoding detection.
- No `raise_for_status()` — preserve feedparser's "try to parse anything" behavior; existing bozo/version checks already handle bad content.
- `requests` decompresses gzip/deflate transparently — feedparser's HTTP gzip handling is not missed.

**Note:** ETag/Last-Modified support can be added in the same pass — see the ETag future-work item below.

---

## Future work: ETag / Last-Modified support in feed pipeline

Currently `requests.get` fetches the full feed body on every refresh, ignoring HTTP caching headers. Adding conditional GET support would reduce bandwidth and skip re-parsing unchanged feeds.

**Agreed direction:**
1. Add `etag` and `last_modified` fields to the `Feed` entity.
2. Store the values after each successful fetch.
3. On subsequent requests, pass `If-None-Match` / `If-Modified-Since` headers.
4. Handle `304 Not Modified` responses to skip re-parsing entirely.

Implement as part of the feed pipeline plan alongside favicon fetching (item 9).

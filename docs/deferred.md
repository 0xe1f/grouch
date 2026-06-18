# Deferred Tasks

Items from the TODO/FIXME audit that require further investigation or a separate plan before implementation. Each entry captures the problem, the agreed direction (where applicable), and the open questions that must be resolved first.

---

## 4. `articleExtras` dead code — `web/static/js/reader.js`

Two related issues:
- Line ~734: `entry.loadExtras()` is commented out with a bare `// FIXME`.
- Line ~951: `loadExtras()` makes an AJAX call to `articleExtras`, but **that endpoint does not exist** in `serve.py`.

`areExtrasDirty` is always set `true` but never acted upon. This is an incomplete feature.

**Decision needed:** Implement the feature end-to-end, or remove the dead code entirely.

---

## 7. `refresh_feeds` time-bounding — `tasks/feeds.py`

`iter_updated_before` can return an unbounded number of feeds. `fetch_batch_max = 40` batches writes but does not cap the total number refreshed per run. The real risk is runs taking longer than the schedule interval, causing task pile-up.

A simple count cap is too crude. Options discussed:

- **Time-boxed runs (recommended):** Stop processing new batches once a deadline is reached (e.g. 90% of the schedule interval). Feeds are already sorted oldest-first, so natural priority is preserved. Requires a `max_runtime_secs` config parameter.
- **Per-feed Celery tasks:** `refresh_feeds` becomes a coordinator that enqueues one task per feed. Most scalable, but a significant refactor — better suited to its own plan.
- **Chunked runs with Redis cursor:** Process the next N feeds per run from a stored position. Adds persistent state to manage.

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

## Future work: scale up feed-fetch concurrency

`_fetch_feeds` in `tasks/feeds.py` currently fans out via `ThreadPoolExecutor(max_workers=10)`. Two related ideas were discussed and deferred:

- **Raise concurrency (e.g. to ~50).** Effective in-flight count is also capped by `fetch_batch_max = 40` in `refresh_feeds`, so to truly run 50 at once both `max_workers` and `fetch_batch_max` must be raised together. The import path (`import_feeds`) has no batching, so there `max_workers` is the sole cap. This is the lever that actually helps; it overlaps more network wait, especially valuable now that a hung feed caps at the 10s fetch timeout.
- **Switch to coroutines (asyncio).** Decided *not* worth it at current/near-term scale:
  - `requests` is blocking, so it would require an async HTTP client (`aiohttp`/`httpx` — new dependency) and async rewrites of the parser entry points.
  - `feedparser.parse()` + lxml sanitizing are CPU-bound and synchronous; they'd block the event loop, so an executor would still be needed for the parse step. asyncio doesn't escape threads here.
  - At n≈50, plain threads are fine; asyncio's per-task memory advantage only matters at hundreds–thousands of concurrent connections.
  - The bottleneck above ~50 shifts off the fetch onto GIL-serialized parsing and CouchDB writes (`BulkUpdateQueue`), neither of which asyncio improves. Prefork Celery (`--concurrency=2`) already provides multi-core parse parallelism.

**Open questions for revisit:**
- What concurrency do real refresh/import batch sizes justify? (Measure fetch phase vs. parse phase vs. CouchDB write latency before tuning.)
- At higher concurrency, watch per-worker memory (parsed content held in flight) and CouchDB write-burst latency.
- If fan-out ever reaches many hundreds, prefer `celery worker --pool=gevent` (cooperative `requests` with no code rewrite) over a full asyncio/`aiohttp` port.

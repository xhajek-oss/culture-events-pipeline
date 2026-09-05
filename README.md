# Culture Events Pipeline

API-first cultural event monitoring pipeline inspired by the structure of `sports-tv-pipeline`.

The service watches configured cultural venues across independent ticket/event sources and sends a Telegram message only when a source publishes a previously unseen event. There are no daily or weekly reports.

## Core rules

- Source-local identity: GoOut, SMS Ticket and Ticketportal listings are independent events.
- Prefer stable source IDs; fall back to stable source URLs where needed.
- API/XHR first, HTML second, Playwright only as discovery/runtime fallback.
- SQLite tracks first/last seen state, source runs and notification delivery.
- Production schedule is intentionally not defined; configure the cron interval in `.github/workflows/production.yml`.

## Workflows

- `production.yml`: fetch, compare, persist and notify.
- `pr-check.yml`: deterministic tests.
- `debug.yml`: manual source debugging scaffold.

## Setup

Configure `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` as GitHub Actions secrets. Fill stable venue/source identifiers in `config/venues.yaml` before enabling production scheduling.

SMS Ticket and Ticketportal adapters are intentionally marked `discovery_required` until their most efficient stable transport is identified and implemented.

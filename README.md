# Culture Events Pipeline

API-first cultural event monitoring pipeline inspired by the structure of `sports-tv-pipeline`.

The service watches configured cultural venues across independent ticket/event sources and sends a Telegram message only when a source publishes a previously unseen event. There are no daily or weekly reports.

## Core rules

- Source-local identity: GoOut, SMS Ticket and Ticketportal listings are independent events.
- Stable source IDs are used whenever available.
- GoOut uses its JSON API and stable schedule ID.
- SMS Ticket and Ticketportal currently use lightweight server-rendered HTTP parsing with stable event IDs extracted from event URLs.
- Playwright is optional and reserved for endpoint discovery or a future fallback if a site becomes browser-only.
- SQLite tracks first/last seen state, source runs and durable Telegram notification delivery.
- The first complete successful production run establishes a baseline and sends no historical notifications.
- SQLite is restored from the latest successful `culture-db` workflow artifact and uploaded again after each run.
- Production schedule is intentionally not defined; configure the cron interval in `.github/workflows/production.yml`.

## Workflows

- `production.yml`: restore state, fetch, compare, persist and notify.
- `pr-check.yml`: deterministic tests.
- `debug.yml`: manual source debugging scaffold.

## Setup

Configure `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` as GitHub Actions secrets. Venue/source identifiers live in `config/venues.yaml`.

For browser/network discovery install the optional dependency group with `pip install '.[discovery]'` and then install a Playwright browser only when needed.

# Architecture

The pipeline is source-local by design: an event from GoOut, SMS Ticket, and Ticketportal is treated as a separate event.

Production flow:

`fetch -> parse -> normalize -> source-local identity -> SQLite compare -> enqueue notification -> Telegram`

There are no daily or weekly digests. Telegram is sent only when an event is first observed.

Transport priority:

`public API -> internal JSON/XHR -> embedded JSON -> HTML -> Playwright network discovery -> Playwright DOM fallback`

Playwright should primarily be used to discover a stable endpoint, not as the default production transport.

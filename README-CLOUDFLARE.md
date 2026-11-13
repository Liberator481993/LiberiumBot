# LiberiumBot — Cloudflare Worker port

This is a separate migration branch. The original Python/aiogram polling bot remains unchanged on `main`.

## Architecture
- Telegram webhook endpoint: `POST /telegram/webhook`
- Cloudflare Worker runtime (JavaScript)
- Cloudflare D1 database for users, catalog entries and conversational state
- Secrets: `BOT_TOKEN`, `ADMIN_IDS`, `WEBHOOK_SECRET`
- Variables: `CHANNEL_ID`, `CHANNEL_URL`

## Implemented in this branch
- Russian and English interface, language selection, subscription check, profile and catalog navigation.
- Admin content wizard accepts Telegram documents and photos and stores their `file_id` metadata in D1.
- Catalog delivery sends stored images with `sendPhoto` and attached files with `sendDocument`.
- Admin channel-post wizard supports text or photo posts with a custom URL button and a confirmation step.
- Broadcast copies the original Telegram message, preserving supported media, and applies a basic delay / 429 retry wait.
- Basic content management and statistics.

## SQLite → D1 data migration

The repository includes an offline, read-only exporter at `cloudflare/export_sqlite_to_d1.py`. It exports the existing `users` and `content_items` tables, including language preferences and Telegram file/photo IDs. The generated SQL uses UPSERTs, so importing it more than once does not duplicate users or catalog entries. Existing wizard state is intentionally not migrated because it is temporary in-progress interaction state.

**The source SQLite file is not included in GitHub and this exporter does not access the bot host automatically.** Run the exporter on a machine that has a copy of the actual production SQLite file:

```bash
python cloudflare/export_sqlite_to_d1.py --sqlite data/liberium.sqlite3 --output data/cloudflare-migration.sql
```

The source is opened in SQLite read-only mode. The output file contains Telegram user IDs and may contain Telegram `file_id` values; keep it private, do not commit it, and do not send it in chat.

After creating the D1 database, applying the schema, and configuring its ID in `wrangler.toml`, import the SQL from the same trusted machine:

```bash
npx wrangler d1 execute liberiumbot --remote --file=data/cloudflare-migration.sql
```

Then compare the printed exporter counts with the D1 counts:

```bash
npx wrangler d1 execute liberiumbot --remote --command="SELECT 'users' AS table_name, COUNT(*) AS row_count FROM users UNION ALL SELECT 'content_items', COUNT(*) FROM content_items;"
```

The import is additive/upserting; it does not delete D1 rows that are absent from the SQLite source. Back up the D1 database before importing into a database that already contains production data. Do not run the import until you have confirmed that the SQLite file is the latest complete bot database.

## Production readiness and persistent storage

The Worker is event-driven: Cloudflare starts it for incoming Telegram webhook requests, so there is
no polling process to keep alive. D1 is the persistent SQL database; its contents survive Worker
deployments and idle periods.

Before first deployment:
1. Create a D1 database named `liberiumbot` in the same Cloudflare account used for the Worker.
2. Apply `cloudflare/schema.sql` to that database. The schema includes a Telegram update ledger to
   reduce duplicate processing when Telegram retries webhook deliveries.
3. Copy the D1 database ID into `wrangler.toml` (replace the placeholder).
4. Configure Worker secrets `BOT_TOKEN`, `ADMIN_IDS`, and a strong random `WEBHOOK_SECRET`.
   The webhook refuses requests if any required secret or the D1 binding is missing.
5. Deploy only after importing and verifying the real SQLite data, then test
   `GET /healthz` and the webhook using a non-production test bot if possible.
6. Only after verification, set Telegram's webhook with the same secret token. Never run polling
   and webhook delivery simultaneously for the same bot token.

`GET /healthz` checks that D1 can execute a query and returns HTTP 503 if the binding/database
is unavailable. Telegram updates are recorded in `processed_updates`; duplicate deliveries are
acknowledged, failed handlers return HTTP 503 so Telegram can retry, and stale processing claims
can be reclaimed after five minutes.

### Free-plan capacity to keep in mind

Cloudflare's published Free limits currently include 100,000 Worker requests/day, 5 million D1
rows read/day, 100,000 D1 rows written/day, 500 MB per D1 database and 5 GB total D1 storage.
Exceeding daily D1 read/write quotas causes queries to fail until the UTC reset; data is not deleted.
These limits may be enough for a small bot, but they are not an uptime guarantee. Monitor usage
and consider Workers Paid if real traffic exceeds the free quotas.

## Known gaps before production
- The migration utility is implemented and unit-tested, but it has **not** been run against the real production SQLite database or a real D1 database yet. Counts have not been verified.
- No live Telegram integration test; CI performs JavaScript syntax validation and offline migration smoke tests.
- Broadcast retry handling is basic; failed recipients are counted but not persisted for a retry campaign.
- Channel button colour selection is not exposed in this Worker port; Telegram Bot API button styling compatibility needs separate verification.
- The existing SQLite database is not automatically synchronized with D1.
- D1 database ID is still a placeholder in `wrangler.toml`.

## Cloudflare setup (do not run until the migration is approved)
1. Create a D1 database named `liberiumbot`.
2. Apply `cloudflare/schema.sql` using `npx wrangler d1 execute liberiumbot --remote --file=cloudflare/schema.sql`.
3. Put the D1 database ID into `wrangler.toml`.
4. Set Worker secrets: `npx wrangler secret put BOT_TOKEN`, `ADMIN_IDS`, and `WEBHOOK_SECRET`.
5. Install dependencies and deploy with `npm install` then `npm run deploy`.
6. Set Telegram webhook to `https://<worker-host>/telegram/webhook` with the same secret token. Do this only after the Worker is deployed and verified.
7. Disable the old polling process before setting the webhook. Telegram does not allow polling and webhook delivery at the same time for one bot token.

Do not deploy until D1 is created, its ID is configured, secrets are set, SQLite data migration has been run and verified, and the production parity checklist is complete.

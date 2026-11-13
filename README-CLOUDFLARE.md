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

## Known gaps before production
- No migration utility yet for importing existing SQLite users/content into D1.
- No live Telegram integration test; CI currently performs JavaScript syntax validation and static smoke tests.
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

Do not deploy until D1 is created, its ID is configured, secrets are set, SQLite data migration is implemented and verified, and the production parity checklist is complete.

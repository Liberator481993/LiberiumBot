# LiberiumBot — Cloudflare Worker port

This is a separate migration branch. The original Python/aiogram polling bot remains unchanged on `main`.

## Architecture
- Telegram webhook endpoint: `POST /telegram/webhook`
- Cloudflare Worker runtime (JavaScript)
- Cloudflare D1 database for users, catalog entries and conversational state
- Secrets: `BOT_TOKEN`, `ADMIN_IDS`, `WEBHOOK_SECRET`
- Variables: `CHANNEL_ID`, `CHANNEL_URL`

## Current migration scope
The Worker implements language selection, subscription checks, user menu/profile, catalog navigation, MM2 loadstring delivery, basic admin content editing, broadcast and statistics. Remaining parity work before production: full channel-post wizard and media/file delivery (Telegram file_id send/copy flow), then automated tests and live webhook validation.

## Cloudflare setup
1. Create a D1 database named `liberiumbot`.
2. Apply `cloudflare/schema.sql` using `npx wrangler d1 execute liberiumbot --remote --file=cloudflare/schema.sql`.
3. Put the D1 database ID into `wrangler.toml`.
4. Set Worker secrets: `npx wrangler secret put BOT_TOKEN`, `ADMIN_IDS`, and `WEBHOOK_SECRET`.
5. Install dependencies and deploy with `npm install` then `npm run deploy`.
6. Set Telegram webhook to `https://<worker-host>/telegram/webhook` with the same secret token. Do this only after the Worker is deployed and verified.
7. Disable the old polling process before setting the webhook. Telegram does not allow polling and webhook delivery at the same time for one bot token.

Do not deploy until D1 is created, its ID is configured, secrets are set, and the production parity checklist is complete.

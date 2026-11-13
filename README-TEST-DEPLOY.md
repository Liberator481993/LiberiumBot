# Isolated test bot deployment

This procedure is for the separate Telegram test bot only. It does not deploy the production Worker, change the production Telegram bot, or set any Telegram webhook.

## Fixed test targets

- Worker name: `liberiumbot-test`
- Wrangler config: `wrangler.test.toml`
- D1 database: `liberiumbot-test`
- D1 database ID: `02c6a0c3-b32d-4740-8973-d455555c8b72`
- Test channel ID: `-1004474178126`
- Test channel invite: `https://t.me/+IINCMlJqAolkZGFh`

The production `wrangler.toml`, production D1 database, production bot token, and `main` branch are not used by the test deployment workflow.

## GitHub Actions configuration

In the repository `Liberator481993/LiberiumBot`, open **Settings → Secrets and variables → Actions**.

Required repository variable:
- `CLOUDFLARE_ACCOUNT_ID` — the Cloudflare account ID.

Required repository secrets:
- `CLOUDFLARE_API_TOKEN` — Cloudflare API token with Workers Scripts edit and D1 edit permissions for this account.
- `TEST_BOT_TOKEN` — token for `@testbotaliberty` only. Never use the production bot token.
- `TEST_ADMIN_IDS` — numeric Telegram user ID(s) allowed to administer the test bot; multiple IDs may be comma-separated.
- `TEST_WEBHOOK_SECRET` — a random secret of at least 32 characters.

Do not paste any bot token or webhook secret into chat, source files, workflow logs, or ordinary repository variables. Add them directly in GitHub Secrets.

## Deploy the test Worker

1. Confirm the test bot is an administrator of the private test channel and can publish messages.
2. Add the required GitHub variable and secrets above.
3. Open **Actions → Deploy LiberiumBot TEST Worker → Run workflow**.
4. Select branch `cloudflare-worker-port`; leave confirmation as `no` until all secrets are configured and the test deployment is intentionally approved.
5. Selecting `yes` applies the schema only to `liberiumbot-test`, deploys only the Worker configured by `wrangler.test.toml`, and installs only the test bot secrets.
6. The workflow deliberately does not call Telegram `setWebhook`. After checking `/healthz` and the test Worker, webhook setup is a separate step requiring explicit approval.

Expected test Worker URL: `https://liberiumbot-test.pavloosakura.workers.dev`.

## Safety boundary

Do not run the production workflow `.github/workflows/cloudflare-deploy.yml` for this test. Do not merge the migration PR, deploy `wrangler.toml`, set a webhook for the production bot, or stop the existing polling bot as part of test deployment.

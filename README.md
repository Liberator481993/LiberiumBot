# LiberiumBot

Telegram bot for the Liberium ecosystem. This project is separate from the existing
LiberiumHub repository.

## Current features

- Russian and English interface, selected on first launch.
- Required subscription check for https://t.me/mm2hubscripts.
- Script catalog: Murder Mystery 2, Adopt Me and Blade Ball.
- Injector catalog: Delta and Arceus X.
- Guide catalog: installation, launch and troubleshooting.
- SQLite storage for users and published materials.
- Telegram admin panel: add/update/delete catalog entries, send broadcasts and view basic statistics.
- Admin access controlled by numeric Telegram user IDs in ADMIN_IDS.

The catalog starts empty. The owner publishes actual files, links, versions and descriptions from the Telegram admin panel.

## Requirements

- Python 3.10 or newer.
- A Telegram bot token from https://t.me/BotFather.
- The bot must be an administrator in the required channel so Telegram can reliably verify membership.

## Local setup

1. Clone this repository.
2. Create a virtual environment and install dependencies:

   ~~~bash
   python -m venv .venv
   source .venv/bin/activate
   # Windows: .venv\\Scripts\\activate
   pip install -r requirements.txt
   ~~~

3. Copy .env.example to .env.
4. Set BOT_TOKEN and your numeric Telegram ID in ADMIN_IDS.
5. Keep CHANNEL_ID=@mm2hubscripts and CHANNEL_URL=https://t.me/mm2hubscripts, unless the required channel changes.
6. Add the bot to the channel as an administrator.
7. Run:

   ~~~bash
   python main.py
   ~~~

Do not commit .env or share your bot token. The token belongs only in a secret environment variable on the machine that runs the bot.

## Admin panel

Open the bot in Telegram and send /admin (or use the Admin panel button).

To publish a catalog entry:

1. Choose Scripts, Injectors or Guides.
2. Select the item to manage.
3. Send its Russian title, English title, Russian description, English description, version and URL.
4. Upload an optional document (for example, a .txt script or an APK), or send /skip.

A later update replaces the previous entry for that item. Deleting an entry removes its stored metadata from the database.

## GitHub Actions and 24/7 operation

GitHub is used for source control and automated checks. The workflow in .github/workflows/ci.yml
checks Python syntax when code is pushed or a pull request is opened.

GitHub Actions is not a permanent Telegram bot host. Workflow jobs are temporary and can be stopped;
they are suitable for tests and scheduled tasks, not dependable continuous polling. For 24/7 message
handling, run the bot on an always-on machine or hosting service. The SQLite database must live on
persistent storage and be backed up.

## Notes

- The bot checks membership at the time a user opens protected sections.
- If membership checks fail for everyone, verify the channel ID and that the bot is an administrator.
- The first version uses long polling. Do not run two polling instances with the same token at the same time.


## Temporary GitHub Actions test session

The `.github/workflows/manual-bot-test.yml` workflow can be started manually from the
Actions tab after adding repository secrets `BOT_TOKEN` and `ADMIN_IDS`.
It starts one temporary long-polling session for up to 330 minutes. Do not run it while
another instance of this bot is polling with the same token.

This workflow is for a short test only, not production hosting. The runner is temporary and is not 24/7 hosting. The workflow now restores the latest
available `liberium-sqlite-db` artifact from a previous successful session and uploads a
consistent SQLite snapshot after the polling process exits. Artifacts are retained for 30 days
and are accessible only to repository collaborators with appropriate access. The first run
after this change has no prior artifact to restore, so it starts with an empty database unless
an earlier backup is manually supplied. This is a continuity aid for manual test sessions,
not a substitute for durable production hosting or independent backups.

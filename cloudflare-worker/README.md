# Cloudflare morning trigger

This Worker checks the public Morning Magazine at 06:52 Europe/London and retries at 07:02, 07:12 and 07:22. It dispatches the GitHub Actions newspaper workflow only when the public edition is stale. Both GMT and BST are handled by UTC cron pairs plus a London-time guard in the Worker.

Required encrypted Worker secrets:

- `GITHUB_TOKEN`: GitHub token able to dispatch Actions workflows in `terasfly/morning-news`.
- `TRIGGER_SECRET`: protects the optional `/trigger` manual test endpoint.

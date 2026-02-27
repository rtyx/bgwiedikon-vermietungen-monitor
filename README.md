# BG Wiedikon Vermietungen Monitor

Monitors `https://bgwiedikon.ch/vermietungen` via the public GraphQL API and sends an email alert when content changes.

## What it watches
- Page title and intro
- All `accordionSection` blocks (titles, text, docs, images)

## How it works
1. Fetches content from `https://admin.bgwiedikon.ch/api`
2. Builds a canonical JSON payload
3. Computes SHA-256 hash
4. Compares with previous hash in `state.json`
5. If changed:
   - Updates `state.json`
   - Writes `last_change.diff`
   - Sends an email to `rafaeltoledanoillan@gmail.com`

First run creates a baseline and does **not** send an email.

## Required GitHub Secrets
Set these repository secrets:
- `RESEND_API_KEY`
- `EMAIL_FROM` (sender address)

## Resend API test
Replace `re_xxxxxxxxx` with your real Resend API key, then run:

```bash
curl -X POST 'https://api.resend.com/emails' \
  -H 'Authorization: Bearer re_xxxxxxxxx' \
  -H 'Content-Type: application/json' \
  -d $'{
    "from": "onboarding@resend.dev",
    "to": "rafaeltoledanoillan@gmail.com",
    "subject": "Hello World",
    "html": "<p>Congrats on sending your <strong>first email</strong>!</p>"
  }'
```

## Schedule
The workflow runs hourly and can also be triggered manually (`workflow_dispatch`).

## Notes
- This repo stores the previous payload in `state.json`.
- `last_change.diff` keeps a unified diff between the previous and current payload when a change is detected.

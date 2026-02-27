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
- `SMTP_HOST`
- `SMTP_PORT` (for example `587` or `465`)
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `EMAIL_FROM` (sender address)

## Schedule
The workflow runs hourly and can also be triggered manually (`workflow_dispatch`).

## Notes
- This repo stores the previous payload in `state.json`.
- `last_change.diff` keeps a unified diff between the previous and current payload when a change is detected.

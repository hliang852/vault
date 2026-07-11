# Email Notification Setup — Gmail SMTP for the GitHub Actions Scraper

**Goal:** the daily scraper (GitHub Actions) emails `kellylianghl@gmail.com` with the dated transformed CSV (`Japan_yyyy-mm-dd.csv`) attached, after any run that produced changes.

**Approach:** Gmail SMTP with an **App Password**. This is the standard production route for sending from CI. Important distinctions:
- The email account is used only as the *sending* mechanism; the recipient is the same address (self-notification), which is fine.
- A Gmail **App Password is not your Google password**. It's a 16-character token that works only for SMTP/IMAP and can be revoked independently at any time. Never put your real Google password anywhere in the repo or its settings.
- The App Password goes into **GitHub Actions Secrets** (encrypted at rest, masked in logs), never into code or the workflow file.

---

## Step 1 — Create the Gmail App Password (you do this; it requires your Google login)

1. 2-Step Verification must be ON for the Google account: myaccount.google.com → Security → 2-Step Verification.
2. Go to myaccount.google.com/apppasswords (Security → 2-Step Verification → App passwords).
3. Create a new app password. Name it something identifiable, e.g. `github-japan-ma-scraper`.
4. Google shows a 16-character password **once**. Copy it — you'll paste it into GitHub in Step 2 and never need it again locally.

If the App passwords page doesn't appear, the account may be an Advanced Protection or Workspace-restricted account; tell me and we'll use a transactional service (Resend/SendGrid free tier) instead — the pipeline code will support either via the same env vars.

## Step 2 — Add GitHub repository secrets (you do this once the repo exists)

Repo → Settings → Secrets and variables → Actions → New repository secret. Create:

| Secret name | Value |
|---|---|
| `SMTP_HOST` | `smtp.gmail.com` |
| `SMTP_PORT` | `465` (SSL) |
| `SMTP_USERNAME` | `kellylianghl@gmail.com` |
| `SMTP_PASSWORD` | the 16-character App Password from Step 1 |
| `MAIL_TO` | `kellylianghl@gmail.com` |

## Step 3 — Workflow usage (I build this in the pipeline repo)

The daily workflow will use the widely-used `dawidd6/action-send-mail` action (or a ~20-line Python `smtplib` step — my recommendation, zero third-party action dependency):

```yaml
# excerpt from .github/workflows/daily_scan.yml
- name: Send notification email
  if: steps.scan.outputs.changed == 'true'
  env:
    SMTP_HOST: ${{ secrets.SMTP_HOST }}
    SMTP_PORT: ${{ secrets.SMTP_PORT }}
    SMTP_USERNAME: ${{ secrets.SMTP_USERNAME }}
    SMTP_PASSWORD: ${{ secrets.SMTP_PASSWORD }}
    MAIL_TO: ${{ secrets.MAIL_TO }}
  run: python pipeline/send_notification.py --attach "output/Japan_$(date -u +%F).csv"
```

`send_notification.py` (to be delivered with the repo): stdlib-only `smtplib` + `email.message.EmailMessage`, SSL on port 465, subject line `[Japan M&A] {n_new} new / {n_updated} updated — {date}`, body listing each new/updated record (target, acquirer, status, citation), CSV attached. Fails loudly (non-zero exit) so a broken email surfaces in the Actions run status.

## Step 4 — Test plan (first thing after repo scaffold)

A manual `workflow_dispatch` job that sends a test email with a dummy CSV — verifies secrets, SMTP, and attachment handling before the scanner logic ever runs.

## Security notes

- Rotate/revoke the App Password anytime at myaccount.google.com/apppasswords; the pipeline resumes after updating the one secret.
- Gmail SMTP limits (~500 recipients/day) are irrelevant at one email/day.
- The repo should be **private**: it will contain the masterfile data. Actions secrets work identically in private repos.
- If the repo is ever made public, nothing changes for secrets, but the data files become public — decide deliberately.

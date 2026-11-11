# Security Policy

## Supported versions

Only the latest commit on `main` receives security fixes.

## Reporting a vulnerability

**Please do not report security problems in public issues, discussions or pull
requests.**

Report them privately through GitHub:
[**Report a vulnerability**](https://github.com/MichaelGeranis/wedding/security/advisories/new).

Please include what the problem is, steps to reproduce, and the impact you
expect. This project is maintained by one person in their own time. The aim is
to acknowledge a report within 7 days and agree a disclosure date once a fix is
understood. You will be credited in the advisory unless you prefer not to be.

## Scope

Of particular interest:

- reaching admin endpoints or guest data without logging in;
- guessing or enumerating guest invitation tokens;
- getting past the RSVP rate limit or the invited-guest validation;
- injection through RSVP fields, CSV import or CSV export.

## Running it safely

The values in `docker/demo.env` are public. Before guests can reach your site,
set your own `JWT_SECRET_KEY` and `ADMIN_PASSWORD_HASH`, set
`ENVIRONMENT=production`, and serve it over HTTPS.

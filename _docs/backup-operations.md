# Backup operations and outstanding production checks


### Daily offsite backup setup (pending operations verification)

The workflow `.github/workflows/daily-backup.yml` runs at 19:17 UTC (02:17 Asia/Bangkok), **only after this workflow exists on the default branch**. Configure repository Actions secrets `BACKUP_DATABASE_URL`, `BACKUP_AWS_ACCESS_KEY_ID`, `BACKUP_AWS_SECRET_ACCESS_KEY`, `BACKUP_AWS_REGION`, and `BACKUP_S3_BUCKET`. Use a dedicated read-only PostgreSQL account for pg_dump and a narrowly scoped S3 identity with PutObject/ListBucket only. The S3 bucket must block public access, enable versioning and lifecycle retention, and apply encryption and access logging. The job fails if secrets are missing, and verifies that at least one dump exists offsite; configure GitHub Actions failure notifications.

**Important:** The scheduled workflow is only a proposed configuration until secrets, S3 permissions, first successful Actions run and bucket object evidence are verified. Media backup is not covered by the database-only workflow: the protected PDF media must be backed up to private offsite storage separately. Do not mark production backup AC complete until that is implemented and verified.

For PostgreSQL restore rehearsal, provision an isolated disposable database with a name containing `_restore_test`, and set `RESTORE_TEST_DATABASE_URL` to its connection URL. Run `bash scripts/backup_restore.sh test` with `DATABASE_URL` set to the source. This executes `pg_restore --exit-on-error` against the isolated database and checks restored tables and users. Never set the test URL to production. The script rejects a missing or identical test URL. **Do not claim a successful PostgreSQL restore until a real test DB run and data verification evidence are attached.** The standalone `restore` action requires `ALLOW_DESTRUCTIVE_RESTORE=YES` and is for explicit recovery operations only.

## Current status (November 2026)
The backup/restore script (`scripts/backup_restore.sh`) and daily workflow (`.github/workflows/daily-backup.yml`) exist in the repository (with additional safety checks in Issue [#192](https://github.com/Jupiter4428/cntagram/issues/192) / PR [#199](https://github.com/Jupiter4428/cntagram/pull/199)). Passing unit tests is not the same as restoring a production PostgreSQL snapshot. Never restore over production: use an isolated `_restore_test` database and keep the test evidence, with secrets removed, before publishing it.

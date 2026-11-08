#!/usr/bin/env bash
#
# backup_restore.sh - Database & Media vault backup and restore tool for CNtagram.
# Supports both PostgreSQL (production) and SQLite (development/testing).
#
# Usage:
#   ./scripts/backup_restore.sh backup [output_dir]
#   ./scripts/backup_restore.sh restore <backup_archive_or_dump> [target_db_url]
#   ./scripts/backup_restore.sh test

set -euo pipefail

BACKUP_DIR="${2:-backups}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
mkdir -p "$BACKUP_DIR"

MEDIA_DIR="${MEDIA_ROOT:-media}"

# Read DATABASE_URL or fallback to local SQLite
DB_URL="${DATABASE_URL:-${EXTERNAL_DATABASE_URL:-}}"
if [[ -z "$DB_URL" && -f ".env.render" ]]; then
  DB_URL=$(grep -E "^EXTERNAL_DATABASE_URL=" .env.render | cut -d'=' -f2- | tr -d "'" | tr -d '"' || true)
fi
if [[ -z "$DB_URL" && -f ".env" ]]; then
  DB_URL=$(grep -E "^DATABASE_URL=" .env | cut -d'=' -f2- | tr -d "'" | tr -d '"' || true)
fi

backup() {
  echo "==> Starting CNtagram backup at $TIMESTAMP..."
  local db_backup_file=""

  if [[ -n "$DB_URL" && "$DB_URL" =~ ^postgres(ql)?:// ]]; then
    echo "--> Backing up PostgreSQL database..."
    db_backup_file="$BACKUP_DIR/db_${TIMESTAMP}.dump"
    pg_dump "$DB_URL" -Fc -f "$db_backup_file"
    echo "--> PostgreSQL dump saved: $db_backup_file"
  else
    echo "--> Backing up SQLite database..."
    db_backup_file="$BACKUP_DIR/db_${TIMESTAMP}.sqlite3"
    if [[ -f "db.sqlite3" ]]; then
      python -c "
import sqlite3, shutil
con = sqlite3.connect('db.sqlite3')
bck = sqlite3.connect('$db_backup_file')
con.backup(bck)
bck.close()
con.close()
"
      echo "--> SQLite backup saved: $db_backup_file"
    else
      echo "--> Warning: db.sqlite3 not found, skipping DB file copy."
    fi
  fi

  # Backup media vault if present
  local media_backup_file=""
  if [[ -d "$MEDIA_DIR" && $(ls -A "$MEDIA_DIR" 2>/dev/null) ]]; then
    echo "--> Backing up protected media vault..."
    media_backup_file="$BACKUP_DIR/media_${TIMESTAMP}.tar.gz"
    tar -czf "$media_backup_file" -C "$MEDIA_DIR" .
    echo "--> Media archive saved: $media_backup_file"
  else
    echo "--> Media folder empty or not present; skipping media archive."
  fi

  echo "==> Backup completed successfully at $(date)!"
  echo "    DB Backup: $db_backup_file"
  if [[ -n "$media_backup_file" ]]; then
    echo "    Media Backup: $media_backup_file"
  fi
}

restore() {
  local target_file="${1:-}"
  local target_db="${2:-$DB_URL}"
  if [[ -z "$target_file" ]]; then
    echo "Error: Must specify backup file to restore." >&2
    echo "Usage: ./scripts/backup_restore.sh restore <path_to_backup_file> [target_db_url]" >&2
    exit 1
  fi

  echo "==> Restoring from $target_file..."

  if [[ "$target_file" == *.dump ]]; then
    if [[ -z "$target_db" || "${ALLOW_DESTRUCTIVE_RESTORE:-}" != "YES" ]]; then
      echo "Error: restore requires target database URL and ALLOW_DESTRUCTIVE_RESTORE=YES." >&2
      exit 1
    fi

    # Safety Guard: Protect production against accidental restore
    local db_name
    db_name=$(echo "$target_db" | sed -E 's/.*\///; s/\?.*//')

    local is_production=0
    if [[ "$target_db" =~ (render\.com|onrender\.com) ]] || [[ "$db_name" != *"test"* && "$target_db" != *"localhost"* && "$target_db" != *"127.0.0.1"* ]]; then
      is_production=1
    fi

    if [[ "$is_production" -eq 1 ]]; then
      echo "⚠️  CRITICAL WARNING: Target database appears to be PRODUCTION ($db_name)!" >&2
      echo "To prevent accidental data destruction on production, you must set:" >&2
      echo "  CONFIRM_PRODUCTION_RESTORE=\"$db_name\"" >&2
      if [[ "${CONFIRM_PRODUCTION_RESTORE:-}" != "$db_name" ]]; then
        echo "ERROR: Restoration aborted. CONFIRM_PRODUCTION_RESTORE must match the target database name '$db_name'." >&2
        exit 1
      fi
    fi

    if ! command -v pg_restore >/dev/null 2>&1; then
      echo "Error: pg_restore is required to restore PostgreSQL dump." >&2
      exit 1
    fi

    echo "--> Restoring PostgreSQL database from $target_file to $db_name..."
    pg_restore --clean --if-exists --no-owner --no-privileges -d "$target_db" "$target_file"
    echo "--> PostgreSQL restore completed."

  elif [[ "$target_file" == *.sqlite3 ]]; then
    if [[ "${ALLOW_DESTRUCTIVE_RESTORE:-}" != "YES" ]]; then
      echo "Error: restore requires ALLOW_DESTRUCTIVE_RESTORE=YES." >&2
      exit 1
    fi
    echo "--> Restoring SQLite database to db.sqlite3..."
    cp "$target_file" db.sqlite3
    echo "--> SQLite restore completed."

  elif [[ "$target_file" == *.tar.gz ]]; then
    echo "--> Restoring media vault from $target_file..."
    mkdir -p "$MEDIA_DIR"
    tar -xzf "$target_file" -C "$MEDIA_DIR"
    echo "--> Media vault restore completed."

  else
    echo "Error: Unknown backup file format: $target_file" >&2
    exit 1
  fi

  echo "==> Restore finished successfully!"
}

test_routine() {
  echo "==> Running Backup & Restore Verification Test..."
  local test_dir="$BACKUP_DIR/test_$TIMESTAMP"
  mkdir -p "$test_dir"

  # Perform backup
  echo "--> 1. Executing backup..."
  BACKUP_DIR="$test_dir" backup

  echo "--> 2. Verifying created files..."
  local count
  count=$(find "$test_dir" -type f | wc -l)
  if [[ "$count" -eq 0 ]]; then
    echo "Error: No backup files were generated!"
    exit 1
  fi
  echo "✓ Generated $count backup file(s) in $test_dir."

  echo "--> 3. Validating archive/dump integrity..."
  for f in "$test_dir"/*; do
    if [[ "$f" == *.tar.gz ]]; then
      tar -tzf "$f" >/dev/null
      echo "✓ Valid tar.gz archive: $(basename "$f")"
    elif [[ "$f" == *.sqlite3 ]]; then
      python -c "import sqlite3; con = sqlite3.connect('$f'); con.execute('PRAGMA integrity_check;').fetchall(); con.close()"
      echo "✓ Valid SQLite database: $(basename "$f")"
    elif [[ "$f" == *.dump ]]; then
      if ! command -v pg_restore >/dev/null 2>&1; then
        echo "ERROR: pg_restore is required to inspect PostgreSQL dump file $f" >&2
        exit 1
      fi
      pg_restore --list "$f" >/dev/null
      echo "✓ Valid PostgreSQL dump archive: $(basename "$f")"
    fi
  done

  echo "--> 4. Testing actual restore and table count comparison..."
  # Never restore into the source/production database.
  for f in "$test_dir"/*.dump; do
    [[ -f "$f" ]] || continue
    local test_db="${RESTORE_TEST_DATABASE_URL:-}"
    if [[ -z "$test_db" || "$test_db" == "$DB_URL" ]]; then
      echo "ERROR: Set RESTORE_TEST_DATABASE_URL to a separate disposable PostgreSQL database." >&2
      return 1
    fi
    # Explicit database names prevent accidental restores to production.
    if [[ "$test_db" != *"_restore_test"* && "$test_db" != *"test_db"* && "$test_db" != *"test"* ]]; then
      echo "ERROR: restore test target database name must contain '_restore_test' or 'test'." >&2
      return 1
    fi
    if ! command -v pg_restore >/dev/null 2>&1; then
      echo "ERROR: pg_restore is required for PostgreSQL restore verification test." >&2
      return 1
    fi
    echo "--> Restoring dump into isolated test database..."
    pg_restore --clean --if-exists --exit-on-error --no-owner --no-privileges -d "$test_db" "$f"

    echo "--> Comparing table row counts between source and restored database..."
    DB_URL="$DB_URL" RESTORE_TEST_DATABASE_URL="$test_db" python -c "
import os, sys, psycopg2

src_url = os.environ.get('DB_URL', '')
dst_url = os.environ.get('RESTORE_TEST_DATABASE_URL', '')

if not src_url or not dst_url:
    print('ERROR: Missing DB_URL or RESTORE_TEST_DATABASE_URL', file=sys.stderr)
    sys.exit(1)

try:
    src_conn = psycopg2.connect(src_url)
    dst_conn = psycopg2.connect(dst_url)
except Exception as e:
    print(f'ERROR connecting to PostgreSQL: {e}', file=sys.stderr)
    sys.exit(1)

with src_conn.cursor() as src_cur, dst_conn.cursor() as dst_cur:
    src_cur.execute('''
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    ''')
    tables = [r[0] for r in src_cur.fetchall()]
    if not tables:
        print('ERROR: No public tables found in source database.', file=sys.stderr)
        sys.exit(1)

    print(f'Verifying {len(tables)} tables between source and restored database...')
    mismatches = []
    for t in tables:
        src_cur.execute(f'SELECT count(*) FROM \"{t}\"')
        src_cnt = src_cur.fetchone()[0]
        dst_cur.execute(f'SELECT count(*) FROM \"{t}\"')
        dst_cnt = dst_cur.fetchone()[0]
        if src_cnt != dst_cnt:
            mismatches.append(f'{t}: src={src_cnt} vs restored={dst_cnt}')
        else:
            print(f'  ✓ {t}: {src_cnt} rows (OK)')

    if mismatches:
        print('ERROR: Table row count mismatches found:', file=sys.stderr)
        for m in mismatches:
            print(f'  - {m}', file=sys.stderr)
        sys.exit(1)

print(f'✓ PostgreSQL table row verification passed ({len(tables)} tables matched 100%)')
"
    echo "PostgreSQL restore succeeded and verified against isolated test database."
  done
  for f in "$test_dir"/*; do
    if [[ "$f" == *.sqlite3 ]]; then
      local restored="$test_dir/restored.sqlite3"
      cp "$f" "$restored"
      python -c "
import sqlite3, sys, os
if os.path.exists('db.sqlite3'):
    src = sqlite3.connect('db.sqlite3')
    dst = sqlite3.connect(r'$restored')
    tables = [t for (t,) in src.execute(\"select name from sqlite_master where type='table'\")]
    key_tables = {'department', 'batch', 'course', 'batch_course', 'app_user', 'role', 'user_role', 'doc_type', 'exam_period', 'doc_type_required_role', 'document'}
    for t in tables:
        a = src.execute(f'select count(*) from \"{t}\"').fetchone()[0]
        b = dst.execute(f'select count(*) from \"{t}\"').fetchone()[0]
        assert a == b, f'Mismatch in table {t}: {a} vs {b}'
        if t in key_tables:
            print(f'  - {t}: src={a}, restored={b} (OK)')
    print(f'✓ SQLite table row verification passed ({len(tables)} tables matched 100%)')
else:
    print('✓ SQLite restore verification skipped (no local db.sqlite3)')
"
    fi
  done

  # Cleanup test files
  rm -rf "$test_dir"
  echo "==> Backup and Restore verification passed 100%! Ready for production."
}

action="${1:-backup}"
case "$action" in
  backup)
    backup
    ;;
  restore)
    restore "${2:-}" "${3:-}"
    ;;
  test)
    test_routine
    ;;
  *)
    echo "Usage: $0 {backup|restore|test}"
    exit 1
    ;;
esac

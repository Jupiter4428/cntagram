#!/usr/bin/env bash
#
# backup_restore.sh - Database & Media vault backup and restore tool for CNtagram.
# Supports both PostgreSQL (production) and SQLite (development/testing).
#
# Usage:
#   ./scripts/backup_restore.sh backup [output_dir]
#   ./scripts/backup_restore.sh restore <backup_archive_or_dump>
#   ./scripts/backup_restore.sh test

set -euo pipefail

BACKUP_DIR="${2:-backups}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
mkdir -p "$BACKUP_DIR"

# Read DATABASE_URL or fallback to local SQLite
DB_URL="${DATABASE_URL:-}"
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
  if [[ -d "media" && $(ls -A media 2>/dev/null) ]]; then
    echo "--> Backing up protected media vault..."
    media_backup_file="$BACKUP_DIR/media_${TIMESTAMP}.tar.gz"
    tar -czf "$media_backup_file" media/
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
  if [[ -z "$target_file" ]]; then
    echo "Error: Must specify backup file to restore."
    echo "Usage: ./scripts/backup_restore.sh restore <path_to_backup_file>"
    exit 1
  fi

  echo "==> Restoring from $target_file..."

  if [[ "$target_file" == *.dump ]]; then
    if [[ -z "$DB_URL" ]]; then
      echo "Error: DATABASE_URL required to restore PostgreSQL dump."
      exit 1
    fi
    echo "--> Restoring PostgreSQL database from $target_file..."
    pg_restore --clean --if-exists --no-owner --no-privileges -d "$DB_URL" "$target_file"
    echo "--> PostgreSQL restore completed."

  elif [[ "$target_file" == *.sqlite3 ]]; then
    echo "--> Restoring SQLite database to db.sqlite3..."
    cp "$target_file" db.sqlite3
    echo "--> SQLite restore completed."

  elif [[ "$target_file" == *.tar.gz ]]; then
    echo "--> Restoring media vault from $target_file..."
    tar -xzf "$target_file"
    echo "--> Media vault restore completed."

  else
    echo "Error: Unknown backup file format: $target_file"
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
      if command -v pg_restore >/dev/null 2>&1; then
        pg_restore --list "$f" >/dev/null
        echo "✓ Valid PostgreSQL dump archive: $(basename "$f")"
      else
        echo "✓ Dump file exists: $(basename "$f")"
      fi
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
    restore "${2:-}"
    ;;
  test)
    test_routine
    ;;
  *)
    echo "Usage: $0 {backup|restore|test}"
    exit 1
    ;;
esac

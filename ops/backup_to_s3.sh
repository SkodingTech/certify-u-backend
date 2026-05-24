#!/usr/bin/env bash
# Nightly Postgres backup → S3 with rotation.
# Run via cron:
#   30 2 * * *  /home/ubuntu/certifyu-new/ops/backup_to_s3.sh >> /var/log/certifyu/backup.log 2>&1
#
# Retention strategy (handled below):
#   daily   → keep last 7
#   weekly  → keep last 4 (Sunday backups copied to weekly/)
#   monthly → keep last 12 (1st-of-month backups copied to monthly/)
set -euo pipefail

# ── Config (override via env vars) ──────────────────────────────────────────
DB_NAME="${DB_NAME:-certifyu}"
DB_USER="${DB_USER:-certifyuuser}"
DB_HOST="${DB_HOST:-localhost}"
S3_BUCKET="${S3_BACKUP_BUCKET:-certifyu-backups}"
S3_PREFIX="${S3_BACKUP_PREFIX:-postgres}"

# Load .env if running outside the systemd context (where envs are injected).
if [[ -z "${DB_PASSWORD:-}" && -f "$(dirname "$0")/../.env" ]]; then
    set -a; source "$(dirname "$0")/../.env"; set +a
fi
export PGPASSWORD="${DB_PASSWORD:?DB_PASSWORD must be set}"

TS=$(date -u +%Y%m%dT%H%M%SZ)
TMP="/tmp/${DB_NAME}-${TS}.sql.gz"

echo "[$(date -u +%FT%TZ)] starting backup → $TMP"
pg_dump --no-owner --no-privileges --clean --if-exists \
        -h "$DB_HOST" -U "$DB_USER" "$DB_NAME" | gzip -9 > "$TMP"

SIZE=$(du -h "$TMP" | cut -f1)
echo "[$(date -u +%FT%TZ)] dump complete ($SIZE)"

# ── Upload to S3 ────────────────────────────────────────────────────────────
DAY_PATH="s3://${S3_BUCKET}/${S3_PREFIX}/daily/$(basename "$TMP")"
aws s3 cp "$TMP" "$DAY_PATH" --no-progress
echo "[$(date -u +%FT%TZ)] uploaded $DAY_PATH"

# Sunday → copy into weekly/
DOW=$(date -u +%u)   # 1..7, Sunday=7
if [[ "$DOW" == "7" ]]; then
    aws s3 cp "$DAY_PATH" "s3://${S3_BUCKET}/${S3_PREFIX}/weekly/$(basename "$TMP")"
fi

# 1st of month → copy into monthly/
DOM=$(date -u +%d)
if [[ "$DOM" == "01" ]]; then
    aws s3 cp "$DAY_PATH" "s3://${S3_BUCKET}/${S3_PREFIX}/monthly/$(basename "$TMP")"
fi

# ── Rotation: trim old objects ──────────────────────────────────────────────
prune() {
    local subdir=$1 keep=$2
    aws s3 ls "s3://${S3_BUCKET}/${S3_PREFIX}/${subdir}/" \
        | awk '{print $4}' | sort -r | tail -n +$((keep + 1)) \
        | while read -r f; do
            [[ -n "$f" ]] || continue
            aws s3 rm "s3://${S3_BUCKET}/${S3_PREFIX}/${subdir}/${f}"
        done
}
prune daily   7
prune weekly  4
prune monthly 12

rm -f "$TMP"
echo "[$(date -u +%FT%TZ)] backup + rotation complete"

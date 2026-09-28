#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-/srv/braink-beta}"
CRON_SRC="$ROOT_DIR/deployment/cron.d/braink-d030-production"
NFT_SRC="$ROOT_DIR/deployment/network/braink-nftables.conf"
PGHBA_SRC="$ROOT_DIR/deployment/network/pg_hba.conf"
CRON_DST="/etc/cron.d/braink-d030-production"
NFT_DST="/etc/nftables.d/braink-braink-beta.conf"
PGHBA_DST="${PGHBA_PATH:-}"

die() { printf '[BRAINK_DEPLOY_BLOCKED] %s\n' "$*" >&2; exit 2; }
need() { command -v "$1" >/dev/null 2>&1 || die "missing binary: $1"; }

[[ "$(id -u)" -eq 0 ]] || die "root required"
[[ -f "$CRON_SRC" ]] || die "missing cron source"
[[ -f "$NFT_SRC" ]] || die "missing nftables source"
[[ -f "$PGHBA_SRC" ]] || die "missing pg_hba source"
[[ -n "${DB_CONN_STR:-}" ]] || die "DB_CONN_STR required for recovery execution"
[[ -n "$PGHBA_DST" ]] || die "PGHBA_PATH required; refusing to guess PostgreSQL configuration path"

need nft
need psql
need install
need sha256sum

# Validate without mutating.
nft -c -f "$NFT_SRC"
psql "$DB_CONN_STR" -v ON_ERROR_STOP=1 -c 'SELECT 1' >/dev/null

install -d -m 0755 /etc/nftables.d /var/log/braink
install -m 0644 "$CRON_SRC" "$CRON_DST"
install -m 0644 "$NFT_SRC" "$NFT_DST"

backup="$PGHBA_DST.braink-backup.$(date -u +%Y%m%dT%H%M%SZ)"
cp --preserve=mode,ownership,timestamps "$PGHBA_DST" "$backup"
install -m 0600 "$PGHBA_SRC" "$PGHBA_DST"

# Apply firewall only after syntax validation and configuration installation.
nft -f "$NFT_DST"

# PostgreSQL reload is explicit and configurable; never guess a service name.
if [[ -n "${POSTGRES_RELOAD_CMD:-}" ]]; then
  bash -lc "$POSTGRES_RELOAD_CMD"
else
  printf '[BRAINK_DEPLOY_PARTIAL] pg_hba installed but PostgreSQL reload not invoked; set POSTGRES_RELOAD_CMD.\n' >&2
fi

printf '[BRAINK_DEPLOYED] cron_sha256=%s nft_sha256=%s pghba_sha256=%s backup=%s\n' \
  "$(sha256sum "$CRON_DST" | awk '{print $1}')" \
  "$(sha256sum "$NFT_DST" | awk '{print $1}')" \
  "$(sha256sum "$PGHBA_DST" | awk '{print $1}')" \
  "$backup"
printf '[BRAINK_READBACK] nft_ruleset_sha256=%s\n' "$(nft list ruleset | sha256sum | awk '{print $1}')"

#!/usr/bin/env bash
# 로컬 시험대 띄우기 — 진짜 PostgreSQL 16 + PostgREST 12 + 가짜 Supabase Auth(게이트웨이 :8767)
# 사용: bash tools/testbed_up.sh        (다시 실행하면 스키마를 새로 깔고 전부 다시 띄운다)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; W="${TESTBED_DIR:-/tmp/pcs-testbed}"; PGBIN=/usr/lib/postgresql/16/bin; PORT=54329
mkdir -p "$W"; chmod 755 "$W"; chown postgres "$W"
if [ ! -x "$W/postgrest" ]; then
  curl -sSL -o "$W/pgrst.tar.xz" https://github.com/PostgREST/postgrest/releases/download/v12.2.3/postgrest-v12.2.3-linux-static-x64.tar.xz
  tar xJf "$W/pgrst.tar.xz" -C "$W"; fi
if [ ! -x "$W/deno" ]; then   # Edge Function(Deno) 시험용
  curl -sSL -o "$W/deno.zip" https://github.com/denoland/deno/releases/download/v2.5.6/deno-x86_64-unknown-linux-gnu.zip && (cd "$W" && unzip -q -o deno.zip); fi
if [ ! -d "$W/data" ]; then mkdir -p "$W/data"; chown postgres "$W/data"
  su postgres -c "$PGBIN/initdb -D $W/data -U postgres --auth=trust -E UTF8 --locale=C.UTF-8 >/dev/null"; fi
chown -R postgres "$W/data"
su postgres -c "$PGBIN/pg_ctl -D $W/data status" >/dev/null 2>&1 || su postgres -c "$PGBIN/pg_ctl -D $W/data -o '-p $PORT -k $W' -l $W/pg.log start" >/dev/null
for i in $(seq 1 20); do psql -h 127.0.0.1 -p $PORT -U postgres -c 'select 1' >/dev/null 2>&1 && break; sleep 0.5; done
P="psql -h 127.0.0.1 -p $PORT -U postgres -v ON_ERROR_STOP=1 -q"
[ -f "$W/pgrst.pid" ] && kill "$(cat $W/pgrst.pid)" 2>/dev/null || true
[ -f "$W/gw.pid" ] && kill "$(cat $W/gw.pid)" 2>/dev/null || true
sleep 0.5
$P -c "drop database if exists pcs" -c "create database pcs"
$P -d pcs -f "$ROOT/app/server/testbed/supabase_shim.sql" 2>&1 | grep -v NOTICE || true
$P -d pcs -f "$ROOT/app/server/schema.sql" 2>&1 | grep -v NOTICE || true
SECRET=testbed-secret-that-is-at-least-32-chars-long
PGRST_DB_URI="postgres://authenticator:testbed@127.0.0.1:$PORT/pcs" PGRST_DB_SCHEMAS=public PGRST_DB_ANON_ROLE=anon \
  PGRST_JWT_SECRET=$SECRET PGRST_SERVER_PORT=3001 PGRST_DB_CHANNEL_ENABLED=true nohup "$W/postgrest" >"$W/pgrst.log" 2>&1 & echo $! > "$W/pgrst.pid"
JWT_SECRET=$SECRET nohup python3 "$ROOT/app/server/testbed/gateway.py" >"$W/gw.log" 2>&1 & echo $! > "$W/gw.pid"
for i in $(seq 1 30); do curl -s http://127.0.0.1:8767/__anon >/dev/null 2>&1 && curl -s http://127.0.0.1:3001/ >/dev/null 2>&1 && break; sleep 0.5; done
echo "testbed up · gateway http://127.0.0.1:8767 · PostgREST :3001 · Postgres :$PORT"

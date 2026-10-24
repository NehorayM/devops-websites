#!/usr/bin/env bash
# Same checks as run.sh, without Docker: starts a throwaway local Postgres (initdb/pg_ctl on PATH or under
# /usr/lib/postgresql/*/bin), installs the SQL, runs every suite. Run as a user that may run postgres (not root),
# or as root with a `postgres` system user. Usage: ./sql_tests/run_local.sh
set -euo pipefail
cd "$(dirname "$0")/.."
BIN=$(dirname "$(command -v pg_ctl 2>/dev/null || ls -d /usr/lib/postgresql/*/bin/pg_ctl | tail -1)")
DIR=$(mktemp -d /tmp/shipit-sql.XXXXXX); PORT=5499
AS=""; if [ "$(id -u)" = 0 ]; then chown postgres "$DIR"; AS="su postgres -c"; fi
run(){ if [ -n "$AS" ]; then $AS "$*"; else sh -c "$*"; fi; }
cleanup(){ run "$BIN/pg_ctl -D $DIR/data stop -m immediate" >/dev/null 2>&1 || true; rm -rf "$DIR"; }
trap cleanup EXIT
run "$BIN/initdb -D $DIR/data -A trust -U postgres" >/dev/null
run "$BIN/pg_ctl -D $DIR/data -o '-p $PORT -k $DIR -c listen_addresses=' -l $DIR/log -w start" >/dev/null
P="psql -h $DIR -p $PORT -U postgres"
$P -q -c 'create database neon' postgres
for f in sql_tests/harness.sql supabase_casino.sql supabase_casino_v2.sql supabase_duel.sql supabase_duel_v2.sql supabase_exam_history.sql supabase_leaderboard.sql supabase_tournament.sql supabase_duel_v2.sql; do
  echo "--- installing $f"; $P -d neon -q -v ON_ERROR_STOP=1 -f "$f" >/dev/null
done
for s in suite exam_history_suite duel_v2_suite leaderboard_suite tournament_suite; do
  echo "--- $s"
  $P -d neon -f "sql_tests/$s.sql" 2>&1 | grep -E "PASS|FAIL|ERROR|ALL CHECKS" | sed 's/^psql:[^ ]* //;s/^NOTICE:  //'
done
echo "--- tournament: two starts at the same instant"
U=11111111-1111-4111-8111-111111111111
$P -d neon -qAt -c "delete from public.tournaments; insert into public.wallets (user_id, chips) values ('$U', 1000) on conflict (user_id) do update set chips = 1000;" >/dev/null
for n in 1 2 3 4; do
  $P -d neon -qAt -c "select set_config('test.uid','$U',false); select pg_sleep(0.3); select public.tourney_start(250)->>'ok';" >/dev/null 2>&1 &
done
wait
OPEN=$($P -d neon -qAt -c "select count(*) from public.tournaments where status='active';")
CHIPS=$($P -d neon -qAt -c "select chips from public.wallets where user_id='$U';")
if [ "$OPEN" = "1" ] && [ "$CHIPS" = "750" ]; then echo "PASS  four starts at once: one tournament, one buy-in taken"; else echo "FAIL  four starts at once: $OPEN open, $CHIPS chips left"; fi

#!/bin/bash
# Run regression tests locally.
#
# Prerequisites:
#   - $SUPABASE_KEY must be set to the Supabase service role key
#   - Node.js installed
#   - Python 3 installed (for http.server)
#
# Usage:
#   ./scripts/local-test.sh                    # run all tests
#   ./scripts/local-test.sh spec pick-roundtrip # run one spec
#   ./scripts/local-test.sh run-all            # run all baselines
#   ./scripts/local-test.sh list               # list available tests
#
# Any arguments are passed through to test.sh.

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CITY_DIR="$REPO_ROOT/cities/santarosa"
TRACE_TOOLS="$CITY_DIR/trace-tools"
PORT=8080
SUPABASE_URL="https://dzpdualvwspgqghrysyz.supabase.co"
TEST_USER_EMAIL="ci-test@community-calendar.test"

# --- Check prerequisites ---

if [ -z "$SUPABASE_KEY" ]; then
  echo "Error: \$SUPABASE_KEY must be set to the Supabase service role key"
  exit 1
fi

# --- Ensure trace-tools is cloned and installed ---

if [ ! -d "$TRACE_TOOLS" ]; then
  echo "Cloning trace-tools..."
  git clone https://github.com/xmlui-org/trace-tools.git "$TRACE_TOOLS"
  cd "$TRACE_TOOLS"
  npm install
  npx playwright install chromium
  cd "$REPO_ROOT"
elif [ ! -d "$TRACE_TOOLS/node_modules" ]; then
  echo "Installing trace-tools dependencies..."
  cd "$TRACE_TOOLS"
  npm install
  npx playwright install chromium
  cd "$REPO_ROOT"
fi

# --- Start local server if not already running ---

if curl -s http://localhost:$PORT >/dev/null 2>&1; then
  echo "Server already running on port $PORT"
  SERVER_PID=""
else
  echo "Starting local server on port $PORT..."
  cd "$REPO_ROOT"
  python3 -m http.server $PORT &
  SERVER_PID=$!
  # Wait for server to be ready
  for i in $(seq 1 10); do
    curl -s http://localhost:$PORT >/dev/null 2>&1 && break
    sleep 0.5
  done
fi

# --- Ensure trace-capture symlink for specs ---

mkdir -p "$TRACE_TOOLS/capture-scripts"
[ -e "$TRACE_TOOLS/capture-scripts/trace-capture.ts" ] || \
  ln -s ../trace-capture.ts "$TRACE_TOOLS/capture-scripts/trace-capture.ts"

# --- Mint test session ---

echo "Minting test session..."
SUPABASE_URL="$SUPABASE_URL" \
SUPABASE_SERVICE_KEY="$SUPABASE_KEY" \
TEST_USER_EMAIL="$TEST_USER_EMAIL" \
BASE_URL="http://localhost:$PORT" \
  node "$CITY_DIR/traces/mint-session.js"

# --- Run tests ---

cd "$CITY_DIR"
chmod +x test.sh

if [ $# -eq 0 ]; then
  # No args: run all baselines (same as CI)
  ./test.sh run-all
else
  ./test.sh "$@"
fi
TEST_EXIT=$?

# --- Cleanup ---

if [ -n "$SERVER_PID" ]; then
  kill $SERVER_PID 2>/dev/null
fi

exit $TEST_EXIT

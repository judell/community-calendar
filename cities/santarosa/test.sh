#!/bin/bash
# Regression test runner for community-calendar (Santa Rosa)

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
TRACE_TOOLS="$APP_DIR/trace-tools"
REPO_ROOT="$APP_DIR/../.."

# Keep repo root copies in sync with trace-tools
cp "$TRACE_TOOLS/xs-trace.js" "$REPO_ROOT/xs-trace.js"
cp "$TRACE_TOOLS/xs-diff.html" "$REPO_ROOT/xs-diff.html"

source "$TRACE_TOOLS/test-base.sh"

#!/usr/bin/env sh
# Zenable plugin bootstrap (SessionStart): wire the CLI's hooks if it is installed.
#
# Never downloads or installs anything: installing the CLI needs the user's consent.
# Hooks only, for the same reason: the MCP server needs a one-time interactive login
# (`zenable install mcp`) that the user runs themselves.

wire_hooks() {
  ZENABLE_INVOCATION_SOURCE=claude-plugin ZENABLE_NONINTERACTIVE=1 \
    nohup zenable install hook "$1" >/dev/null 2>&1 &
}

if ! command -v zenable >/dev/null 2>&1; then
  echo "The zenable CLI is not installed, so Zenable's post-edit review is off. Mention this once if relevant, and ask the user before installing it. Install: https://cli.zenable.app Details: https://www.zenable.app/docs/integrations/mcp/getting-started"
  exit 0
fi

# Other clients also set CLAUDE_PLUGIN_ROOT, so it identifies Claude Code only when none
# of their own variables are set. An unrecognized client gets no hooks: wiring the wrong
# one would edit the settings of a tool the user didn't start.
if [ -n "${CURSOR_PLUGIN_ROOT:-}" ]; then
  wire_hooks cursor
elif [ -n "${PLUGIN_ROOT:-}" ]; then
  # Not only Codex sets PLUGIN_ROOT, so also require that it's in Codex's own directory
  case "$PLUGIN_ROOT" in
    "${CODEX_HOME:-$HOME/.codex}"/*) wire_hooks codex ;;
  esac
elif [ -n "${CLAUDE_PLUGIN_ROOT:-}" ]; then
  wire_hooks claude-code
fi

exit 0

#!/usr/bin/env sh
# Zenable plugin bootstrap (SessionStart): wire the CLI's hooks if it is installed.
#
# Never downloads or installs anything: installing the CLI needs the user's consent.
# Hooks only, for the same reason: the MCP server needs a one-time interactive login
# (`zenable install mcp claude-code`) that the user runs themselves.

if command -v zenable >/dev/null 2>&1; then
  ZENABLE_INVOCATION_SOURCE=claude-plugin ZENABLE_NONINTERACTIVE=1 \
    nohup zenable install hook claude-code >/dev/null 2>&1 &
else
  echo "The zenable CLI is not installed, so Zenable's post-edit review is off. Mention this once if relevant, and ask the user before installing it. Install: https://cli.zenable.app Details: https://www.zenable.app/docs/integrations/mcp/getting-started"
fi

exit 0

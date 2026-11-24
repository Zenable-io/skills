#!/usr/bin/env sh
# Zenable plugin bootstrap (SessionStart): wire the CLI's hooks if it is installed.
#
# Never downloads or installs anything: installing the CLI needs the user's consent.
# Hooks only, for the same reason: the MCP server needs a one-time interactive login
# (`zenable install mcp`) that the user runs themselves.

if ! command -v zenable >/dev/null 2>&1; then
  echo "The zenable CLI is not installed, so Zenable's post-edit review is off. Mention this once if relevant, and ask the user before installing it. Install: https://cli.zenable.app Details: https://www.zenable.app/docs/integrations/mcp/getting-started"
  exit 0
fi

# Reuse the IDE detection in the zenable hook handler. Descriptor 3 passes it the hook's
# JSON from stdin, because background commands lose stdin (and <&0 can't restore it in dash).
exec 3<&0
ZENABLE_INVOCATION_SOURCE=claude-plugin ZENABLE_NONINTERACTIVE=1 \
  nohup zenable install hook current <&3 >/dev/null 2>&1 &

exit 0

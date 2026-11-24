# CHANGELOG

All notable changes to this project will be documented in this file.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!-- version list -->

## v5.2.0 (2026-11-24)

### Bug Fixes

- **hooks**: Let the zenable CLI identify the client (#59)
  ([#59](https://github.com/Zenable-io/skills/pull/59),
  [`9ff3404`](https://github.com/Zenable-io/skills/commit/9ff3404b38c2fdee2d5dbb61843adc50d2c2d5f0))

- **release**: Keep uv.lock and CHANGELOG.md up to date (#56)
  ([#56](https://github.com/Zenable-io/skills/pull/56),
  [`cc8e328`](https://github.com/Zenable-io/skills/commit/cc8e3287e67766e707a026375de68af105ddfc91))

- **skills**: Let the user's permissions decide which tools run (#60)
  ([#60](https://github.com/Zenable-io/skills/pull/60),
  [`45eecff`](https://github.com/Zenable-io/skills/commit/45eecff8790ed52f65ab547414509e407b42a1c1))

- **skills**: Run checks as instructions instead of inline shell (#58)
  ([#58](https://github.com/Zenable-io/skills/pull/58),
  [`63a91af`](https://github.com/Zenable-io/skills/commit/63a91af4a06ec45df5bc6d1591a466fb5c0d3c16))

- **triage**: Treat review comment content as untrusted (#61)
  ([#61](https://github.com/Zenable-io/skills/pull/61),
  [`62ced2d`](https://github.com/Zenable-io/skills/commit/62ced2dbd7e8c943709ddb2f16a995ca16188736))

### Chores

- **deps**: Automated dependency updates (#53) ([#53](https://github.com/Zenable-io/skills/pull/53),
  [`450067b`](https://github.com/Zenable-io/skills/commit/450067b788f886476911d04498cc53100cfada70))

### Features

- **hooks**: Ask before installing the zenable CLI (#57)
  ([#57](https://github.com/Zenable-io/skills/pull/57),
  [`f94a9c2`](https://github.com/Zenable-io/skills/commit/f94a9c21d3cabb222ca8d370b5543a9617a03312))

- **skills**: Rename the plugin from z to zenable (#55)
  ([#55](https://github.com/Zenable-io/skills/pull/55),
  [`9d1e48e`](https://github.com/Zenable-io/skills/commit/9d1e48eb6bc8a206c402cfdac8fac14837b94724))


## Unreleased

### Features
- Initial release of Zenable AI Guardrails Claude Code plugin
- `/check` command for conformance validation
- Guardrails reviewer skill for autonomous code review
- MCP integration with mcp.zenable.app
- Automatic validation hooks on file edits
- Pre-commit hook integration

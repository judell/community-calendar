# Domain Documentation

This repo uses a **single-context** layout.

## Location

- **Context document**: `CONTEXT.md` at the repo root
- **ADRs**: `docs/adr/` directory

## Consumer rules

Skills like `improve-codebase-architecture`, `diagnose`, and `tdd` read these files to learn the project's domain language and architectural decisions.

### CONTEXT.md

A living document describing:
- Key domain concepts and terminology
- Business rules and constraints
- Important relationships between components

### ADRs (Architecture Decision Records)

Numbered markdown files in `docs/adr/` that record:
- What decision was made
- Why it was made
- What alternatives were considered
- What the consequences are

Format: `NNNN-title.md` (e.g., `0001-use-xmlui-for-ui.md`)

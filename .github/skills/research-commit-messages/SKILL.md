---
name: research-commit-messages
description: 'Create git commit messages for this research repository. Use when preparing commits, writing commit messages, or summarizing staged changes. Focus on the feature, workflow, artifact, or research capability added or changed. Avoid dataset sizes, metric values, benchmark counts, and other quantitative results in the commit message unless the numbers themselves are the change.'
argument-hint: 'Short summary of the staged change or intended commit scope'
---

# Research Commit Messages

## When to Use

- Creating a git commit in this repository
- Suggesting a commit message from staged changes or a diff summary
- Revising a draft commit message so it matches the repository's research style

## Goal

Write commit messages that describe the **feature or change itself**, not the supporting numbers around it.

For this repository, quantitative details such as dataset sizes, benchmark counts, edge counts, token counts, or intermediate results should usually live in docs, experiment notes, PR descriptions, or result files, not in the commit message.

## Rules

1. Focus the subject line on the main feature, capability, workflow, or research artifact that changed.
2. Do not highlight counts such as `4 RQs`, `1.1M edges`, `47k nodes`, `13GB`, or similar statistics unless the number is itself the feature being introduced.
3. Prefer concise subjects in the form `<scope>: <change>` when a scope is helpful.
4. If the change is mostly documentation, describe the research topic or documentation purpose, not the amount of material added.
5. If a commit body is needed, use it to explain intent or scope, while still avoiding unnecessary benchmark numbers.

## Suggested Scopes

- `research:` for problem framing, hypotheses, experiment design, and evaluation plans
- `docs:` for README, benchmark notes, and roadmap documents
- `data:` for dataset setup, adapters, and download workflows
- `infra:` for repo setup, ignore rules, or environment tooling
- `exp:` for runnable experiments and baseline implementations

## Procedure

1. Identify the primary change.
2. Name the capability, artifact, or workflow that changed.
3. Draft the shortest accurate subject line.
4. Remove counts, metrics, and numeric bragging unless they are essential to meaning.

## Good Examples

- `docs: define research agenda for temporal graph memory`
- `research: outline questions and hypotheses for TCGM`
- `data: add TGB-V2 dataset integration workflow`
- `infra: ignore local datasets and virtual environment`

## Avoid

- `docs: add 4 RQs and 4 hypotheses`
- `data: download 1.1M-edge TGB dataset`
- `repo: add 13GB LongMemEval dataset`

## Output Preference

When asked to commit, propose one primary commit message first. If multiple commits would be cleaner, explicitly suggest a split and provide one feature-focused message per commit.
# Handing a task to Codex

For the owner. Do this once per task card, in the order of `TASKS.md`.

## 1. Open the project

Open `C:\Dev\Proc React` in Codex. Codex reads `AGENTS.md` at the repo root by itself, so it
already knows the rules, the setup and the checks.

## 2. Paste this prompt

Replace `T-03` with the card you're on (both places).

```
Do task T-03 from docs/nextjs-rebuild/TASKS.md.

Before writing any code, read AGENTS.md, then docs/nextjs-rebuild/RULES.md,
ARCHITECTURE.md and API_CONTRACT.md, then the T-03 card and every file the card
lists under "Read".

Work on a new branch rebuild/T-03-<short-name> made from the rebuild branch.
Run the standard checks, the privacy scan and the card's own checks. Commit to the
task branch, but do not merge or push. Finish with the report described in AGENTS.md.
```

## 3. Bring the result back for review

Paste Codex's report into Claude Code and say "review T-03". Claude reruns the checks, reads
the diff against `RULES.md` and either merges the branch into `rebuild` or lists fixes to
send back to Codex.

## 4. After the merge

The reviewer ticks the card (`[ ]` becomes `[x]`) in `TASKS.md`. Move on to the next card.

## Watch-outs

- **T-21 (scanning)** handles borrower documents. Review it most carefully: no PDF bytes to
  any AI, no server key fallback.
- **T-30 to T-32** cover several tools per card. If Codex struggles, ask Claude to split the
  card into one card per tool.
- **T-40 and T-41** change Railway and the live domain. Do these with Claude, not Codex.

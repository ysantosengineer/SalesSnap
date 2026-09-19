# Git workflow

Never implement an entire stage in one giant branch. Split each stage into small branches representing logical units, using `feat/`, `fix/`, `test/`, `docs/`, `chore/`, `ci/`, or `refactor/`. A branch normally has 1–4 commits; a stage commonly has 8–20 real commits depending on complexity. Do not manufacture commits.

Use Conventional Commits, for example `feat(api): add health endpoint`, `test(api): add health endpoint tests`, and `ci: add backend test workflow`. Each commit is a comprehensible technical change.

Workflow: small change → validate → commit → next change. Do not finish a whole stage before committing. On a branch: validate, make a final unit commit if needed, inspect `git status` and `git log`, open a PR, integrate, update main, then start the next branch.

Do not use squash as the standard merge strategy and do not recommend Squash and merge. Prefer Rebase and merge to retain meaningful commits and linear history; use a merge commit only when justified. Do not use `git commit --amend` to combine independent units or interactive rebase merely to collapse valid commits.

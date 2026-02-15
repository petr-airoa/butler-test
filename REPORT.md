# GitButler Stacked Branches Experiment Report

## Objective

Learn GitButler's stacked branches workflow by building a real Python library (`textkit`) with two interdependent feature branches, creating PRs, modifying branches post-PR, and introducing a breaking change to observe conflict propagation.

## Environment

- **GitButler CLI**: `but` (installed as `but`)
- **Python**: 3.12, managed via `uv` 0.8.3
- **GitHub CLI**: `gh` for verification
- **Repo**: `github.com/petr-airoa/butler-test`

---

## Phase 1: Project Setup

### Actions
1. `uv init --lib --name textkit --vcs none` - created Python library scaffold
2. `uv add --dev pytest` - added test framework
3. Created `.gitignore`, cleaned up `__init__.py`
4. Committed and pushed to `main`
5. `but setup` - initialized GitButler workspace

### Findings

- **GitButler workspace branch**: `but setup` switches to a special `gitbutler/workspace` branch. All work happens here; GitButler manages virtual branches on top.
- **Teardown/setup cycle**: To add files to `main` after GitButler init, had to `but teardown`, commit to main, then `but setup` again. GitButler's workspace branch doesn't let you commit directly to main.
- **`but pull`**: After adding commits to main outside GitButler, used `but pull` to integrate upstream changes and rebase active branches.
- **Auto-created branch**: GitButler creates a default branch (`pk-branch-1`) on setup. Had to delete it before starting real work.
- **HTTPS vs SSH**: `gh auth` was configured for HTTPS but the remote was SSH. Had to switch remote URL to match.

---

## Phase 2: Branch 1 — Word Counter

### Actions
1. `but branch new feature-word-counter`
2. Created `src/textkit/word_counter.py` with: `count_words`, `word_frequencies`, `most_common_words`, `_normalize_words`
3. Created `tests/test_word_counter.py` (5 tests)
4. Staged files explicitly: `but stage <file> <branch>`
5. `but commit feature-word-counter -m "Add word counter module"`

### Findings

- **Unstaged changes area**: New files appear in a special `[unstaged changes]` area (shown as `zz` in status). Must explicitly stage to a branch with `but stage <file> <branch>`.
- **Staging model**: Unlike git where staging is global, GitButler stages files _to specific branches_. This is how it supports multiple virtual branches simultaneously.
- **Commit targets a branch**: `but commit <branch> -m "..."` — you specify which branch receives the commit, unlike git where you commit to HEAD.

---

## Phase 3: Branch 2 — Text Stats (Stacked)

### Actions
1. `but branch new --anchor feature-word-counter feature-text-stats` — created stacked branch
2. Created `src/textkit/text_stats.py` importing from `word_counter`
3. Created `tests/test_text_stats.py` (5 tests, 10 total)
4. All 10 tests passed
5. Staged and committed to `feature-text-stats`

### Findings

- **`--anchor` flag**: Creates a branch stacked on another. The new branch's base is the tip of the anchor branch, not main.
- **Status shows stack structure**: `but status` renders the stack visually:
  ```
  ╭┄ex [feature-text-stats]
  ●   Add text statistics module
  │
  ├┄wo [feature-word-counter]
  ●   Add word counter module
  ```
- **Workspace sees all branches**: Since both branches are "applied" in the workspace, all files from both branches are visible in the working directory simultaneously. Tests can import across branch boundaries.

---

## Phase 4: Push & Create PRs

### Actions
1. `but push` — pushed both branches
2. `but pr new feature-word-counter -m "..."` — created PR #1 targeting `main`
3. `but pr new feature-text-stats -m "..."` — created PR #2 targeting `feature-word-counter`

### Findings

- **`but push` is silent on success**: No output when branches are already up to date or push succeeds. Use `but status -r` to verify.
- **PR stacking works automatically**: PR #2 was auto-targeted to `feature-word-counter` (not main) because GitButler knows the stack structure.
- **First `pr new` for stacked branch failed**: When creating PR for branch 2, GitButler also tried to create a PR for branch 1 (which already existed), causing a 422 error. Retrying succeeded — it recognized the existing PR and only created the new one.
- **Stack footer in PRs**: GitButler adds a footer to each PR showing its position in the stack:
  ```
  This is part 2 of 2 in a stack made with GitButler:
  - 2 #2
  - 1 #1 👈
  ```
- **Forge auth required**: `but pr new` requires prior authentication via `but config forge auth`. This is separate from `gh auth`.

---

## Phase 5: Post-PR Modifications

### Actions
1. Added `count_unique_words()` to `word_counter.py` on branch 1
2. Added `vocabulary_richness()` to `text_stats.py` on branch 2 (imports from branch 1)
3. Staged, committed, and pushed each branch
4. All 12 tests passed

### Findings

- **Database lock on rapid operations**: Running `but stage` immediately after a background sync can hit `Error code 517: database is locked`. A brief wait resolves it.
- **Push updates PRs automatically**: After pushing, the GitHub PRs reflect the new commits. No manual PR update needed.
- **Cross-branch dependencies work in workspace**: Branch 2's code imports a function added in branch 1's latest commit. Since both branches coexist in the workspace, this works seamlessly during local development.

---

## Phase 6: Conflict Experiment

### Setup
Renamed `count_unique_words` → `unique_word_count` in branch 1 (`word_counter.py` and its test). Branch 2's `text_stats.py` still imported the old name.

### Actions
1. Renamed function in `word_counter.py`, updated `test_word_counter.py`
2. Branch 1 tests: 6/6 passed
3. Branch 2 tests: `ImportError: cannot import name 'count_unique_words'`
4. Staged and committed to branch 1
5. `but push` — pushed successfully
6. `but status` showed branch 2 commits with `◐` markers (needs rebase) before push, then `●` after

### Key Finding: Semantic Conflicts Pass Git Silently

**GitButler rebased branch 2 on top of updated branch 1 without any conflict.**

The rebase succeeded because there was no _textual_ overlap: branch 2's commits only add new files (`text_stats.py`, `test_text_stats.py`), and branch 1's rename only modifies existing files (`word_counter.py`, `test_word_counter.py`). Git sees no conflicting hunks.

However, the code was **semantically broken** — `text_stats.py` imported a name that no longer existed. This is only caught by running tests, not by git's merge machinery.

### Resolution
Updated the import in `text_stats.py` on branch 2 (`count_unique_words` → `unique_word_count`), committed, and pushed. All 12 tests green again.

### Implications
- **Stacked branches amplify semantic conflicts**: A rename in a base branch silently breaks all dependent branches. Git won't warn you.
- **CI on every branch in the stack is essential**: Without per-branch CI, broken imports/APIs propagate silently through the stack.
- **The `◐` marker in `but status`** indicates commits that haven't been rebased yet onto the latest base. After push/rebase, they become `●`.

---

## GitButler CLI Command Reference (as used)

| Command | Purpose |
|---|---|
| `but setup` | Initialize GitButler in a repo |
| `but teardown` | Exit GitButler mode, return to normal git |
| `but pull` | Integrate upstream changes, rebase active branches |
| `but branch new <name>` | Create a new branch |
| `but branch new --anchor <base> <name>` | Create a stacked branch |
| `but branch delete <name>` | Delete a branch |
| `but stage <file> <branch>` | Stage a file to a specific branch |
| `but commit <branch> -m "..."` | Commit staged changes to a branch |
| `but push` | Push all branches |
| `but push <branch>` | Push a specific branch |
| `but pr new <branch> -m "..."` | Create a PR for a branch |
| `but status` | Show workspace status |
| `but status -r` | Show status with remote/PR info |
| `but show <branch>` | Show branch details and commits |
| `but config forge auth` | Authenticate with GitHub/GitLab |
| `but integrate upstream` | (Does not exist — use `but pull`) |

## Status Symbols

| Symbol | Meaning |
|---|---|
| `●` | Commit is up to date |
| `◐` | Commit needs rebase onto updated base |
| `zz` | Unstaged changes area |

---

## Summary of Lessons Learned

1. **GitButler's mental model differs from git**: Branches are virtual and coexist in a single workspace. Staging is per-branch, not global.
2. **Stacking is explicit**: Use `--anchor` to declare dependencies between branches. GitButler renders and manages the stack.
3. **PRs auto-target correctly**: Stacked PRs target the preceding branch, not main. GitButler adds stack navigation to PR descriptions.
4. **Semantic conflicts are the real danger**: Git-level merge conflicts are rare in stacks (branches usually touch different files). The real risk is broken imports, changed APIs, and behavioral changes that pass rebase but fail tests.
5. **Push triggers rebase**: When you push a base branch with new commits, GitButler rebases dependent branches automatically.
6. **The CLI is database-backed**: Operations can fail with lock errors during background syncs. Brief retries resolve this.

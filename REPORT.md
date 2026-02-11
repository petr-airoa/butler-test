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

## Phase 7: Provoking a Git-Level Merge Conflict

### Goal

Phase 6 showed that a function rename in branch 1 causes only a **semantic** conflict — git rebases silently. This phase attempts a **real git-level add/add conflict** by creating `src/textkit/text_stats.py` on branch 1, which already exists on branch 2.

### Setup

Created a partial, different version of `text_stats.py` on branch 1 (`feature-word-counter`) — same file path as branch 2's version but with:
- Different module docstring
- Different import style (inline `import re` instead of top-level)
- Only 2 of branch 2's 5 functions (`sentence_count`, `average_word_length`)
- Different docstrings for the shared functions

### Actions

1. Wrote the conflicting `text_stats.py` on disk
2. `but stage src/textkit/text_stats.py feature-word-counter` — staged to branch 1
3. `but commit feature-word-counter -m "Add preliminary text stats helpers"` — committed
4. `but push` — pushed (silent success)
5. `but status -r` — checked for conflicts

### What Actually Happened: No Git Conflict

**Surprise: GitButler did NOT report a git-level merge conflict.** Despite both branches creating the same file, all commits showed `"conflicted": false` in JSON status.

Instead, GitButler's behavior was:

1. **Rebased branch 2 on top of updated branch 1** — the rebase succeeded because GitButler treats branch 2's commits as modifications to a file that now exists in the base (branch 1).
2. **Working tree showed branch 1's version** — after rebase, the on-disk file was branch 1's partial `text_stats.py` (2 functions).
3. **Surfaced the diff as "staged changes"** — the difference between branch 1's version (now the base) and branch 2's version appeared in a `[staged to feature-text-stats]` area, with the file locked to the relevant branch 2 commits:
   ```
   ╭┄i0 [staged to feature-text-stats]
   │ g0 M src/textkit/text_stats.py 🔒 a93cdc8, d31f10d
   ```
4. **Tests failed** — `ImportError: cannot import name 'reading_difficulty'` because the working tree had branch 1's partial version.

### Resolution

Restored branch 2's full `text_stats.py` to disk. Since this matched what the rebased commits expected, the diff vanished and the workspace became clean — no additional commit was needed.

- All 12 tests passed
- `but status -r` showed all `●` (up to date)

### Key Finding: GitButler's "Silent Merge" for Add/Add Conflicts

GitButler handles add/add conflicts **differently than vanilla git**:

| Scenario | Vanilla Git | GitButler |
|---|---|---|
| Both branches create same file | `CONFLICT (add/add)` — merge stops, conflict markers in file | Rebase succeeds silently |
| Conflict reporting | Explicit merge conflict state | Shows diff as "staged changes" to dependent branch |
| Working tree | Contains `<<<<<<<` markers | Contains base branch's version (clean, no markers) |
| Resolution | Manual edit + `git add` + `git commit` | Restore desired version on disk; diff disappears if it matches rebase result |
| `but resolve` needed? | N/A | No — `but resolve` was available but not triggered because commits weren't flagged as conflicted |

### Why No Conflict Was Detected

GitButler's virtual branch system treats the stack differently than `git rebase`:
- Branch 1's `text_stats.py` becomes part of the **base tree** for branch 2
- Branch 2's commits that create `text_stats.py` are reinterpreted as **modifications** to the already-existing file
- Since the rebase can apply branch 2's changes as patches on top of branch 1's version, there's no conflict from git's perspective

The result is correct in the commit history but the working tree temporarily shows the wrong version until the user resolves the discrepancy.

### Contrast with Phase 6 (Semantic Conflict)

| Aspect | Phase 6 (Rename) | Phase 7 (Add/Add) |
|---|---|---|
| Conflict type | Semantic (broken import) | File overlap (same path, different content) |
| Git detects it? | No | No (in GitButler's rebase model) |
| Working tree broken? | Yes (ImportError) | Yes (ImportError — missing functions) |
| How surfaced | Not at all — must run tests | Diff appears in "staged changes" area |
| Resolution | Edit import in branch 2, new commit | Restore full version on disk, no commit needed |

### Implications

1. **GitButler absorbs add/add conflicts** into its staged changes mechanism rather than halting with conflict markers. This is smoother but can be confusing — the working tree is subtly wrong.
2. **The `🔒` lock annotation** on staged files helps identify which commits are affected.
3. **`but resolve` exists but wasn't needed** — it's for commits explicitly marked as conflicted, which didn't happen here.
4. **Tests remain the ultimate safety net** — whether the conflict is semantic or textual, only running the test suite catches the breakage.

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
| `but resolve <commit>` | Enter conflict resolution mode for a conflicted commit |
| `but resolve status` | Show remaining conflicted files during resolution |
| `but resolve finish` | Finalize conflict resolution |
| `but resolve cancel` | Cancel conflict resolution |

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
7. **Add/add conflicts are absorbed, not flagged**: When two stacked branches create the same file, GitButler rebases silently and surfaces the diff as "staged changes" rather than stopping with conflict markers. The working tree is temporarily wrong but `but resolve` is not triggered.
8. **Tests are the only reliable conflict detector**: Both semantic conflicts (Phase 6) and file-overlap conflicts (Phase 7) pass through GitButler's rebase without explicit conflict flags. Only running the test suite catches the breakage.

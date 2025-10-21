# Git Branch Strategy

## Branch Structure

This repository uses a **two-branch workflow**:

### `main` - Stable Releases Only
- **Purpose:** Production-ready code only
- **Updates:** Only when features are complete and tested
- **Commits:** Clean, descriptive, one per feature/version
- **Users should clone from:** `main` for stable code

### `dev` - Active Development
- **Purpose:** Working branch for all development
- **Updates:** Frequent commits as work progresses
- **Commits:** Can be messy, WIP commits are fine
- **Claude Code works on:** `dev` exclusively

---

## Workflow

### Daily Development (Claude Code)
```bash
# Always work on dev branch
git checkout dev

# Make changes, commit often
git add .
git commit -m "WIP: feature progress"
git push origin dev
```

### Releasing to Main (When Ready)
```bash
# Ensure dev is up to date
git checkout dev
git pull origin dev

# Switch to main and merge
git checkout main
git pull origin main
git merge --squash dev

# Create clean release commit
git commit -m "Version X.X.X: Feature Name

Complete description of changes
"

# Push to main
git push origin main

# Return to dev for next work
git checkout dev
```

---

## Version Strategy

Versions follow semantic versioning: `MAJOR.MINOR.PATCH`

- **MAJOR** (v3.0.0): Breaking changes, major rewrites
- **MINOR** (v2.1.0): New features, non-breaking changes
- **PATCH** (v2.1.1): Bug fixes, small improvements

**Examples from this project:**
- v2.0.0 - MAJOR: Complete rewrite to use Plex API
- v2.1.0 - MINOR: Added scan limits, pagination, thumbnail slider
- v2.1.1 - PATCH: Implemented PlexAPI delete with auto-refresh

---

## For Users

**Want stable code?**
```bash
git clone https://github.com/ButtaJones/plex-poster-manager.git
git checkout main
```

**Want bleeding edge / latest features?**
```bash
git clone https://github.com/ButtaJones/plex-poster-manager.git
git checkout dev
```

**Updating your local copy:**
```bash
# For stable releases
git checkout main
git pull origin main

# For latest development
git checkout dev
git pull origin dev
```

---

## Benefits of This Approach

✅ **Clean main branch** - Easy to see project milestones
✅ **Freedom on dev** - Commit often without cluttering history
✅ **Easy rollback** - Main always has stable versions
✅ **Clear releases** - One commit per feature on main
✅ **Safe testing** - Test on dev before merging to main

---

## Commit Message Guidelines

### On `dev` branch:
- Can be casual: "fix thing", "WIP: trying X", "update docs"
- Commit often for safety

### On `main` branch:
- Must be descriptive and clean
- Follow this format:
```
TYPE: Short description (50 chars max)

Detailed explanation of what changed and why.
Can be multiple paragraphs.

- Bullet points for key changes
- List important details
- Mention breaking changes

Version: X.X.X
```

**Types:**
- `FEATURE:` - New functionality
- `FIX:` - Bug fixes
- `REFACTOR:` - Code cleanup, no behavior change
- `DOCS:` - Documentation updates
- `BREAKING:` - Breaking changes (increment MAJOR version)

---

## Current Status

- **Active Branch:** `dev`
- **Latest Stable:** `main` (v2.1.1)
- **Next Release:** TBD

---

**Questions?** This strategy keeps the project organized while allowing rapid development.

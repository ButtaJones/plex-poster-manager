# 📚 Documentation Index

Complete guide to all documentation in this repository.

**Last Updated:** 2025-10-20
**Current Version:** 2.1.1 (dev branch: 2.1.2-dev)

---

## 🚀 Getting Started

### **[README.md](README.md)** - Start Here!
**Purpose:** Main project documentation
**Read this for:**
- Project overview and features
- Quick start guide for first-time users
- Installation instructions
- Usage guide and common Plex server URLs
- Troubleshooting common issues

**Key Sections:**
- 🚀 Quick Start (First-Time GitHub Users)
- 🎯 What's New in v2.0 (Plex API Integration)
- Features and capabilities
- Getting Your Plex Token (REQUIRED)
- API endpoints reference

---

## 🔧 Technical Documentation

### **[PROJECT_CONTEXT.md](PROJECT_CONTEXT.md)** - Architecture Overview
**Purpose:** Complete project context and architecture
**Read this for:**
- Project goals and architecture
- Version history (v1.x → v2.0 evolution)
- Why we switched from filesystem to Plex API
- Technical learnings and decisions

**Key Sections:**
- Current approach: Plex API integration
- Version history and why things changed
- Important notes for future development
- API endpoints reference

---

### **[project_status.md](project_status.md)** - Current Status
**Purpose:** Live project status and setup guide
**Read this for:**
- Current version and status
- Setup instructions for backend/frontend
- How to start the application
- Known issues and limitations
- Testing checklist

**Key Sections:**
- Production readiness checklist
- Configuration requirements
- Known issues (high/medium priority)
- Next steps and future enhancements

---

### **[CLAUDE_CODE_INSTRUCTIONS.md](CLAUDE_CODE_INSTRUCTIONS.md)** - AI Development Guide
**Purpose:** Instructions for Claude Code to work on this project
**Read this for:**
- Understanding the autonomous debugging approach
- How Claude Code uses tools (Playwright, etc.)
- Project-specific debugging workflows
- Common mistakes to avoid

**Key Sections:**
- Tool usage (Playwright, filesystem, curl, GitHub)
- Debugging workflow
- Project-specific context (paths, architecture)
- Known issues and solutions

---

## 🛠️ Feature Documentation

### **[ARTWORK_DELETE_GUIDE.md](ARTWORK_DELETE_GUIDE.md)** - NEW! PlexAPI Delete
**Purpose:** Complete guide to artwork deletion implementation
**Read this for:**
- How artwork delete works with PlexAPI
- PlexAPI limitations (unlock vs delete)
- Testing instructions
- Troubleshooting delete issues

**Key Sections:**
- What was implemented
- PlexAPI limitations explained
- Delete flow diagram
- API response formats
- Frontend update suggestions

**Created:** 2025-10-20 (v2.1.1)

---

## 🐛 Troubleshooting

### **[DEBUGGING_GUIDE.md](DEBUGGING_GUIDE.md)** - Bug Fix Reference
**Purpose:** Critical bug fixes and troubleshooting
**Read this for:**
- How to debug scan issues
- Path scanning problems
- Token validation errors
- Empty scan results

**Key Sections:**
- Critical bug fixes applied
- Common issues and solutions
- Testing checklist
- Log file locations

---

### **[GET_PLEX_TOKEN.md](GET_PLEX_TOKEN.md)** - Token Retrieval
**Purpose:** Guide to getting your Plex authentication token
**Read this for:**
- Why token is required (v2.0+)
- 3 methods to get your token
- Token verification steps
- Troubleshooting expired tokens

**Key Sections:**
- Method 1: PowerShell script (Windows)
- Method 2: Browser HTML helper
- Method 3: Browser console (most reliable)
- Verification steps

---

## 📝 Project History

### **[CHANGES_SUMMARY.md](CHANGES_SUMMARY.md)** - Bug Fix Session Log
**Purpose:** Complete list of changes from bug fix session
**Read this for:**
- What files were modified
- How to transfer to another PC
- Version history
- Testing checklist

**Key Sections:**
- Files modified in bug fix session
- Transfer instructions (Git/manual/ZIP)
- Quick start on new PC
- Critical changes for testing

---

## 🌿 Git Workflow

### **[.github/BRANCH_STRATEGY.md](.github/BRANCH_STRATEGY.md)** - NEW! Branch Strategy
**Purpose:** Git branching and version strategy
**Read this for:**
- How branches are organized (main vs dev)
- Workflow for development and releases
- Semantic versioning explanation
- Commit message guidelines

**Key Sections:**
- Two-branch workflow (main + dev)
- Daily development workflow
- Releasing to main
- Version strategy (MAJOR.MINOR.PATCH)

**Created:** 2025-10-20

---

## 📊 Quick Reference

### Which Doc Do I Need?

**I'm a first-time user:**
→ Read [README.md](README.md)

**I want to understand the architecture:**
→ Read [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md)

**I need my Plex token:**
→ Read [GET_PLEX_TOKEN.md](GET_PLEX_TOKEN.md)

**Deleted posters still showing in Plex:**
→ Read [ARTWORK_DELETE_GUIDE.md](ARTWORK_DELETE_GUIDE.md)

**Scan returns 0 results:**
→ Read [DEBUGGING_GUIDE.md](DEBUGGING_GUIDE.md)

**I'm contributing to the project:**
→ Read [.github/BRANCH_STRATEGY.md](.github/BRANCH_STRATEGY.md)

**I want to know current status:**
→ Read [project_status.md](project_status.md)

**I'm Claude Code working on this:**
→ Read [CLAUDE_CODE_INSTRUCTIONS.md](CLAUDE_CODE_INSTRUCTIONS.md)

---

## 🎯 Documentation by Topic

### Setup & Installation
- [README.md](README.md) - Installation and setup
- [project_status.md](project_status.md) - Current status and setup

### Authentication
- [GET_PLEX_TOKEN.md](GET_PLEX_TOKEN.md) - Getting Plex token
- [DEBUGGING_GUIDE.md](DEBUGGING_GUIDE.md) - Token validation errors

### Features
- [ARTWORK_DELETE_GUIDE.md](ARTWORK_DELETE_GUIDE.md) - Delete/unlock artwork
- [README.md](README.md) - All features overview

### Architecture & Design
- [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) - Architecture and decisions
- [CLAUDE_CODE_INSTRUCTIONS.md](CLAUDE_CODE_INSTRUCTIONS.md) - Technical details

### Development
- [.github/BRANCH_STRATEGY.md](.github/BRANCH_STRATEGY.md) - Git workflow
- [CHANGES_SUMMARY.md](CHANGES_SUMMARY.md) - Recent changes

### Troubleshooting
- [DEBUGGING_GUIDE.md](DEBUGGING_GUIDE.md) - Common issues
- [project_status.md](project_status.md) - Known issues

---

## 📈 Version Documentation

### v2.1.1 (Current - Main Branch)
- PlexAPI delete implementation
- Automatic metadata refresh
- See: [ARTWORK_DELETE_GUIDE.md](ARTWORK_DELETE_GUIDE.md)

### v2.1.0
- Scan limit options
- Thumbnail size slider
- Pagination with Load More
- See: [project_status.md](project_status.md)

### v2.0.0 (MAJOR)
- Complete rewrite to use Plex API
- Professional approach (like Kometa/Tautulli)
- See: [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md)

### v1.x (Legacy)
- Filesystem scanning (deprecated)
- See: [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) for why we changed

---

## 🔄 Keeping Docs Updated

All documentation is:
- ✅ Version controlled in Git
- ✅ Saved on `dev` branch (latest)
- ✅ Merged to `main` on releases
- ✅ Available on GitHub

**Location:** https://github.com/ButtaJones/plex-poster-manager

**Branches:**
- `main` - Stable documentation
- `dev` - Latest documentation (may have unreleased features)

---

## 📞 Support

**Issues or questions?**
1. Check relevant documentation above
2. Review [DEBUGGING_GUIDE.md](DEBUGGING_GUIDE.md)
3. Check [project_status.md](project_status.md) for known issues
4. Open issue on [GitHub](https://github.com/ButtaJones/plex-poster-manager/issues)

---

**Last Updated:** 2025-10-20
**Documentation Count:** 9 markdown files
**Total Lines:** ~2,500 lines of documentation

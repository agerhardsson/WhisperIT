# WhisperIT - Git Branch Structure

## Overview

WhisperIT documentation has been organized into two git branches for clean separation of concerns.

## Branch Structure

### `main` Branch
- **Purpose**: Production application code
- **Content**: Application source code, dependencies, setup script
- **README**: Simple, focused (114 lines)
- **Files**:
  - `src/transcriber.py` - Core transcription engine
  - `src/gui.py` - Interactive CLI interface
  - `run.sh` - Automated setup and launch
  - `requirements.txt` - Python dependencies
  - **README.md** - Simple quick-start guide

### `docs` Branch
- **Purpose**: Comprehensive documentation
- **Content**: All detailed guides, references, and technical documentation
- **README**: Comprehensive documentation index
- **Files**:
  - All detailed documentation files:
    - QUICKSTART.md
    - SETUP.md
    - START_HERE.md
    - QUICK_REFERENCE.md
    - ARCHITECTURE.md
    - INDEX.md
    - PROJECT_STATUS.md
    - PROJECT_COMPLETE.md
    - And more...
  - All application source code (merged from main)

## Branch Comparison

| Aspect | Main | Docs |
|--------|------|------|
| **Purpose** | Application code | Documentation |
| **README size** | 114 lines | 209 lines |
| **Focus** | Clean, simple | Comprehensive guides |
| **Target audience** | Users running app | Users learning/reference |
| **Includes source code** | ✓ Yes | ✓ Yes |
| **Includes docs** | ✓ Minimal | ✓ Complete |

## Accessing Each Branch

### Using Main Branch (Default)
```bash
# Main is the default checkout
cd /Users/andreas.gerhardsson/Sites/WhisperIT
git branch  # Shows you're on main
```

### Switching to Docs Branch
```bash
git checkout docs
# Now you have access to all documentation
cat README.md        # Comprehensive guide
cat QUICKSTART.md    # 5-minute start
cat ARCHITECTURE.md  # Technical details
```

### Back to Main
```bash
git checkout main
# Clean, simple README with quick start
bash run.sh          # Run the application
```

## Use Cases

### I want to use WhisperIT
1. `git checkout main`
2. Read the simple README
3. Run `bash run.sh`

### I want to understand the system
1. `git checkout docs`
2. Read ARCHITECTURE.md
3. Review source code in `src/`

### I need detailed installation help
1. `git checkout docs`
2. Read SETUP.md
3. Follow step-by-step instructions

### I need a quick reference
1. `git checkout docs`
2. Read QUICK_REFERENCE.md
3. Use commands immediately

## Git Log

Both branches track the same project history with proper separation:

```
main:
  - 8540660: Simplify README - detailed docs on docs branch
  - feed995: Initial commit with full documentation

docs:
  - a11ec8a: Add comprehensive documentation guide to docs branch
  - 8540660: Simplify README - detailed docs on docs branch
  - feed995: Initial commit with full documentation
```

## Documentation Files Location

### On `main` branch
- Only: `README.md` (simple 114 lines)

### On `docs` branch
- `README.md` - Documentation index
- `QUICKSTART.md` - 5-minute quick start
- `SETUP.md` - Detailed installation
- `START_HERE.md` - Introduction
- `QUICK_REFERENCE.md` - Command reference
- `ARCHITECTURE.md` - Technical design
- `INDEX.md` - Full documentation index
- `PROJECT_STATUS.md` - Completion report
- `PROJECT_COMPLETE.md` - Project summary
- `README_FIRST.md` - Feature overview
- `FINAL_SUMMARY.md` - Session summary
- `DELIVERY_SUMMARY.md` - Feature delivery
- `STATUS.txt` - Status report
- `README_COMPLETE.md` - Complete guide
- `.whisperit_config.example` - Config template

## Switching Workflow

### Typical workflow for users:
```bash
# Start on main (default)
bash run.sh                  # Run the app

# Need help? Check docs
git stash                   # Save local changes if any
git checkout docs
cat QUICKSTART.md           # Read guide
git checkout main           # Back to app
```

### Typical workflow for developers:
```bash
# Work on code in main
git checkout main
# Make changes to source code
git add -A
git commit -m "Feature: ..."

# Update docs in docs branch
git checkout docs
git merge main             # Sync code changes
# Update documentation files
git add -A
git commit -m "Docs: ..."
```

## Benefits of This Structure

✓ **Clean separation** - Code and docs in separate branches  
✓ **Focused README** - Main has simple, action-oriented README  
✓ **Complete reference** - Docs branch has all detailed guides  
✓ **Shared history** - Both branches track project evolution  
✓ **Easy navigation** - Users can choose which branch to use  
✓ **Clear intent** - Branch name indicates content focus  

## Default Branch

The default branch is `main`, which gives users:
- Quick start instructions
- Application code ready to run
- Minimal documentation to read
- Clear call-to-action: `bash run.sh`

Users can explore detailed documentation by checking out the `docs` branch.

## Future Maintenance

### When adding features:
1. Make changes in `main` branch
2. Merge into `docs` branch
3. Update documentation files in `docs` branch
4. Keep both branches in sync

### When updating documentation:
1. Update in `docs` branch
2. Consider if main README needs adjustment
3. Keep main README focused and simple

---

**Current Status**: Main branch with simplified README and application code. Docs branch with comprehensive documentation.

**Default Checkout**: `main` (production-ready code)

**Documentation Checkout**: `git checkout docs` (all guides available)

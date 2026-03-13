# Pre-Commit Hooks

This project uses git pre-commit hooks to ensure code quality before commits are made.

## What the Hook Does

The pre-commit hook automatically runs before each commit and:

1. ✅ Runs `ruff check` to catch linting errors
2. ✅ Runs `ruff format --check` to ensure code is properly formatted

If either check fails, the commit is blocked until the issues are fixed.

## Installation

### Automatic Installation (Recommended)

```bash
make install-hooks
```

This will install the pre-commit hook automatically.

### Manual Installation

```bash
./scripts/install-hooks.sh
```

## Usage

Once installed, the hook runs automatically on every commit:

```bash
git commit -m "Your commit message"
```

Output example:
```
Running pre-commit checks...

🔍 Running ruff linting...
All checks passed!
✓ Ruff check passed
🔍 Checking code formatting...
11 files already formatted
✓ Formatting check passed

✓ All pre-commit checks passed!
```

## Fixing Issues

### Linting Errors

If you see linting errors:
```bash
# View the errors
python -m ruff check custom_components/ tests/ scraper/

# Fix automatically where possible
python -m ruff check --fix custom_components/ tests/ scraper/
```

### Formatting Issues

If you see formatting errors:
```bash
# Auto-format all files
make format
# or
python -m ruff format custom_components/ tests/ scraper/
```

## Bypassing the Hook

**Not recommended**, but if you need to bypass the hook:

```bash
git commit --no-verify -m "Your message"
```

Only use this in emergencies or when you're certain the code is correct.

## Troubleshooting

### Hook Not Running

If the hook isn't running:
```bash
# Check if hook exists and is executable
ls -la .git/hooks/pre-commit

# Reinstall if needed
make install-hooks
```

### "ruff: command not found"

The hook automatically falls back to `python -m ruff` if the `ruff` command isn't in your PATH. Ensure you have ruff installed:

```bash
pip install -r requirements-dev.txt
```

### Hook Runs But Always Fails

Make sure you're in the project root directory when committing:
```bash
cd /path/to/central-hudson-electric-rates
git commit -m "Your message"
```

## Benefits

- 🚀 **Catch errors early** - Before they reach CI/CD
- 🎨 **Consistent formatting** - All code follows the same style
- ⚡ **Fast feedback** - Know immediately if there's an issue
- 🛡️ **Prevent bad commits** - Can't commit code that doesn't pass checks

## Disabling the Hook

If you need to temporarily disable the hook:

```bash
# Rename the hook
mv .git/hooks/pre-commit .git/hooks/pre-commit.disabled

# Re-enable later
mv .git/hooks/pre-commit.disabled .git/hooks/pre-commit
```

Or simply use `--no-verify` on individual commits.

## For Contributors

If you're contributing to this project:

1. Install the pre-commit hook: `make install-hooks`
2. Make your changes
3. The hook will automatically check your code before commit
4. Fix any issues reported by the hook
5. Commit successfully!

This ensures all contributions meet the project's quality standards.
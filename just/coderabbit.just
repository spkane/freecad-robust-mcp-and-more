# CodeRabbit CLI commands
# Usage: just coderabbit::install, just coderabbit::review, etc.
#
# CodeRabbit CLI provides AI-powered code reviews in your terminal.
# https://www.coderabbit.ai/cli
#
# IMPORTANT - RATE LIMITS:
#   - Free tier: 1 review per hour
#   - Pro tier: 5 reviews per hour
#   Run reviews manually when needed to avoid hitting limits.
#
# Note: In CI, skip CodeRabbit CLI since the GitHub App handles PR reviews.
# These commands are for local, on-demand development workflow only.

# =============================================================================
# Installation
# =============================================================================

# Install CodeRabbit CLI using the official installer
install:
    @echo "Installing CodeRabbit CLI..."
    curl -fsSL https://cli.coderabbit.ai/install.sh | sh
    @echo ""
    @echo "CodeRabbit CLI installed. Run 'just coderabbit::login' to authenticate."

# Check if CodeRabbit CLI is installed
check-installed:
    @command -v coderabbit >/dev/null 2>&1 || { echo "CodeRabbit CLI not installed. Run: just coderabbit::install"; exit 1; }
    @coderabbit --version

# =============================================================================
# Authentication
# =============================================================================

# Login to CodeRabbit (opens browser for authentication)
login: check-installed
    coderabbit auth login

# Logout from CodeRabbit
logout: check-installed
    coderabbit auth logout

# Check authentication status
auth-status: check-installed
    coderabbit auth status

# =============================================================================
# Code Reviews
# =============================================================================

# Review staged changes (most common use case)
review: check-installed
    @echo "Reviewing staged changes..."
    git add -A
    coderabbit review --plain --type uncommitted
    git reset

# Review staged changes with auto-fix suggestions
review-fix: check-installed
    @echo "Reviewing staged changes with auto-fix..."
    git add -A
    coderabbit review --plain --type uncommitted --auto-fix
    git reset

# Review the last commit
review-last: check-installed
    coderabbit review --plain --type committed --base-commit HEAD~1

# Review changes since a specific commit (usage: just coderabbit::review-since abc123)
review-since commit: check-installed
    coderabbit review --plain --type committed --base-commit {{commit}}

# Review changes between current branch and main
review-branch: check-installed
    coderabbit review --plain --type committed --base-commit main

# =============================================================================
# Output Formats
# =============================================================================

# Generate prompt-only output (for AI agents like Claude Code)
prompt-only: check-installed
    git add -A
    coderabbit review --prompt-only --type uncommitted
    git reset

# Review with JSON output
review-json: check-installed
    git add -A
    coderabbit review --format json --type uncommitted
    git reset

# =============================================================================
# Configuration
# =============================================================================

# Show CodeRabbit configuration
config-show: check-installed
    coderabbit config show

# Show help for all CodeRabbit commands
help: check-installed
    coderabbit --help

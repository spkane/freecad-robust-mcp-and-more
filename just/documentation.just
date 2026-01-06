# Documentation commands
# Usage: just documentation::build, just documentation::serve, etc.

# Build documentation
build:
    uv run mkdocs build

# Build documentation with strict mode (fails on warnings, for CI)
build-strict:
    uv run mkdocs build --strict

# Serve documentation locally
serve:
    uv run mkdocs serve

# Build and open documentation in browser
open:
    uv run mkdocs build
    @if [[ "$OSTYPE" == "darwin"* ]]; then \
        open site/index.html; \
    elif command -v xdg-open &> /dev/null; then \
        xdg-open site/index.html; \
    else \
        echo "Documentation built at: site/index.html"; \
    fi

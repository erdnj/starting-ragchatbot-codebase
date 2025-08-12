#!/bin/bash

# Pre-commit hook script
# Copy this to .git/hooks/pre-commit to run automatically before commits

echo "🚀 Running pre-commit checks..."

# Format code
echo "🎨 Auto-formatting code..."
uv run black backend/

# Check formatting
echo "📋 Verifying formatting..."
uv run black backend/ --check
if [ $? -ne 0 ]; then
    echo "❌ Formatting check failed after auto-format. Please check for issues."
    exit 1
fi

# Run tests if they exist
if [ -d "backend/tests" ] && [ "$(ls -A backend/tests/*.py 2>/dev/null)" ]; then
    echo "🧪 Running tests..."
    uv run pytest backend/tests/ -q
    if [ $? -ne 0 ]; then
        echo "❌ Tests failed. Please fix before committing."
        exit 1
    fi
fi

echo "✅ Pre-commit checks passed!"
exit 0
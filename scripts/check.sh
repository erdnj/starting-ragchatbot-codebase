#!/bin/bash

# Run all quality checks
echo "🔍 Running code quality checks..."
echo ""

# Check code formatting
echo "📋 Checking code formatting..."
uv run black backend/ --check
FORMAT_STATUS=$?

if [ $FORMAT_STATUS -ne 0 ]; then
    echo "❌ Code formatting issues found. Run './scripts/format.sh' to fix."
else
    echo "✅ Code formatting is correct!"
fi

echo ""

# Run tests if they exist
if [ -d "backend/tests" ] && [ "$(ls -A backend/tests/*.py 2>/dev/null)" ]; then
    echo "🧪 Running tests..."
    uv run pytest backend/tests/ -v
    TEST_STATUS=$?
    
    if [ $TEST_STATUS -ne 0 ]; then
        echo "❌ Some tests failed."
    else
        echo "✅ All tests passed!"
    fi
else
    echo "ℹ️  No tests found to run."
fi

echo ""

# Summary
if [ $FORMAT_STATUS -eq 0 ]; then
    echo "🎉 All checks passed!"
    exit 0
else
    echo "⚠️  Some checks failed. Please fix the issues above."
    exit 1
fi
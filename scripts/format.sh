#!/bin/bash

# Format Python code with black
echo "🎨 Formatting Python code with black..."
uv run black backend/ --check --diff 2>/dev/null

if [ $? -ne 0 ]; then
    echo "📝 Files need formatting. Running black..."
    uv run black backend/
    echo "✅ Formatting complete!"
else
    echo "✅ All files are properly formatted!"
fi
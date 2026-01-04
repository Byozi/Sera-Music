#!/bin/bash
# ==============================================================================
# cleanup.sh - Clean up downloaded files and cache
# ==============================================================================
# This script removes all downloaded media files and cache to free up space.
# Run this periodically to prevent disk space issues.
# Usage: bash cleanup.sh
# ==============================================================================

echo "🧹 Starting cleanup..."

# Show current disk usage
echo ""
echo "📊 Current disk usage:"
du -sh downloads/ 2>/dev/null || echo "downloads/ folder not found"
du -sh cache/ 2>/dev/null || echo "cache/ folder not found"

# Clear downloads folder
if [ -d "downloads" ]; then
    echo ""
    echo "🗑️  Clearing downloads folder..."
    rm -rf downloads/*
    echo "✅ Downloads folder cleared"
else
    echo "⚠️  downloads/ folder not found"
fi

# Clear cache folder
if [ -d "cache" ]; then
    echo ""
    echo "🗑️  Clearing cache folder..."
    rm -rf cache/*
    echo "✅ Cache folder cleared"
else
    echo "⚠️  cache/ folder not found"
fi

# Show final disk usage
echo ""
echo "📊 Disk usage after cleanup:"
du -sh downloads/ 2>/dev/null || echo "downloads/ folder is empty"
du -sh cache/ 2>/dev/null || echo "cache/ folder is empty"

echo ""
echo "✅ Cleanup complete!"

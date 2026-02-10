#!/bin/bash
# Cleanup script to remove root-owned files in Web-Interface
# Run with: sudo bash cleanup_root_files.sh

cd "$(dirname "$0")"

echo "[*] Removing root-owned integration directory..."
rm -rf integration/

echo "[✓] Cleanup complete!"

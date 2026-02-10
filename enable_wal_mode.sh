#!/bin/bash
# Enable WAL mode on existing database for better concurrent access

DB_PATH="/home/zaher/Loki-IDS/Core/loki/database/loki_ids.db"

if [ ! -f "$DB_PATH" ]; then
    echo "[!] Database not found at: $DB_PATH"
    echo "[*] Please run init_database.sh first"
    exit 1
fi

echo "======================================================="
echo "  Enabling WAL Mode for Better Concurrency"
echo "======================================================="
echo ""
echo "[*] Database: $DB_PATH"
echo ""

# Enable WAL mode and optimize settings
sqlite3 "$DB_PATH" <<EOF
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA cache_size=-64000;
PRAGMA busy_timeout=30000;
PRAGMA wal_autocheckpoint=1000;

-- Verify settings
SELECT 'Journal Mode: ' || journal_mode FROM pragma_journal_mode;
SELECT 'Synchronous: ' || synchronous FROM pragma_synchronous;
SELECT 'Cache Size: ' || cache_size FROM pragma_cache_size;
SELECT 'Busy Timeout: ' || busy_timeout FROM pragma_busy_timeout;
EOF

echo ""
echo "[✓] WAL mode enabled successfully!"
echo ""
echo "Benefits:"
echo "  - Concurrent reads while writing"
echo "  - Better performance under load"
echo "  - No database locking during IDS detection"
echo ""
echo "Note: You'll see a new file 'loki_ids.db-wal' created."
echo "This is normal and is part of WAL mode."

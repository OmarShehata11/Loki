#!/bin/bash
# Check database health and performance

DB_PATH="Web-Interface/loki_ids.db"

echo "======================================================"
echo "  Database Health Check"
echo "======================================================"
echo ""

if [ ! -f "$DB_PATH" ]; then
    echo "✗ Database file not found: $DB_PATH"
    echo ""
    echo "Initialize it with:"
    echo "  cd Web-Interface"
    echo "  ../loki_env/bin/python3 init_database.py"
    exit 1
fi

echo "✓ Database file exists"
echo "  Size: $(du -h $DB_PATH | cut -f1)"
echo ""

# Check if database is accessible
echo "Checking database integrity..."
if sqlite3 "$DB_PATH" "PRAGMA integrity_check;" 2>&1 | grep -q "ok"; then
    echo "✓ Database integrity OK"
else
    echo "✗ Database integrity FAILED"
    sqlite3 "$DB_PATH" "PRAGMA integrity_check;"
    exit 1
fi
echo ""

# Check tables
echo "Checking tables..."
TABLES=$(sqlite3 "$DB_PATH" ".tables" 2>&1)
echo "  Tables: $TABLES"
echo ""

# Check alerts table
echo "Alerts table info:"
ALERT_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM alerts;" 2>&1)
echo "  Total alerts: $ALERT_COUNT"

# Check if there are too many alerts
if [ "$ALERT_COUNT" -gt 10000 ]; then
    echo "  ⚠ Large number of alerts ($ALERT_COUNT) - queries may be slow"
fi
echo ""

# Test a simple query with timing
echo "Testing query performance..."
START=$(date +%s%N)
sqlite3 "$DB_PATH" "SELECT * FROM alerts ORDER BY timestamp DESC LIMIT 10;" > /dev/null 2>&1
END=$(date +%s%N)
DURATION=$(( ($END - $START) / 1000000 ))
echo "  Query time: ${DURATION}ms"

if [ "$DURATION" -gt 1000 ]; then
    echo "  ⚠ Slow query (>1000ms) - missing indexes or database issues"
elif [ "$DURATION" -gt 5000 ]; then
    echo "  ✗ Very slow query (>5000ms) - serious performance issue"
else
    echo "  ✓ Query speed OK"
fi
echo ""

# Check indexes
echo "Checking indexes..."
INDEXES=$(sqlite3 "$DB_PATH" "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='alerts';" 2>&1)
if [ -z "$INDEXES" ]; then
    echo "  ⚠ No indexes on alerts table - this will cause slow queries!"
    echo ""
    echo "  Fix: Add indexes with:"
    echo "    sqlite3 $DB_PATH 'CREATE INDEX idx_alerts_timestamp ON alerts(timestamp DESC);'"
else
    echo "  Indexes:"
    echo "$INDEXES" | sed 's/^/    /'
fi
echo ""

# Check for database locks
echo "Checking for locks..."
if lsof "$DB_PATH" 2>/dev/null | grep -q "$DB_PATH"; then
    echo "  ⚠ Database file is currently open by:"
    lsof "$DB_PATH" | grep "$DB_PATH"
else
    echo "  ✓ No processes currently holding database locks"
fi
echo ""

echo "======================================================"
echo "  Recommendations"
echo "======================================================"

if [ "$ALERT_COUNT" -gt 10000 ]; then
    echo "• Consider cleaning old alerts:"
    echo "    sqlite3 $DB_PATH 'DELETE FROM alerts WHERE timestamp < datetime(\"now\", \"-7 days\");'"
fi

if [ -z "$INDEXES" ]; then
    echo "• Add performance indexes:"
    echo "    sqlite3 $DB_PATH 'CREATE INDEX idx_alerts_timestamp ON alerts(timestamp DESC);'"
    echo "    sqlite3 $DB_PATH 'CREATE INDEX idx_alerts_type ON alerts(type);'"
    echo "    sqlite3 $DB_PATH 'CREATE INDEX idx_alerts_src_ip ON alerts(src_ip);'"
fi

echo ""
echo "• If queries still hang, try:"
echo "    1. Stop the IDS temporarily"
echo "    2. Restart the web interface"
echo "    3. Check if queries work then"

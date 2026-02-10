#!/bin/bash

QUEUE_NUM_INPUT="100"
QUEUE_NUM_FORWARD="200"

echo "======================================================"
echo "    LOKI IDS: SAFELY FLUSHING NFQUEUE RULES"
echo "======================================================"

# 1. IDENTIFY AND DELETE NFQUEUE RULES
# NOTE: The -D rule must match EXACTLY what -I added, including --queue-bypass!
# If iptables_up.sh was run multiple times, there may be duplicate rules,
# so we loop until all copies are removed.

# Delete ALL NFQUEUE rules from the FORWARD chain
echo "[+] Deleting NFQUEUE rule(s) from FORWARD chain..."
while sudo iptables -D FORWARD -j NFQUEUE --queue-num $QUEUE_NUM_FORWARD --queue-bypass 2>/dev/null; do
    echo "    -> Removed one FORWARD rule"
done

# Delete ALL NFQUEUE rules from the INPUT chain
echo "[+] Deleting NFQUEUE rule(s) from INPUT chain..."
while sudo iptables -D INPUT -j NFQUEUE --queue-num $QUEUE_NUM_INPUT --queue-bypass 2>/dev/null; do
    echo "    -> Removed one INPUT rule"
done

# 2. VERIFICATION
echo "[+] Remaining NFQUEUE rules (should be empty):"
sudo iptables -L --line-numbers | grep NFQUEUE || echo "    (none - all clean!)"
echo "------------------------------------------------------"
echo "[+] IPTABLES cleanup complete."
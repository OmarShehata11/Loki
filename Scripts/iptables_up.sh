#!/bin/bash
QUEUE_NUM_INPUT="100" # for the input chain
QUEUE_NUM_FORWARD="200" # for the forward chain

echo "======================================================"
echo "    LOKI IDS: SETTING UP IPTABLES FOR ROUTING"
echo "======================================================"

# 1. ENABLE IP FORWARDING 
echo "[1/3] Enabling IP forwarding..."
sudo sysctl -w net.ipv4.ip_forward=1

# 2. ADD NFQUEUE RULES FIRST (so localhost rules can be inserted ABOVE them)
echo "[2/4] Inserting NFQUEUE rule to FORWARD chain with bypass..."
sudo iptables -I FORWARD -j NFQUEUE --queue-num $QUEUE_NUM_FORWARD --queue-bypass

echo "[2/4] Inserting NFQUEUE rule to INPUT chain (for traffic to the Pi itself) with bypass..."
sudo iptables -I INPUT -j NFQUEUE --queue-num $QUEUE_NUM_INPUT --queue-bypass

# 3. EXCLUDE ONLY PORT 8080 ON LOCALHOST (for dashboard)
echo "[3/4] Excluding localhost:8080 from inspection (for dashboard)..."
sudo iptables -I INPUT -i lo -p tcp --dport 8080 -j ACCEPT
sudo iptables -I OUTPUT -o lo -p tcp --sport 8080 -j ACCEPT

# 4. VERIFICATION
echo "[4/4] Rules set. Localhost excluded, other packets sent to Queue $QUEUE_NUM_FORWARD & $QUEUE_NUM_INPUT."

echo " *** Printing the iptables rules *** "

echo "------------------------------------------------------"
sudo iptables -L --line-numbers | grep NFQUEUE
echo "------------------------------------------------------"

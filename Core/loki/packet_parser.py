from scapy.all import TCP, UDP, IP
import datetime
import time

def scan_packet(packet):
    pkt = IP(packet.get_payload()) # get the IP layerrr.
    src_ip = pkt[IP].src
    dst_ip = pkt[IP].dst
    timestamp = packet.get_timestamp()
    if not timestamp:
        timestamp = time.time()

    packetID = packet.id
    payloadLen = packet.get_payload_len()
    dst_port = 0
    src_port = 0 # incase the packet has no TCP or UDP layer.
    port = ""
    tcp_flags = 0
    
    if pkt.haslayer(TCP):
        dst_port = pkt[TCP].dport
        src_port = pkt[TCP].sport
        tcp_flags = int(pkt[TCP].flags)
        is_syn = bool(tcp_flags & 0x02)
        is_ack = bool(tcp_flags & 0x10)
        is_rst = bool(tcp_flags & 0x04)
        is_fin = bool(tcp_flags & 0x01)

        port = "TCP"

    elif pkt.haslayer(UDP):
        dst_port = pkt[UDP].dport
        src_port = pkt[UDP].sport
        port = "UDP"

    # now calc the timestamp to be in a good format..
    finalTimeStamp = datetime.datetime.fromtimestamp(timestamp, datetime.UTC).strftime('%Y-%m-%d %H:%M:%S')

    Result = {
            "src_ip" : src_ip,
            "dst_ip" : dst_ip,
            "timestamp" : finalTimeStamp,
            "packetID" : packetID,
            "payloadLen" : payloadLen,
            "src_port" : src_port,
            "dst_port" : dst_port,
            "port" : port,
            "rawts" : timestamp,
            "tcp_flags": tcp_flags,
            }
    return Result # finaly returning the dictionary..
    

from netfilterqueue import NetfilterQueue
import threading
import time
from packet_parser import scan_packet
from detectore_engine import PortScanningDetector
from signature_engine import SignatureScanning
from scapy.all import IP, Raw
def process_packet(packet, IsInput, port_scanner):
    if IsInput:
        # now we are working in the input chain packet..
        packetInfo = scan_packet(packet)

        print(" *** Data Captured from INPUT chain ***")
        print()

        print(f" Source IP: {packetInfo.get("src_ip")}\n Dest Ip {packetInfo.get("dst_ip")}\n timestamp: {packetInfo.get("timestamp")}\n PacketID: {packetInfo.get("packetID")}\n Payload Len: {packetInfo.get("payloadLen")}\n Dst port: {packetInfo.get("dst_port")}\n src port: {packetInfo.get("src_port")}\n TCP or UDP: {packetInfo.get("port")}\n")
        
        #print("the data are: ")
        #print(packetInfo)

        # let's now try to analyze it with the port scanner:
        analyze_result = port_scanner.analyze_packet(packetInfo.get("src_ip"), packetInfo.get("rawts"), packetInfo.get("dst_port"))
        
        print(f"the analyze result is : {analyze_result}")

        # let's now test the signature based scanning..
        SigScanning = SignatureScanning()
        ip_layer = IP(packet.get_payload())
        if ip_layer.haslayer(Raw):
            print("packet has a Raw layer..")
            RawData = ip_layer[Raw].load
            RuleID, RuleDesc, Drop = SigScanning.CheckPacketPayload(RawData)
            print(f"Rule ID: {RuleID}, Rule Description: {RuleDesc}, Drop: {Drop}")
        else:
            print("the packet has no Raw Layer..***********")

        # then just accept it:
        packet.accept()

    else:
        # now working withing the forward chain
        # do the same as above, but I'm lazy to rewrite it, just print anything and move-on..
        print("*** Recieved Data from FORWARD chain ***")
        print()

        packet.accept()

def forward_agent():
    nfq = NetfilterQueue()
    port_scanner_object_forward = PortScanningDetector(10, 10)
    nfq.bind(200, lambda packet: process_packet(packet, False, port_scanner_object_forward))

    try:
        nfq.run()
    except Exception as e:
        print(f"[!] forward agent crashed: {e}")


def input_agent():
    nfq = NetfilterQueue()
    port_scanner_object_input = PortScanningDetector(10, 10)
    nfq.bind(100, lambda packet: process_packet(packet, True, port_scanner_object_input))
    
    try:
        nfq.run()
    
    except Exception as e:
        print(f"[!] Input agent crashed: {e}")


if __name__ == "__main__":
    print("========== Starting LOKI IDS ==========")
    print()
    
    # let's now create the 2 threads..
    input_thread= threading.Thread(target=input_agent, daemon=True)
    forward_thread= threading.Thread(target=forward_agent, daemon= True)


    # now let's start it:::
    input_thread.start()
    forward_thread.start()

    print(" ### The Threads have started ### ")

    # let's make sure the main thread exit peacefully::
    try:
        while True:
            time.sleep(1) # just sleep for one second, then intercept.
    except KeyboardInterrupt:
        print()
        print("[*] Recieved ^C, then Quitting...")
        print(" ========== Stopping LOKI IDS ==========")



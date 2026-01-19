from netfilterqueue import NetfilterQueue
import time
from collections import deque, defaultdict, Counter

# global var

class PortScanningDetector:
    def __init__(self, threshold, max_seconds):
        self.threshold = threshold
        self.port_scanning_log = defaultdict(deque)
        self.tcp_flood_log = defaultdict(deque)
        self.m_sec = max_seconds

        # the dictionary should have the time, and ip address, and port accessed.
        # the IP as a key, and list of (time, port access) as a value.

    def analyze_tcp(self, src_ip_add, dst_ip_add, timestamp, port_number):
        
        result = check_port_scanning(src_ip_add, dst_ip_add, timestamp, port_number)
        if result:
            return # whatever you wanna say about port scanning..
        result = check_tcp_flood(dst_ip_add, timestamp, port_number)
        if result:
            return # again whatever you feel about DoS/DDoS attack.


    def check_port_scanning(self, src_ip_add, dst_ip_add, timestamp, port_number):
    
        # first let's check the port scanning log:
        if ((src_ip_add, dst_ip_add) not in self.port_scanning_log):
            # now it's the simplest case, just add it to the dictionary:    
            self.port_scanning_log[(src_ip_add, dst_ip_add)].append((timestamp, port_number))

            # and that's it..
            return False
        else:
          
            # now it's the main thing, here we should compare and do the other logic.
            
            history = self.port_scanning_log.get((src_ip_add, dst_ip_add))

            # check if there's already an item there and the difference in time is not big..
            while history and ((timestamp - history[0][0]) > self.m_sec) :
                # just pop up that entry::
                history.popleft()
                
            # let's just append that item..
            history.append((timestamp, port_number))

            # now you have everything fresh, let's go to the next step::
            # 2. now the last and most important thing, let's check if the uniqueue port access is bigger than the threshold::
            active_ports = {item[1] for item in history}
            # I used a set to automatically add only unique items

            #now let's check if the list contains more than 10 items
            if len(active_ports) > self.threshold:
                return True

            return False

    def check_tcp_flood(self, dst_ip_add, timestamp, port_number):

        # first let's check the port scanning log:
        if ((dst_ip_add, port_number) not in self.tcp_flood_log):
            # now it's the simplest case, just add it to the dictionary:    
            self.tcp_flood_log[(dst_ip_add, port_number)].append(timestamp)

            # and that's it..
            return False

        else:
          
            # now it's the main thing, here we should compare and do the other logic.
            
            history = self.tcp_flood_log.get((dst_ip_add, port_number))

            # check if there's already an item there and the difference in time is not big..
            while history and ((timestamp - history[0]) > self.m_sec) :
                # just pop up that entry::
                history.popleft()
                
            # let's just append that item..
            history.append(timestamp)

            # now you have everything fresh, let's go to the next step::
            # 2. now the last and most important thing, let's check if the uniqueue port access is bigger than the threshold::
            #access_rate = len(history)
            # I used a set to automatically add only unique items

            #now let's check if the list contains more than 10 items
            if len(history) > self.threshold:
                return True

            return False


    def analyze_packet(self, src_ip_add, dst_ip_add, timestamp, port_number):
        if (src_ip_add, dst_ip_add) not in self.log:
            # now it's the simplest case, just add it to the dictionary:    
            self.log[(src_ip_add, dst_ip_add)].append((timestamp, port_number))

            # and that's it...
            return False

        else:
            # now it's the main thing, here we should compare and do the other logic.
            
            history = self.log.get((src_ip_add, dst_ip_add))

            # check if there's already an item there and the difference in time is not big..
            while history and ((timestamp - history[0][0]) > self.m_sec) :
                # just pop up that entry::
                history.popleft()
                
            # let's just append that item..
            history.append((timestamp, port_number))

            # now you have everything fresh, let's go to the next step::
            # 2. now the last and most important thing, let's check if the uniqueue port access is bigger than the threshold::
            active_ports = {item[1] for item in history}
            # I used a set to automatically add only unique items

            #now let's check if the list contains more than 10 items
            if len(active_ports) > self.threshold:
                return True

            return False




            



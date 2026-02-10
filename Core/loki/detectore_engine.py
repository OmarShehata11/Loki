from netfilterqueue import NetfilterQueue
import time
import math
from collections import deque, defaultdict, Counter

# global var

# ============================================================
# EWMA (Exponentially Weighted Moving Average) Rate Estimator
# ============================================================
# Instead of just counting packets in a window, EWMA gives us
# a smooth, real-time estimate of the packet rate (packets/sec).
# 
# How it works:
#   ewma_rate = alpha * instant_rate + (1 - alpha) * ewma_rate
#
# alpha close to 1.0 = reacts fast to bursts (but noisy)
# alpha close to 0.0 = smooth but slow to react
#
# We use this ON TOP of the existing sliding window:
#   - Sliding window: "did we see X packets in Y seconds?" (count-based)
#   - EWMA: "what is the current packets-per-second rate?" (rate-based)
#   - Both must agree before we trigger an alert.
# ============================================================

class EWMARateEstimator:
    """
    Tracks packet rate using EWMA (Exponentially Weighted Moving Average).
    Gives a smooth packets-per-second estimate that reacts to bursts.
    """
    def __init__(self, alpha=0.3):
        """
        Args:
            alpha: Smoothing factor (0.0 to 1.0)
                   Higher = more reactive to bursts
                   Lower  = smoother, less false positives
        """
        self.alpha = alpha
        self.ewma_rate = 0.0        # current smoothed rate (packets/sec)
        self.last_timestamp = None   # timestamp of the last packet we saw

    def update(self, timestamp):
        """
        Call this for every packet. Updates the EWMA rate estimate.
        
        Args:
            timestamp: current packet timestamp (float, seconds)
        
        Returns:
            float: the updated EWMA rate (packets per second)
        """
        if self.last_timestamp is None:
            # first packet ever, can't calculate a rate yet
            self.last_timestamp = timestamp
            self.ewma_rate = 0.0
            return self.ewma_rate

        dt = timestamp - self.last_timestamp
        self.last_timestamp = timestamp

        if dt <= 0:
            # packets arrived at the exact same time (or clock glitch)
            # treat as very high instant rate
            instant_rate = 10000.0
        else:
            # instant rate = 1 packet / dt seconds = 1/dt packets per second
            instant_rate = 1.0 / dt

        # the EWMA formula:
        # new_rate = alpha * instant_rate + (1 - alpha) * old_rate
        self.ewma_rate = self.alpha * instant_rate + (1.0 - self.alpha) * self.ewma_rate

        return self.ewma_rate

    def get_rate(self):
        """Get the current EWMA rate without updating."""
        return self.ewma_rate

    def reset(self):
        """Reset the estimator (e.g., after attack ends)."""
        self.ewma_rate = 0.0
        self.last_timestamp = None


class PortScanningDetector:
    def __init__(self, threshold, max_seconds):
        self.threshold = threshold
        self.port_scanning_log = defaultdict(deque)

        self.tcp_flood_log = defaultdict(deque)
        self.udp_flood_log = defaultdict(deque)
        self.icmp_flood_log = defaultdict(deque)
        
        self.m_sec = max_seconds

        # values for testing attacks..
        self.port_scanning_window = 5
        self.port_scanning_threshold = 20

        self.tcp_flood_window = 2
        self.tcp_flood_threshold = 200
        self.tcp_ack_ratio = 0.2

        self.udp_flood_window = 2
        self.udp_flood_threshold = 300

        self.icmp_flood_window = 2
        self.icmp_flood_threshold = 100

        # ===== EWMA Rate Estimators =====
        # One estimator per (flow key), stored in defaultdicts
        # alpha=0.3 is a good balance between reactivity and smoothness
        self.tcp_flood_ewma = defaultdict(lambda: EWMARateEstimator(alpha=0.3))
        self.udp_flood_ewma = defaultdict(lambda: EWMARateEstimator(alpha=0.3))
        self.icmp_flood_ewma = defaultdict(lambda: EWMARateEstimator(alpha=0.3))

        # EWMA rate thresholds (packets per second)
        # These work together with the sliding window thresholds above.
        # An alert fires only when BOTH the sliding window count AND 
        # the EWMA rate exceed their respective thresholds.
        self.tcp_flood_ewma_threshold = 100.0    # pps
        self.udp_flood_ewma_threshold = 150.0    # pps
        self.icmp_flood_ewma_threshold = 50.0    # pps

    def analyze_tcp(self, src_ip_add, dst_ip_add, timestamp, port_number):
        # return types: (just again for test, maybe optimized later..)
        # 0 => no attack detected
        # 1 => port scanning
        # 2 => tcp flood
        result = self.check_port_scanning(src_ip_add, dst_ip_add, timestamp, port_number)
        if result:
            return 1 # whatever you wanna say about port scanning..
        result = self.check_tcp_flood(dst_ip_add, timestamp, port_number)
        if result:
            return 2 # again whatever you feel about DoS/DDoS attack.
        return 0

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
            while history and ((timestamp - history[0][0]) > self.port_scanning_window) :
                # just pop up that entry::
                history.popleft()
                
            # let's just append that item..
            history.append((timestamp, port_number))

            # now you have everything fresh, let's go to the next step::
            # 2. now the last and most important thing, let's check if the uniqueue port access is bigger than the threshold::
            active_ports = {item[1] for item in history}
            # I used a set to automatically add only unique items

            #now let's check if the list contains more than 10 items
            if len(active_ports) > self.port_scanning_threshold:
                return True

            return False

    def check_tcp_flood(self, dst_ip_add, timestamp, port_number):

        flow_key = (dst_ip_add, port_number)

        # Update EWMA rate estimator for this flow
        ewma_rate = self.tcp_flood_ewma[flow_key].update(timestamp)

        # first let's check the port scanning log:
        if (flow_key not in self.tcp_flood_log):
            # now it's the simplest case, just add it to the dictionary:    
            self.tcp_flood_log[flow_key].append(timestamp)

            # and that's it..
            return False

        else:
          
            # now it's the main thing, here we should compare and do the other logic.
            
            history = self.tcp_flood_log.get(flow_key)

            # check if there's already an item there and the difference in time is not big..
            while history and ((timestamp - history[0]) > self.tcp_flood_window) :
                # just pop up that entry::
                history.popleft()
                
            # let's just append that item..
            history.append(timestamp)

            # now you have everything fresh, let's go to the next step::
            # 2. now the last and most important thing, let's check if the uniqueue port access is bigger than the threshold::
            #access_rate = len(history)
            # I used a set to automatically add only unique items

            #now let's check if the list contains more than 10 items
            # DUAL CHECK: sliding window count AND EWMA rate must both exceed thresholds
            if len(history) > self.tcp_flood_threshold and ewma_rate > self.tcp_flood_ewma_threshold:
                return True

            return False

    def analyze_udp(self, dst_ip_add, timestamp, port_number):

        flow_key = (dst_ip_add, port_number)

        # Update EWMA rate estimator for this flow
        ewma_rate = self.udp_flood_ewma[flow_key].update(timestamp)

        # first let's check the port scanning log:
        if (flow_key not in self.udp_flood_log):
            # now it's the simplest case, just add it to the dictionary:    
            self.udp_flood_log[flow_key].append(timestamp)

            # and that's it..
            return False

        else:
          
            # now it's the main thing, here we should compare and do the other logic.
            
            history = self.udp_flood_log.get(flow_key)

            # check if there's already an item there and the difference in time is not big..
            while history and ((timestamp - history[0]) > self.udp_flood_window) :
                # just pop up that entry::
                history.popleft()
                
            # let's just append that item..
            history.append(timestamp)

            # now you have everything fresh, let's go to the next step::
            # 2. now the last and most important thing, let's check if the uniqueue port access is bigger than the threshold::
            #access_rate = len(history)
            # I used a set to automatically add only unique items

            #now let's check if the list contains more than 10 items
            # DUAL CHECK: sliding window count AND EWMA rate must both exceed thresholds
            if len(history) > self.udp_flood_threshold and ewma_rate > self.udp_flood_ewma_threshold:
                return True

            return False

    def analyze_icmp(self, dst_ip_add, timestamp):

        flow_key = dst_ip_add

        # Update EWMA rate estimator for this flow
        ewma_rate = self.icmp_flood_ewma[flow_key].update(timestamp)

        # first let's check the port scanning log:
        if dst_ip_add not in self.icmp_flood_log:
            # now it's the simplest case, just add it to the dictionary:    
            self.icmp_flood_log[dst_ip_add].append(timestamp)

            # and that's it..
            return False

        else:
          
            # now it's the main thing, here we should compare and do the other logic.
            
            history = self.icmp_flood_log.get(dst_ip_add)

            # check if there's already an item there and the difference in time is not big..
            while history and ((timestamp - history[0]) > self.icmp_flood_window) :
                # just pop up that entry::
                history.popleft()
                
            # let's just append that item..
            history.append(timestamp)

            # now you have everything fresh, let's go to the next step::
            # 2. now the last and most important thing, let's check if the uniqueue port access is bigger than the threshold::
            # access_rate = len(history)
            # I used a set to automatically add only unique items

            #now let's check if the list contains more than 10 items
            # DUAL CHECK: sliding window count AND EWMA rate must both exceed thresholds
            if len(history) > self.icmp_flood_threshold and ewma_rate > self.icmp_flood_ewma_threshold:
                return True

            return False

    def get_ewma_stats(self):
        """
        Get current EWMA rate stats for all tracked flows.
        Useful for debugging and the dashboard.
        """
        stats = {
            'tcp_flows': {},
            'udp_flows': {},
            'icmp_flows': {}
        }
        for key, estimator in self.tcp_flood_ewma.items():
            stats['tcp_flows'][str(key)] = round(estimator.get_rate(), 2)
        for key, estimator in self.udp_flood_ewma.items():
            stats['udp_flows'][str(key)] = round(estimator.get_rate(), 2)
        for key, estimator in self.icmp_flood_ewma.items():
            stats['icmp_flows'][str(key)] = round(estimator.get_rate(), 2)
        return stats


    # def analyze_packet(self, src_ip_add, dst_ip_add, timestamp, port_number):
    #     if (src_ip_add, dst_ip_add) not in self.log:
    #         # now it's the simplest case, just add it to the dictionary:    
    #         self.log[(src_ip_add, dst_ip_add)].append((timestamp, port_number))

    #         # and that's it...
    #         return False

    #     else:
    #         # now it's the main thing, here we should compare and do the other logic.
            
    #         history = self.log.get((src_ip_add, dst_ip_add))

    #         # check if there's already an item there and the difference in time is not big..
    #         while history and ((timestamp - history[0][0]) > self.m_sec) :
    #             # just pop up that entry::
    #             history.popleft()
                
    #         # let's just append that item..
    #         history.append((timestamp, port_number))

    #         # now you have everything fresh, let's go to the next step::
    #         # 2. now the last and most important thing, let's check if the uniqueue port access is bigger than the threshold::
    #         active_ports = {item[1] for item in history}
    #         # I used a set to automatically add only unique items

    #         #now let's check if the list contains more than 10 items
    #         if len(active_ports) > self.threshold:
    #             return True

    #         return False
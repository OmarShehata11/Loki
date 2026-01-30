# Signature detection engine
import os
import sys

# Add Web-Interface to path to import database modules
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
web_interface_path = os.path.join(project_root, "Web-Interface")
if web_interface_path not in sys.path:
    sys.path.insert(0, web_interface_path)

# Import db_integration from same directory
from db_integration import db_integration


class SignatureScanning:
    """
    Database-based signature engine.
    
    This class loads signatures from the database.
    """
    def __init__(self):
        # the dict will be : RULE_ID -> (description, data, action, rule id)
        self.rule = {"TEST_RULE" : ("test malicious rule", b"ATTACK_TEST", True, "ID1 TEST_RULE")} # just for testing..
        self.rules = []
        self.load_rules()

    def load_rules(self):
        """
        Load rules from database.
        Only loads enabled signatures.
        """
        try:
            # Get enabled signatures from database
            signatures = db_integration.get_signatures(enabled_only=True)
            
            # Clear existing rules
            self.rules = []
            
            # Convert database signatures to rule format
            for sig in signatures:
                rule = {
                    'name': sig['name'],
                    'pattern': sig['pattern'],
                    'pattern_bytes': sig['pattern'].encode('utf-8'),
                    'action': sig['action'],
                    'description': sig.get('description', '')
                }
                self.rules.append(rule)

            print(f"[*] Loading of rules from database is done.")
            print(f"[*] Number of rules loaded is {len(self.rules)}.")

        except Exception as e:
            print(f"[!] ERROR while loading signatures from database: {e}")
            self.rules = []  # Ensure rules list is empty on error
    
    def reload_rules(self):
        """
        Reload rules from the database.
        """
        print("[*] Reloading signatures from database...")
        self.load_rules()
        print(f"[*] Reloaded {len(self.rules)} signatures")
        return len(self.rules)

    def CheckPacketPayload(self, payload):
        # we should get the payload itself like pkt[Raw].load
        # it won't matter if it's tcp or udp
        Rule = self.rule.get("TEST_RULE")
        try:
            for rule in self.rules:
                if rule.get('pattern_bytes') in payload:
                    return rule.get('name'), rule.get('pattern'), rule.get('action')
                    # note that if the packet matches many ruless, then now this code will return
                    # only the first rule that matches, keep in mind that we need to modify it.
            
        except Exception as e:
            print(f"[-] ERROR while checking the packet : {e}")
            
        return 0,0,0

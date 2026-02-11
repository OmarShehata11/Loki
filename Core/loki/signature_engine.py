# Signature detection engine
# Now uses API integration instead of direct database access

# Import API integration client (sends HTTP requests to Web Interface)
from db_integration import db_integration


class SignatureScanning:
    """
    API-based signature engine.

    This class loads signatures from the Web Interface API.
    """
    def __init__(self):
        # the dict will be : RULE_ID -> (description, data, action, rule id)
        self.rule = {"TEST_RULE" : ("test malicious rule", b"ATTACK_TEST", True, "ID1 TEST_RULE")} # just for testing..
        self.rules = []
        self.load_rules()

    def load_rules(self):
        """
        Load rules from Web Interface API.
        Only loads enabled signatures.
        """
        try:
            # Get enabled signatures from API
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

            print(f"[*] Loading of rules from API is done.")
            print(f"[*] Number of rules loaded is {len(self.rules)}.")

        except Exception as e:
            print(f"[!] ERROR while loading signatures from API: {e}")
            self.rules = []  # Ensure rules list is empty on error
    
    def reload_rules(self):
        """
        Reload rules from the Web Interface API.
        """
        print("[*] Reloading signatures from API...")
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

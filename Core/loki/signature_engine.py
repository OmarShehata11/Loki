# nowwww let's detect the content itself..
import yaml


class SignatureScanning:
    def __init__(self, yaml_file_path="../../Configs/test_yaml_file.yaml"):
        # the dict will be : RULE_ID -> (description, data, action, rule id)
        self.rule = {"TEST_RULE" : ("test malicious rule", b"ATTACK_TEST", True, "ID1 TEST_RULE")} # just for testing..
        self.rules = []
        self.load_rules(yaml_file_path)

    def load_rules(self, file_path):
        try:
            with open(file_path, 'r') as f:
                all_rules = yaml.safe_load(f)
                #print("opening the file path is done.")

            # now we have all the rules organized as a dictionaries..
            # let's add them to the rules variable
            
            for block in all_rules.get('signatures'):
               # print(f"current block is : {block}")
                block['pattern_bytes'] = block['pattern'].encode('utf-8')
                self.rules.append(block)

            print(f"[*] loading of the rules from {file_path} is done.")
            print(f"[*] number of rules loaded is {len(self.rules)}.")
           # print(f"the rules are : \n{self.rules}")
           # print("================***==============")

        except Exception as e:
            print(f"[!]ERROR while loading the yaml file: {e}")

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

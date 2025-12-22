# nowwww let's detect the content itself..



class SignatureScanning:
    def __init__(self):
        # the dict will be : RULE_ID -> (description, data, action, rule id)
        self.rule = {"TEST_RULE" : ("test malicious rule", b"ATTACK_TEST", True, "ID1 TEST_RULE")} # just for testing..


    def CheckPacketPayload(self, payload):
        # we should get the payload itself like pkt[Raw].load
        # it won't matter if it's tcp or udp
        Rule = self.rule.get("TEST_RULE")

        mal_string = Rule[1]

        if mal_string in payload:
            return Rule[-1], Rule[0], Rule[2]

        return 0,0,0

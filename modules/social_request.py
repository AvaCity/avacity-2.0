from modules.base_module import Module

class_name = "SocialRequest"


class SocialRequest(Module):
    prefix = "srqst"

    def __init__(self, server):
        self.server = server
        self.commands = {"gtit": self.get_item,
                         "gtrq": self.get_requests}

    def get_item(self, msg, client):
        client.send(["srqst.gtit", {"sreqs": [], "sress": [], "mct": 0}])

    def get_requests(self, msg, client):
        client.send(["srqst.gtrq", {"rqlst": {"shwdt": 0, "rsprlst": {},
                                              "lapt": {}, "rlst": {}}}])

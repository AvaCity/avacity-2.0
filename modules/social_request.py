from modules.base_module import Module

class_name = "SocialRequest"


class SocialRequest(Module):
    prefix = "srqst"

    def __init__(self, server):
        self.server = server
        self.commands = {"gtit": self.get_item}

    def get_item(self, msg, client):
        client.send(["srqst.gtit", {"sreqs": [], "sress": [], "mct": 0}])

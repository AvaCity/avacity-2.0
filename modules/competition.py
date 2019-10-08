from modules.base_module import Module

class_name = "Competition"

class Competition(Module):
    prefix = "ctmr"

    def __init__(self, server):
        self.server = server
        self.commands = {"get": self.get_top}

    def get_top(self, msg, client):
        client.send(["ctmr.get", {"tu": {"snowboardRating": []}}])

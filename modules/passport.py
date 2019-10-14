from modules.base_module import Module
from const import tr

class_name = "Passport"

class Passport(Module):
    prefix = "psp"

    def __init__(self, server):
        self.server = server
        self.commands = {"sttrph": self.set_trophy}

    def set_trophy(self, msg, client):
        if msg[2]["trid"] not in tr:
            self.server.redis.delete(f"uid:{client.uid}:trid")
            trid = None
        else:
            trid = msg[2]["trid"]
            self.server.redis.set(f"uid:{client.uid}:trid", trid)
        client.send(["psp.sttrph", {"trid": trid}])

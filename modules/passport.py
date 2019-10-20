from modules.base_module import Module
from const import tr

class_name = "Passport"

class Passport(Module):
    prefix = "psp"

    def __init__(self, server):
        self.server = server
        self.commands = {"sttrph": self.set_trophy, "psp": self.passport}

    def set_trophy(self, msg, client):
        if msg[2]["trid"] not in tr:
            self.server.redis.delete(f"uid:{client.uid}:trid")
            trid = None
        else:
            trid = msg[2]["trid"]
            self.server.redis.set(f"uid:{client.uid}:trid", trid)
        client.send(["psp.sttrph", {"trid": trid}])

    def passport(self, msg, client):
        ac = {}
        for item in self.server.achievements:
            ac[item] = {"p": 0, "nWct": 0, "l": 3, "aId": item}
        tr = {}
        for item in self.server.trophies:
            tr[item] = {"trrt": 0, "trcd": 0, "trid": item}
        client.send(["psp.psp", {"psp": {"uid": msg[2]["uid"],
                                         "ach": {"ac": ac, "tr": tr},
                                         "rel": {}}}])

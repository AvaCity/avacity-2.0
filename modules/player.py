from modules.base_module import Module
from modules.location import gen_plr

class_name = "Player"

class Player(Module):
    prefix = "pl"

    def __init__(self, server):
        self.server = server
        self.commands = {"gid": self.players_by_id}

    def players_by_id(self, msg, client):
        players = []
        for uid in msg[2]["uids"]:
            players.append(gen_plr(uid, self.server))
        client.send(["pl.get", {"plrs": players, "clid": msg[2]["clid"]}])

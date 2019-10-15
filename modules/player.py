from modules.base_module import Module
from modules.location import gen_plr

class_name = "Player"

class Player(Module):
    prefix = "pl"

    def __init__(self, server):
        self.server = server
        self.commands = {"gid": self.players_by_id, "flw": self.follow}

    def players_by_id(self, msg, client):
        players = []
        for uid in msg[2]["uids"]:
            plr = gen_plr(uid, self.server)
            if not plr:
                continue
            players.append(plr)
        client.send(["pl.get", {"plrs": players, "clid": msg[2]["clid"]}])

    def follow(self, msg, client):
        user = None
        for tmp in self.server.online.copy():
            if tmp.uid == msg[2]["uid"]:
                user = tmp
                break
        if not user:
            scs = "userOffline"
            locinfo = None
        else:
            scs = "success"
            locinfo = {"st": 0, "s": "127.0.0.1", "at": None, "d": 0, "x": -1.0,
                       "y": -1.0, "shlc": True, "pl": "", "l": tmp.room}
        client.send(["pl.flw", {"scs": scs, "locinfo": locinfo}])

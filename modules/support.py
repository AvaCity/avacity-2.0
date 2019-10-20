from modules.base_module import Module
from modules.location import refresh_avatar

icon = "https://raw.githubusercontent.com/AvaCity/avacity-2.0/master/" \
       "readme/star.png"
class_name = "Support"


class Support(Module):
    prefix = "spt"

    def __init__(self, server):
        self.server = server
        self.commands = {"init": self.init, "gscnl": self.get_social_channels,
                         "rsnm": self.reset_avatar_name,
                         "lmdac": self.load_moderator_actions}

    def init(self, msg, client):
        client.send(["spt.init", {"a": False}])

    def get_social_channels(self, msg, client):
        channels = []
        channels.append({"act": True, "prt": 1, "id": 1, "stid": "github",
                         "dsctn": f"Поставьте звёздочку ;(\n"
                         f"Ревизия: {self.server.revision}",
                         "ttl": "GitHub", "icnurl": icon,
                         "lnk": "https://github.com/AvaCity/avacity-2.0"})
        client.send(["spt.gscnl", {"scls": channels}])

    def reset_avatar_name(self, msg, client):
        priveleges = self.server.modules["cp"].priveleges
        user_data = self.server.get_user_data(client.uid)
        if user_data["role"] < priveleges["RENAME_AVATAR"]:
            return
        uid = str(msg[2]["uid"])
        name = msg[2]["n"]
        if not self.server.redis.lindex(f"uid:{uid}:appearance", 0):
            return
        self.server.redis.lset(f"uid:{uid}:appearance", 0, name)
        for tmp in self.server.online.copy():
            if tmp.uid == uid:
                refresh_avatar(tmp, self.server)
                break

    def load_moderator_actions(self, msg, client):
        client.send(["spt.lmdac", {"uid": msg[2]["uid"], "acts": []}])

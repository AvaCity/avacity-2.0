from modules.base_module import Module

icon = "https://raw.githubusercontent.com/AvaCity/avacity-2.0/master/" \
       "readme/star.png"
class_name = "Support"


class Support(Module):
    prefix = "spt"

    def __init__(self, server):
        self.server = server
        self.commands = {"init": self.init, "gscnl": self.get_social_channels}

    def init(self, msg, client):
        client.send(["spt.init", {"a": False}])

    def get_social_channels(self, msg, client):
        channels = []
        channels.append({"act": True, "prt": 1, "id": 1, "stid": "github",
                         "dsctn": "Поставьте звёздочку ;(", "ttl": "GitHub",
                         "icnurl": icon,
                         "lnk": "https://github.com/AvaCity/avacity-2.0"})
        client.send(["spt.gscnl", {"scls": channels}])

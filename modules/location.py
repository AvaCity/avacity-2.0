import logging
from modules.base_module import Module
import common


class Location(Module):
    def __init__(self, server):
        self.server = server
        self.commands = {"r": self.room}

    def room(self, msg, client):
        subcommand = msg[1].split(".")[2]
        if subcommand in ["u", "m", "k", "sa", "sl", "bd", "lks", "hs", "sex"]:
            msg.pop(0)
            if subcommand == "u":
                client.position = (msg[1]["x"], msg[1]["y"])
                client.direction = msg[1]["d"]
                if "at" in msg[1]:
                    client.action_tag = msg[1]["at"]
                else:
                    client.action_tag = ""
                client.state = msg[1]["st"]
            elif subcommand == "sa":
                if "pntHlRd" in msg[1]["at"]:
                    return
            for tmp in self.server.online:
                if tmp.uid == client.uid or tmp.room != client.room:
                    continue
                tmp.send(msg)
        elif subcommand == "ra":
            refresh_avatar(client, self.server)
        else:
            logging.warning(f"Command {msg[1]} not found")


def gen_plr(client, server):
    user_data = server.get_user_data(client.uid)
    apprnc = server.get_appearance(client.uid)
    clths = server.get_clothes(client.uid, type_=2)
    plr = {"uid": client.uid, "apprnc": apprnc, "clths": clths,
           "mbm": {"ac": None, "sk": "blackMobileSkin"},
           "usrinf": {"rl": user_data["role"]}}
    plr["locinfo"] = {"st": 0, "s": "127.0.0.1", "at": client.action_tag,
                      "d": client.dimension, "x": client.position[0],
                      "y": client.position[1], "shlc": True, "pl": "",
                      "l": client.room}
    plr["ci"] = {"exp": user_data["exp"], "crt": user_data["crt"],
                 "hrt": user_data["hrt"], "fexp": 0, "gdc": 0, "lgt": 0,
                 "vip": True, "vexp": 1965298000, "vsexp": 1965298000,
                 "vsact": True, "vret": 0, "vfgc": 0, "ceid": 0, "cmid": 0,
                 "dr": True, "spp": 0, "tts": None, "eml": None, "ys": 0,
                 "ysct": 0, "fak": None, "shcr": True, "gtrfrd": 0,
                 "strfrd": 0, "rtrtm": 0, "kyktid": None, "actrt": 0,
                 "compid": 0, "actrp": 0, "actrd": 0, "shousd": False,
                 "rpt": 0, "as": None, "lvt": user_data["lvt"],
                 "lrnt": 0, "lwts": 0, "skid": None, "skrt": 0, "bcld": 0,
                 "trid": user_data["trid"], "trcd": 0, "sbid": None,
                 "sbrt": 0, "plcmt": {}, "pamns": {"amn": []}, "crst": 0}
    return plr


def refresh_avatar(client, server):
    plr = gen_plr(client, server)
    prefix = common.get_prefix(client.room)
    for tmp in server.online.copy():
        if tmp.room != client.room:
            continue
        tmp.send([f"{prefix}.r.ra", {"plr": plr}])

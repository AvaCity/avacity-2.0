import logging
from modules.base_module import Module
from modules.location import refresh_avatar
from inventory import Inventory
import const

class_name = "Avatar"


class Avatar(Module):
    prefix = "a"

    def __init__(self, server):
        self.server = server
        self.commands = {"apprnc": self.appearance, "clths": self.clothes}

    def appearance(self, msg, client):
        subcommand = msg[1].split(".")[2]
        if subcommand == "rnn":
            if len(msg[2]["unm"]) > const.MAX_NAME_LEN:
                return
            self.server.redis.lset(f"uid:{client.uid}:appearance",
                                   0, msg[2]["unm"])
            user_data = self.server.get_user_data(client.uid)
            client.send(["a.apprnc.rnn", {"res": {"slvr": user_data["slvr"],
                                                  "enrg": user_data["enrg"],
                                                  "emd": user_data["emd"],
                                                  "gld": user_data["gld"]},
                                          "unm": msg[2]["unm"]}])
        elif subcommand == "save":
            apprnc = msg[2]["apprnc"]
            current_apprnc = self.server.get_appearance(client.uid)
            if not current_apprnc:
                self.update_appearance(apprnc, client)
                self.server.inv[client.uid] = Inventory(self.server,
                                                        client.uid)
                if apprnc["g"] == 1:
                    weared = ["boyShoes8", "boyPants10", "boyShirt14"]
                    available = ["boyUnderdress1"]
                else:
                    weared = ["girlShoes14", "girlPants9", "girlShirt12"]
                    available = ["girlUnderdress1", "girlUnderdress2"]
                for item in weared+available:
                    self.server.inv[client.uid].add_item(item, "cls")
                for item in weared:
                    self.server.inv[client.uid].change_wearing(item, True)
                for item in const.room_items:
                    self.server.modules["frn"].add_item(item, "livingroom",
                                                        client.uid)
            else:
                if apprnc["g"] != current_apprnc["g"]:
                    logging.error("gender doesn't match!")
                    return
                self.update_appearance(apprnc, client)
            client.send(["a.apprnc.save",
                         {"apprnc": self.server.get_appearance(client.uid)}])

    def clothes(self, msg, client):
        subcommand = msg[1].split(".")[2]
        if subcommand == "wear":
            self.wear_cloth(msg[2]["clths"], client)
        elif subcommand == "buy":
            self.buy_cloth(msg[2]["tpid"], client)
        elif subcommand == "bcc":
            self.buy_colored_clothes(msg[2]["clths"], client)
        else:
            logging.warning(f"Command {msg[1]} not found")

    def wear_cloth(self, clths, client):
        items = self.server.redis.smembers(f"uid:{client.uid}:items")
        for cloth in clths:
            if cloth["clid"]:
                tmp = f"{cloth['tpid']}_{cloth['clid']}"
            else:
                tmp = cloth["tpid"]
            if tmp not in items:
                return
        wearing = self.server.redis.smembers(f"uid:{client.uid}:wearing")
        for cloth in wearing:
            self.server.inv[client.uid].change_wearing(cloth, False)
        for cloth in clths:
            if cloth["clid"]:
                tmp = f"{cloth['tpid']}_{cloth['clid']}"
            else:
                tmp = cloth["tpid"]
            self.server.inv[client.uid].change_wearing(tmp, True)
        inv = self.server.inv[client.uid].get()
        clths = self.server.get_clothes(client.uid, type_=2)
        ccltn = self.server.get_clothes(client.uid, type_=3)
        client.send(["a.clths.wear", {"inv": inv, "clths": clths,
                                      "ccltn": ccltn, "cn": "",
                                      "ctp": "casual"}])
        refresh_avatar(client, self.server)

    def buy_cloth(self, cloth, client):
        items = self.server.redis.smembers(f"uid:{client.uid}:items")
        if cloth in items:
            return
        if self.server.get_appearance(client.uid)["g"] == 1:
            gender = "boy"
        else:
            gender = "girl"
        category = self.get_category(cloth, gender)
        if not category:
            return
        attrs = self.server.clothes[gender][category][cloth]
        user_data = self.server.get_user_data(client.uid)
        if user_data["gld"] < attrs["gold"] or \
           user_data["slvr"] < attrs["silver"]:
            return
        self.server.redis.set(f"uid:{client.uid}:gld",
                              user_data["gld"] - attrs["gold"])
        self.server.redis.set(f"uid:{client.uid}:slvr",
                              user_data["slvr"] - attrs["silver"])
        self.server.redis.set(f"uid:{client.uid}:crt",
                              user_data["crt"] + attrs["rating"])
        self.server.inv[client.uid].add_item(cloth, "cls")
        self.server.inv[client.uid].change_wearing(cloth, True)
        inv = self.server.inv[client.uid].get()
        clths = self.server.get_clothes(client.uid, type_=2)
        ccltn = self.server.get_clothes(client.uid, type_=1)
        ccltn = ccltn["ccltns"]["casual"]
        user_data = self.server.get_user_data(client.uid)
        client.send(["a.clths.buy", {"inv": inv,
                                     "res": {"slvr": user_data["slvr"],
                                             "enrg": user_data["enrg"],
                                             "emd": user_data["emd"],
                                             "gld": user_data["gld"]},
                                     "clths": clths, "ccltn": ccltn,
                                     "crt": user_data["crt"]}])

    def buy_colored_clothes(self, clothes, client):
        items = self.server.redis.smembers(f"uid:{client.uid}:items")
        if self.server.get_appearance(client.uid)["g"] == 1:
            gender = "boy"
        else:
            gender = "girl"
        gold = 0
        silver = 0
        rating = 0
        to_buy = []
        for item in clothes:
            cloth = item["tpid"]
            clid = item["clid"]
            if f"{cloth}_{clid}" in items or cloth in items:
                continue
            for category in self.server.clothes[gender]:
                for item in self.server.clothes[gender][category]:
                    if item == cloth:
                        tmp = self.server.clothes[gender][category][item]
                        gold += tmp["gold"]
                        silver += tmp["silver"]
                        rating += tmp["rating"]
                        if clid:
                            to_buy.append(f"{cloth}_{clid}")
                        else:
                            to_buy.append(cloth)
                        break
        user_data = self.server.get_user_data(client.uid)
        if not to_buy or user_data["gld"] < gold or user_data["slvr"] < silver:
            return
        pipe = self.server.redis.pipeline()
        pipe.set(f"uid:{client.uid}:gld", user_data["gld"] - gold)
        pipe.set(f"uid:{client.uid}:slvr", user_data["slvr"] - silver)
        pipe.set(f"uid:{client.uid}:crt", user_data["crt"] + rating)
        pipe.execute()
        for cloth in to_buy:
            self.server.inv[client.uid].add_item(cloth, "cls")
            self.server.inv[client.uid].change_wearing(cloth, True)
        user_data = self.server.get_user_data(client.uid)
        inv = self.server.inv[client.uid].get()
        clths = self.server.get_clothes(client.uid, type_=2)
        ccltn = self.server.get_clothes(client.uid, type_=1)
        ccltn = ccltn["ccltns"]["casual"]
        client.send(["a.clths.bcc", {"inv": inv,
                                     "res": {"gld": user_data["gld"],
                                             "slvr": user_data["slvr"],
                                             "emd": user_data["emd"],
                                             "enrg": user_data["enrg"]},
                                     "clths": clths, "ccltn": ccltn,
                                     "crt": user_data["crt"]}])

    def update_appearance(self, apprnc, client):
        self.server.redis.delete(f"uid:{client.uid}:appearance")
        self.server.redis.rpush(f"uid:{client.uid}:appearance", apprnc["n"],
                                apprnc["nct"], apprnc["g"], apprnc["sc"],
                                apprnc["ht"], apprnc["hc"], apprnc["brt"],
                                apprnc["brc"], apprnc["et"], apprnc["ec"],
                                apprnc["fft"], apprnc["fat"], apprnc["fac"],
                                apprnc["ss"], apprnc["ssc"], apprnc["mt"],
                                apprnc["mc"], apprnc["sh"], apprnc["shc"],
                                apprnc["rg"], apprnc["rc"], apprnc["pt"],
                                apprnc["pc"], apprnc["bt"], apprnc["bc"])

    def update_crt(self, uid):
        clothes = []
        for tmp in self.server.redis.smembers(f"uid:{uid}:items"):
            if self.server.redis.lindex(f"uid:{uid}:items:{tmp}", 0) == "cls":
                if "_" in clothes:
                    clothes.append(tmp.split("_")[0])
                else:
                    clothes.append(tmp)
        appearance = self.server.get_appearance(uid)
        if not appearance:
            return 0
        gender = "boy" if appearance["g"] == 1 else "girl"
        crt = 0
        for cloth in clothes:
            for _category in self.clothes[gender]:
                for item in self.clothes[gender][_category]:
                    if item == cloth:
                        crt += self.clothes[gender][_category][cloth]["rating"]
                        break
        self.server.redis.set(f"uid:{uid}:crt", crt)
        return crt

    def get_category(self, cloth, gender):
        for category in self.server.clothes[gender]:
            for item in self.server.clothes[gender][category]:
                if item == cloth:
                    return category
        return None

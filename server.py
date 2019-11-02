import importlib
import threading
import subprocess
import socket
import logging
import time
import redis
import exceptions
from client import Client
from inventory import Inventory
from parser import Parser

modules = ["client_error", "house", "outside", "user_rating", "mail", "avatar",
           "location_game", "relations", "social_request", "user_rating",
           "competition", "furniture", "billing", "component", "support",
           "passport", "player", "statistics", "shop", "mobile", "confirm",
           "craft", "profession", "inventory", "event"]


def get_git_revision_short_hash():
    try:
        return subprocess.check_output(["git", "rev-parse",
                                        "--short", "HEAD"]).strip().decode()
    except (FileNotFoundError, subprocess.CalledProcessError):
        return "Unknown"


class Server():
    def __init__(self, host="0.0.0.0", port=8123):
        self.online = []
        self.inv = {}
        self.redis = redis.Redis(decode_responses=True)
        self.parser = Parser()
        self.conflicts = self.parser.parse_conflicts()
        self.achievements = self.parser.parse_achievements()
        self.trophies = self.parser.parse_trophies()
        self.game_items = self.parser.parse_game_items()
        self.appearance = self.parser.parse_appearance()
        self.modules = {}
        for item in modules:
            module = importlib.import_module(f"modules.{item}")
            class_ = getattr(module, module.class_name)
            self.modules[class_.prefix] = class_(self)
        self.revision = get_git_revision_short_hash()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((host, port))

    def listen(self):
        self.sock.listen(5)
        logging.info("Server is ready to accept connections")
        thread = threading.Thread(target=self._background)
        thread.daemon = True
        thread.start()
        while True:
            client, address = self.sock.accept()
            thread = threading.Thread(target=Client(self).handle,
                                      args=(client, address))
            thread.daemon = True
            thread.start()

    def process_data(self, data, client):
        if not client.uid:
            if data["type"] != 1:
                client.connection.shutdown(2)
            self.auth(data["msg"], client)
            return
        if data["type"] == 2:
            client.connection.shutdown(2)
            return
        elif data["type"] == 34:
            prefix = data["msg"][1].split(".")[0]
            if prefix not in self.modules:
                logging.warning(f"Command {data['msg'][1]} not found")
                return
            self.modules[prefix].on_message(data["msg"], client)

    def auth(self, msg, client):
        uid = self.redis.get(f"auth:{msg[2]}")
        if not uid:
            client.connection.shutdown(2)
            return
        banned = self.redis.get(f"uid:{uid}:banned")
        if banned:
            ban_time = int(self.redis.get(f"uid:{uid}:ban_time"))
            client.send([10, "User is banned",
                         {"duration": 999999, "banTime": ban_time,
                          "notes": "Опа бан", "reviewerId": banned,
                          "reasonId": 0, "unbanType": "none", "leftTime": 0,
                          "id": None, "reviewState": 1, "userId": uid,
                          "moderatorId": banned}], type_=2)
            client.connection.shutdown(2)
            return
        for tmp in self.online:
            if tmp.uid == uid:
                try:
                    tmp.connection.shutdown(2)
                except OSError:
                    pass
                break
        client.uid = uid
        self.online.append(client)
        self.redis.set(f"uid:{uid}:lvt", int(time.time()))
        if uid not in self.inv:
            self.inv[uid] = Inventory(self, uid)
        else:
            self.inv[uid].expire = None
        client.send([client.uid, True, False, False], type_=1)
        client.checksummed = True

    def get_user_data(self, uid):
        pipe = self.redis.pipeline()
        pipe.get(f"uid:{uid}:slvr").get(f"uid:{uid}:enrg")
        pipe.get(f"uid:{uid}:gld").get(f"uid:{uid}:exp").get(f"uid:{uid}:emd")
        pipe.get(f"uid:{uid}:lvt").get(f"uid:{uid}:trid").get(f"uid:{uid}:crt")
        pipe.get(f"uid:{uid}:hrt").get(f"uid:{uid}:role")
        result = pipe.execute()
        if not result[0]:
            return None
        if result[7]:
            crt = int(result[7])
        else:
            crt = self.modules["a"].update_crt(uid)
        if result[8]:
            hrt = int(result[8])
        else:
            hrt = self.modules["frn"].update_hrt(uid)
        if result[9]:
            role = int(result[9])
        else:
            role = 0
        return {"uid": uid, "slvr": int(result[0]), "enrg": int(result[1]),
                "gld": int(result[2]), "exp": int(result[3]),
                "emd": int(result[4]), "lvt": int(result[5]), "crt": crt,
                "hrt": hrt, "trid": result[6], "role": role}

    def get_appearance(self, uid):
        apprnc = self.redis.lrange(f"uid:{uid}:appearance", 0, -1)
        if not apprnc:
            return False
        return {"n": apprnc[0], "nct": int(apprnc[1]), "g": int(apprnc[2]),
                "sc": int(apprnc[3]), "ht": int(apprnc[4]),
                "hc": int(apprnc[5]), "brt": int(apprnc[6]),
                "brc": int(apprnc[7]), "et": int(apprnc[8]),
                "ec": int(apprnc[9]), "fft": int(apprnc[10]),
                "fat": int(apprnc[11]), "fac": int(apprnc[12]),
                "ss": int(apprnc[13]), "ssc": int(apprnc[14]),
                "mt": int(apprnc[15]), "mc": int(apprnc[16]),
                "sh": int(apprnc[17]), "shc": int(apprnc[18]),
                "rg": int(apprnc[19]), "rc": int(apprnc[20]),
                "pt": int(apprnc[21]), "pc": int(apprnc[22]),
                "bt": int(apprnc[23]), "bc": int(apprnc[24])}

    def get_clothes(self, uid, type_):
        clothes = []
        for item in self.redis.smembers(f"uid:{uid}:wearing"):
            if "_" in item:
                id_, clid = item.split("_")
                clothes.append({"id": id_, "clid": clid})
            else:
                clothes.append({"id": item, "clid": None})
        if type_ == 1:
            clths = {"cc": "casual", "ccltns": {"casual": {"cct": [],
                                                           "cn": "",
                                                           "ctp": "casual"}}}
            for item in clothes:
                if item["clid"]:
                    clths["ccltns"]["casual"]["cct"].append(f"{item['id']}:"
                                                            f"{item['clid']}")
                else:
                    clths["ccltns"]["casual"]["cct"].append(item["id"])
        elif type_ == 2:
            clths = {"clths": []}
            for item in clothes:
                clths["clths"].append({"tpid": item["id"],
                                       "clid": item["clid"]})
        elif type_ == 3:
            clths = {"cct": []}
            for item in clothes:
                if item["clid"]:
                    clths["cct"].append(f"{item['id']}:{item['clid']}")
                else:
                    clths["cct"].append(item["id"])
        return clths

    def get_room_items(self, uid, room):
        if "_" in room:
            raise exceptions.WrongRoom()
        items = []
        for name in self.redis.smembers(f"rooms:{uid}:{room}:items"):
            item = self.redis.lrange(f"rooms:{uid}:{room}:items:{name}", 0, -1)
            name, lid = name.split("_")
            if len(item) == 5:
                items.append({"tpid": name, "x": float(item[0]),
                              "y": float(item[1]), "z": float(item[2]),
                              "d": int(item[3]), "lid": int(lid),
                              "rid": item[4]})
            else:
                items.append({"tpid": name, "x": float(item[0]),
                              "y": float(item[1]), "z": float(item[2]),
                              "d": int(item[3]), "lid": int(lid)})
        return items

    def _background(self):
        while True:
            logging.info(f"Players online: {len(self.online)}")
            for uid in self.inv.copy():
                inv = self.inv[uid]
                if inv.expire and time.time() - inv.expire > 0:
                    del self.inv[uid]
            time.sleep(60)


if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)-8s [%(asctime)s]  %(message)s",
                        datefmt="%H:%M:%S", level=logging.DEBUG)
    server = Server()
    server.listen()

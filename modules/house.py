from modules.location import Location, gen_plr
import common
import const

class_name = "House"


class House(Location):
    prefix = "h"

    def __init__(self, server):
        super().__init__(server)
        self.commands.update({"minfo": self.get_my_info, "gr": self.get_room,
                              "oinfo": self.owner_info,
                              "ioinfo": self.init_owner_info})

    def get_my_info(self, msg, client):
        apprnc = self.server.get_appearance(client.uid)
        if not apprnc:
            client.send(["h.minfo", {"has.avtr": False}])
            return
        user_data = self.server.get_user_data(client.uid)
        inv = self.server.inv[client.uid].get()
        cs = self.server.get_clothes(client.uid, type_=1)
        rooms = []
        for item in self.server.redis.smembers(f"rooms:{client.uid}"):
            room = self.server.redis.lrange(f"rooms:{client.uid}:{item}",
                                            0, -1)
            rooms.append({"f": self.server.get_room_items(client.uid, item),
                          "w": 13, "id": item, "lev": int(room[1]), "l": 13,
                          "nm": room[0]})
        tr = {}
        for item in const.tr:
            tr[item] = {"trrt": 0, "trcd": 0, "trid": item}
        plr = gen_plr(client, self.server)
        plr.update({"cs": cs, "hs": {"r": rooms, "lt": 0}, "inv": inv,
                    "onl": True})
        plr["res"] = {"slvr": user_data["slvr"], "enrg": user_data["enrg"],
                      "emd": user_data["emd"], "gld": user_data["gld"]}
        client.send(["h.minfo", {"plr": plr, "tm": 1}])
        self._perform_login(client)

    def owner_info(self, msg, client):
        if not msg[2]["uid"]:
            return
        plr = gen_plr(msg[2]["uid"], self.server)
        rooms = []
        tmp = self.server.redis.smembers(f"rooms:{msg[2]['uid']}")
        for item in tmp:
            room = self.server.redis.lrange(f"rooms:{msg[2]['uid']}:{item}",
                                            0, -1)
            room_items = self.server.get_room_items(msg[2]["uid"], item)
            rooms.append({"f": room_items, "w": 13, "l": 13, "id": item,
                          "lev": int(room[1]), "nm": room[0]})
            client.send(["h.oinfo", {"ath": False, "plr": plr,
                                     "hs": {"r": rooms, "lt": 0}}])

    def init_owner_info(self, msg, client):
        if not msg[2]["uid"]:
            return
        plr = gen_plr(msg[2]["uid"], self.server)
        client.send("h.ioinfo", {"tids": [], "ath": False, "plr": plr})

    def get_room(self, msg, client):
        room = f"{msg[2]['lid']}_{msg[2]['gid']}_{msg[2]['rid']}"
        if client.room:
            prefix = common.get_prefix(client.room)
            for tmp in self.server.online.copy():
                if tmp.room != client.room or tmp.uid == client.uid:
                    continue
                tmp.send([f"{prefix}.r.lv", {"uid": client.uid}])
                tmp.send([client.room, client.uid], type_=17)
        client.room = room
        client.position = (-1.0, -1.0)
        client.action_tag = ""
        client.state = 0
        client.dimension = 4
        plr = gen_plr(client, self.server)
        for tmp in self.server.online.copy():
            if tmp.room != client.room:
                continue
            prefix = common.get_prefix(client.room)
            tmp.send([f"{prefix}.r.jn", {"plr": plr}])
            tmp.send([client.room, client.uid], type_=16)
        client.send(["h.gr", {"rid": client.room}])

    def room(self, msg, client):
        subcommand = msg[1].split(".")[2]
        if subcommand == "info":
            rmmb = []
            room = msg[0]
            for tmp in self.server.online.copy():
                if tmp.room != room:
                    continue
                rmmb.append(gen_plr(tmp, self.server))
            room_addr = f"rooms:{msg[2]['uid']}:{msg[2]['rid']}"
            tmp = self.server.redis.lrange(room_addr, 0, -1)
            room_items = self.server.get_room_items(msg[2]["uid"],
                                                    msg[2]["rid"])
            room = {"f": room_items, "w": 13, "id": msg[2]["rid"],
                    "l": 13, "lev": int(tmp[1]), "nm": tmp[0]}
            client.send(["h.r.info", {"rmmb": rmmb, "rm": room,
                                      "evn": None}])
        elif subcommand == "rfr":
            room = msg[0].split("_")[-1]
            room_data = self.server.redis.lrange(f"rooms:{client.uid}:{room}",
                                                 0, -1)
            room_items = self.server.get_room_items(client.uid, room)
            for tmp in self.server.online.copy():
                if tmp.room != msg[0]:
                    continue
                tmp.send(["h.r.rfr", {"rm": {"f": room_items, "w": 13, "l": 13,
                                             "lev": int(room_data[1]),
                                             "nm": room_data[0]}}])
        else:
            super().room(msg, client)

    def _perform_login(self, client):
        client.send(["cm.new", {"campaigns": const.campaigns}])
        client.send(["cp.cht.gbl", {"blcklst": {"uids": []}}])
        client.send(["nws.hasnews", {"gnexst": True, "gnunr": True}])

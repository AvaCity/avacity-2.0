from modules.base_module import Module
from modules.location import gen_plr

class_name = "Furniture"


class Furniture(Module):
    prefix = "frn"

    def __init__(self, server):
        self.server = server
        self.commands = {"save": self.save_layout, "buy": self.buy}
        self.frn_list = server.parser.parse_furniture()

    def save_layout(self, msg, client):
        room = msg[0].split("_")
        uid = client.uid
        if room[1] != client.uid:
            return
        for item in msg[2]["f"]:
            if item["t"] == 0:
                self.type_add(item, room, uid)
            if item["t"] == 1:
                self.type_update(item, room, uid)
            elif item["t"] == 2:
                self.type_remove(item, room, uid)
            elif item["t"] == 3:
                self.type_replace_door(item, room, uid)
        inv = self.server.inv[uid].get()
        room_inf = self.server.redis.lrange(f"rooms:{uid}:{room[2]}", 0, -1)
        room_items = self.server.get_room_items(uid, room[2])
        self.update_hrt(uid)
        ci = gen_plr(client, self.server)["ci"]
        client.send(["frn.save", {"inv": inv, "ci": ci,
                                  "hs": {"f": room_items, "w": 13,
                                         "id": room[2], "l": 13,
                                         "lev": int(room_inf[1]),
                                         "nm": room[0]}}])

    def type_add(self, item, room, uid):
        items = self.server.redis.smembers(f"rooms:{uid}:{room[2]}:items")
        if not self.server.inv[uid].take_item(item["tpid"]):
            return
        if any(ext in item["tpid"].lower() for ext in ["wll", "wall"]):
            walls = []
            for wall in ["wall", "wll"]:
                for room_item in items:
                    if wall in room_item.lower():
                        self.del_item(room_item, room[2], uid)
                        tmp = room_item.split("_")[0]
                        if tmp not in walls:
                            walls.append(tmp)
                            self.server.inv[uid].add_item(tmp, "frn")
            item["x"] = 0.0
            item["y"] = 0.0
            item["z"] = 0.0
            item["d"] = 3
            self.add_item(item, room[2], uid)
            item["x"] = 13.0
            item["d"] = 5
            item["oid"] += 1
            self.add_item(item, room[2], uid)
        elif any(ext in item["tpid"].lower() for ext in ["flr", "floor"]):
            for floor in ["flr", "floor"]:
                for room_item in items:
                    if floor in room_item.lower():
                        self.del_item(room_item, room[2], uid)
                        tmp = room_item.split("_")[0]
                        self.server.inv[uid].add_item(tmp, "frn")
            item["x"] = 0.0
            item["y"] = 0.0
            item["z"] = 0.0
            item["d"] = 5
            self.add_item(item, room[2], uid)

    def type_update(self, item, room, uid):
        redis = self.server.redis
        items = redis.smembers(f"rooms:{uid}:{room[2]}:items")
        name = f"{item['tpid']}_{item['oid']}"
        if name in items:
            rid = redis.lindex(f"rooms:{uid}:{room[2]}:items:{name}", 4)
            if rid:
                item["rid"] = rid
            self.del_item(name, room[2], uid)
            self.add_item(item, room[2], uid)
        else:
            if not self.server.inv[uid].take_item(item["tpid"]):
                return
            self.add_item(item, room[2], uid)

    def type_remove(self, item, room, uid):
        items = self.server.redis.smembers(f"rooms:{uid}:{room[2]}:items")
        name = f"{item['tpid']}_{item['oid']}"
        if name not in items:
            return
        self.del_item(name, room[2], uid)
        self.server.inv[uid].add_item(item["tpid"], "frn")

    def type_replace_door(self, item, room, uid):
        items = self.server.redis.smembers(f"rooms:{uid}:{room[2]}:items")
        found = None
        for tmp in items:
            oid = int(tmp.split("_")[1])
            if oid == item["oid"]:
                found = tmp
                break
        if not found:
            return
        if not self.server.inv[uid].take_item(item["tpid"]):
            return
        data = self.server.redis.lrange(f"rooms:{uid}:{room[2]}:items:{found}",
                                        0, -1)
        if len(data) < 5:
            rid = None
        else:
            rid = data[4]
        self.del_item(found, room[2], uid)
        self.server.inv[uid].add_item(found.split("_")[0], "frn")
        item.update({"x": float(data[0]), "y": float(data[1]),
                     "z": float(data[2]), "d": int(data[3]),
                     "rid": rid})
        self.add_item(item, room[2], uid)

    def buy(self, msg, client):
        item = msg[2]["tpid"]
        amount = msg[2]["cnt"]
        uid = client.uid
        if item not in self.frn_list:
            return
        user_data = self.server.get_user_data(uid)
        gold = self.frn_list[item]["gold"]*amount
        silver = self.frn_list[item]["silver"]*amount
        if user_data["gld"] < gold or user_data["slvr"] < silver:
            return
        self.server.redis.set(f"uid:{uid}:gld", user_data["gld"] - gold)
        self.server.redis.set(f"uid:{uid}:slvr", user_data["slvr"] - silver)
        self.server.inv[uid].add_item(item, "frn", amount)
        amount = int(self.server.redis.lindex(f"uid:{uid}:items:{item}", 1))
        client.send(["ntf.inv", {"it": {"c": amount, "iid": "", "tid": item}}])
        user_data = self.server.get_user_data(uid)
        client.send(["ntf.res", {"res": {"gld": user_data["gld"],
                                         "slvr": user_data["slvr"],
                                         "enrg": user_data["enrg"],
                                         "emd": user_data["emd"]}}])

    def add_item(self, item, room, uid):
        self.server.redis.sadd(f"rooms:{uid}:{room}:items",
                               f"{item['tpid']}_{item['oid']}")
        if "rid" in item:
            self.server.redis.rpush(f"rooms:{uid}:{room}:items:"
                                    f"{item['tpid']}_{item['oid']}", item["x"],
                                    item["y"], item["z"], item["d"],
                                    item["rid"])
        else:
            self.server.redis.rpush(f"rooms:{uid}:{room}:items:"
                                    f"{item['tpid']}_{item['oid']}", item["x"],
                                    item["y"], item["z"], item["d"])

    def del_item(self, item, room, uid):
        items = self.server.redis.smembers(f"rooms:{uid}:{room}:items")
        if item not in items:
            return
        self.server.redis.srem(f"rooms:{uid}:{room}:items", item)
        self.server.redis.delete(f"rooms:{uid}:{room}:items:{item}")

    def update_hrt(self, uid):
        redis = self.server.redis
        hrt = 0
        for room in redis.smembers(f"rooms:{uid}"):
            for item in redis.smembers(f"rooms:{uid}:{room}:items"):
                item = item.split("_")[0]
                if item not in self.frn_list:
                    continue
                hrt += self.frn_list[item]["rating"]
        redis.set(f"uid:{uid}:hrt", hrt)
        return hrt

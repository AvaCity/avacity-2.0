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
            items = self.server.redis.smembers(f"rooms:{uid}:{room[2]}:items")
            if item["t"] == 1:
                name = f"{item['tpid']}_{item['oid']}"
                if name in items:
                    self.del_item(name, room[2], uid)
                    self.add_item(item, room[2], uid)
                else:
                    if not self.server.inv[uid].take_item(item["tpid"]):
                        continue
                    self.add_item(item, room[2], uid)
            elif item["t"] == 2:
                name = f"{item['tpid']}_{item['oid']}"
                if name not in items:
                    continue
                self.del_item(name, room[2], uid)
                self.server.inv[uid].add_item(item["tpid"], "frn")
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

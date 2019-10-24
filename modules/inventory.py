from modules.base_module import Module
from modules.location import gen_plr

class_name = "Inventory"


class Inventory(Module):
    prefix = "tr"

    def __init__(self, server):
        self.server = server
        self.commands = {"sale": self.sale_item}

    def sale_item(self, msg, client):
        items = self.server.game_items["game"]
        tpid = msg[2]["tpid"]
        cnt = msg[2]["cnt"]
        if tpid not in items or "saleSilver" not in items[tpid]:
            return
        if not self.server.inv[client.uid].take_item(tpid, cnt):
            return
        price = items[tpid]["saleSilver"]
        user_data = self.server.get_user_data(client.uid)
        redis = self.server.redis
        redis.set(f"uid:{client.uid}:slvr", user_data["slvr"]+price*cnt)
        ci = gen_plr(client.uid, self.server)["ci"]
        client.send(["ntf.ci", {"ci": ci}])
        inv = self.server.inv[client.uid].get()
        client.send(["ntf.inv", {"inv": inv}])
        user_data = self.server.get_user_data(client.uid)
        client.send(["ntf.res", {"res": {"gld": user_data["gld"],
                                         "slvr": user_data["slvr"],
                                         "enrg": user_data["enrg"],
                                         "emd": user_data["emd"]}}])

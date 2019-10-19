from modules.base_module import Module

class_name = "Shop"


class Shop(Module):
    prefix = "sh"

    def __init__(self, server):
        self.server = server
        self.commands = {"bji": self.buy_joke_item}
        self.items = server.parser.parse_game_items()

    def buy_joke_item(self, msg, client):
        item = msg[2]["tpid"]
        cnt = msg[2]["cnt"]
        if item not in self.items:
            return
        gold = self.items[item]["gold"]*cnt
        silver = self.items[item]["silver"]*cnt
        user_data = self.server.get_user_data(client.uid)
        if user_data["gld"] < gold or user_data["slvr"] < silver:
            return
        redis = self.server.redis
        redis.set(f"uid:{client.uid}:gld", user_data["gld"]-gold)
        redis.set(f"uid:{client.uid}:slvr", user_data["slvr"]-silver)
        self.server.inv[client.uid].add_item(item, "gm", cnt)
        client.send(["ntf.inv", {"it": {"c": cnt, "lid": "", "tid": item}}])
        user_data = self.server.get_user_data(client.uid)
        client.send(["ntf.res", {"res": {"gld": user_data["gld"],
                                         "slvr": user_data["slvr"],
                                         "enrg": user_data["enrg"],
                                         "emd": user_data["emd"]}}])

from modules.base_module import Module

class_name = "Craft"


class Craft(Module):
    prefix = "crt"

    def __init__(self, server):
        self.server = server
        self.commands = {"bc": self.buy_component, "prd": self.produce}
        self.craft_items = server.parser.parse_craft()

    def buy_component(self, msg, client):
        buy_for = msg[2]["itId"]
        if buy_for not in self.craft_items:
            return
        to_buy = {}
        gold = 0
        redis = self.server.redis
        items = self.server.game_items["loot"]
        for item in msg[2]["cmIds"]:
            price = items[item]["gold"]/100
            have = redis.lindex(f"uid:{client.uid}:items:{item}", 1)
            if not have:
                have = 0
            else:
                have = int(have)
            amount = self.craft_items[buy_for][item] - have
            if amount <= 0:
                continue
            gold += int(rd(price * amount))
            to_buy[item] = amount
        user_data = self.server.get_user_data(client.uid)
        if user_data["gld"] < gold:
            return
        redis.set(f"uid:{client.uid}:gld", user_data["gld"]-gold)
        compIts = []
        for item in msg[2]["cmIds"]:
            self.server.inv[client.uid].add_item(item, "lt", to_buy[item])
            compIts.append({"c": to_buy[item], "iid": "", "tid": item})
        user_data = self.server.get_user_data(client.uid)
        client.send(["crt.bc", {"res": {"gld": user_data["gld"],
                                        "slvr": user_data["slvr"],
                                        "enrg": user_data["enrg"],
                                        "emd": user_data["emd"]},
                                "itId": buy_for, "compIts": compIts}])

    def produce(self, msg, client):
        itId = msg[2]["itId"]
        if itId not in self.craft_items:
            return
        redis = self.server.redis
        for item in self.craft_items[itId]:
            have = redis.lindex(f"uid:{client.uid}:items:{item}", 1)
            if not have:
                return
            have = int(have)
            if have < self.craft_items[itId][item]:
                return
        for item in self.craft_items[itId]:
            amount = self.craft_items[itId][item]
            self.server.inv[client.uid].take_item(item, amount)
        if itId in self.server.game_items["game"]:
            type_ = "gm"
        elif itId in self.server.game_items["loot"]:
            type_ = "lt"
        elif itId in self.server.modules["frn"].frn_list:
            type_ = "frn"
        self.server.inv[client.uid].add_item(itId, type_)
        inv = self.server.inv[client.uid].get()
        client.send(["crt.prd", {"inv": inv, "crIt": {"c": 1, "lid": "",
                                                      "tid": itId}}])


def rd(x, y=0):
    ''' A classical mathematical rounding by Voznica '''
    m = int('1'+'0'*y)  # multiplier - how many positions to the right
    q = x*m  # shift to the right by multiplier
    c = int(q)  # new number
    i = int((q-c)*10)  # indicator number on the right
    if i >= 5:
        c += 1
    return c/m

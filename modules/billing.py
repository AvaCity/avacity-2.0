from modules.base_module import Module

class_name = "Billing"


class Billing(Module):
    prefix = "b"

    def __init__(self, server):
        self.server = server
        self.commands = {"chkprchs": self.check_purchase,
                         "bs": self.buy_silver}

    def check_purchase(self, msg, client):
        amount = int(msg[2]["prid"].split("pack")[1])*100
        user_data = self.server.get_user_data(client.uid)
        gold = user_data["gld"] + amount
        self.server.redis.set(f"uid:{client.uid}:gld", gold)
        res = {"gld": gold, "slvr": user_data["slvr"],
               "enrg": user_data["enrg"], "emd": user_data["emd"]}
        client.send(["ntf.res", {"res": res}])
        client.send(["b.ingld", {"ingld": amount}])

    def buy_silver(self, msg, client):
        user_data = self.server.get_user_data(client.uid)
        if user_data["gld"] < msg[2]["gld"]:
            return
        self.server.redis.set(f"uid:{client.uid}:gld",
                              user_data["gld"] - msg[2]["gld"])
        self.server.redis.set(f"uid:{client.uid}:slvr",
                              user_data["slvr"] + msg[2]["gld"] * 100)
        res = {"gld": user_data["gld"] - msg[2]["gld"],
               "slvr": user_data["slvr"] + msg[2]["gld"] * 100,
               "enrg": user_data["enrg"], "emd": user_data["emd"]}
        client.send(["ntf.res", {"res": res}])
        client.send(["b.inslv", {"inslv": msg[2]["gld"] * 100}])

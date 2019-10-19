from modules.base_module import Module

class_name = "Mobile"

class Mobile(Module):
    prefix = "mb"

    def __init__(self, server):
        self.server = server
        self.commands = {"mkslf": self.make_selfie}

    def make_selfie(self, msg, client):
        amount = 1
        if msg[2]["stg"]:
            amount += 1
        if not self.server.inv[client.uid].take_item("film", amount):
            return
        cnt = self.server.redis.lindex(f"uid:{client.uid}:items:film", 1)
        if cnt:
            cnt = int(cnt)
        else:
            cnt = 0
        client.send(["ntf.inv", {"it": {"c": cnt, "lid": "", "tid": "film"}}])
        client.send(["mb.mkslf", {"sow": client.uid, "stg": msg[2]["stg"],
                                  "zm": msg[2]["zm"]}])
        if msg[2]["stg"]:
            for tmp in self.server.online.copy():
                if tmp.uid == msg[2]["stg"]:
                    tmp.send(["mb.mkslf", {"sow": client.uid, "stg": tmp.uid,
                                           "zm": msg[2]["zm"]}])
                    break

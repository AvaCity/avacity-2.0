from modules.base_module import Module

class_name = "Relations"


class Relations(Module):
    prefix = "rl"

    def __init__(self, server):
        self.server = server
        self.commands = {"get": self.get_relations}

    def get_relations(self, msg, client):
        data = ["rl.get", {"uid": client.uid, "rlts": {}}]
        for match in [f"rl:{client.uid}:*", f"rl:*:{client.uid}"]:
            for key in self.server.redis.scan_iter(match=match):
                if len(key.split(":")) > 3:
                    continue
                if key.split(":")[1] == client.uid:
                    user = key.split(":")[2]
                else:
                    user = key.split(":")[1]
                pipe = self.server.redis.pipeline()
                for item in ["p", "st", "s", "t", "ut"]:
                    pipe.get(f"{key}:{item}")
                result = pipe.execute()
                data[1]["rlts"][user] = {"p": int(result[0]),
                                         "st": int(result[1]),
                                         "s": int(result[2]),
                                         "t": result[3],
                                         "ut": int(result[4])}
        client.send(data)

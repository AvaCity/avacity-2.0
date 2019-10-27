import time
from modules.base_module import Module

class_name = "Relations"


class Relations(Module):
    prefix = "rl"

    def __init__(self, server):
        self.server = server
        self.commands = {"get": self.get_relations,
                         "crt": self.create_relation,
                         "adcr": self.admin_create_relation,
                         "rmv": self.remove_relation,
                         "crs": self.change_relation_status}
        self.statuses = self.server.parser.parse_relations()
        self.progresses = self.server.parser.parse_relation_progresses()

    def get_relations(self, msg, client):
        data = ["rl.get", {"uid": client.uid, "rlts": {}}]
        relations = self.server.redis.smembers(f"rl:{client.uid}")
        for rl in relations:
            if rl.split(":")[0] == client.uid:
                user = rl.split(":")[1]
            else:
                user = rl.split(":")[0]
            pipe = self.server.redis.pipeline()
            for item in ["p", "st", "s", "t", "ut"]:
                pipe.get(f"rl:{rl}:{item}")
            result = pipe.execute()
            data[1]["rlts"][user] = {"p": int(result[0]),
                                     "st": int(result[1]),
                                     "s": int(result[2]),
                                     "t": result[3],
                                     "ut": int(result[4])}
        client.send(data)

    def create_relation(self, msg, client):
        confirms = self.server.modules["cf"].confirms
        privileges = self.server.modules["cp"].privileges
        user_data = self.server.get_user_data(client.uid)
        if client.uid not in confirms and \
           user_data["role"] < privileges["RELATION_TEST_PANEL"]:
            return
        if client.uid in confirms and \
           not confirms[client.uid]["completed"]:
            return
        relation = msg[2]
        if self.get_link(client.uid, relation["uid"]):
            return
        self._create_relation(f"{client.uid}:{relation['uid']}", relation)
        if client.uid in confirms:
            del confirms[client.uid]

    def remove_relation(self, msg, client):
        uid = msg[2]["uid"]
        if uid == client.uid:
            return
        redis = self.server.redis
        link = None
        for rl in redis.smembers(f"rl:{client.uid}"):
            if uid in rl:
                link = rl
                break
        if not link:
            return
        self._remove_relation(link)

    def admin_create_relation(self, msg, client):
        privileges = self.server.modules["cp"].privileges
        user_data = self.server.get_user_data(client.uid)
        if user_data["role"] < privileges["RELATION_TEST_PANEL"]:
            return
        relation = msg[2]
        if client.uid == relation["uid"]:
            return
        link = self.get_link(client.uid, relation["uid"])
        if not link:
            return self._create_relation(f"{client.uid}:{relation['uid']}",
                                         relation)
        self._update_relation(link, relation)

    def change_relation_status(self, msg, client):
        relation = msg[2]
        link = self.get_link(client.uid, relation["uid"])
        if not link:
            return
        rl = self._get_relation(client.uid, link)["rlt"]
        status = self.statuses[rl["s"]]
        if relation["s"] not in status["transition"]:
            privileges = self.server.modules["cp"].privileges
            user_data = self.server.get_user_data(client.uid)
            if user_data["role"] < privileges["RELATION_TEST_PANEL"]:
                return
        self._update_relation(link, relation)

    def _create_relation(self, link, relation):
        pipe = self.server.redis.pipeline()
        for uid in link.split(":"):
            pipe.sadd(f"rl:{uid}", link)
        pipe.set(f"rl:{link}:p", 0)
        pipe.set(f"rl:{link}:st", int(time.time()))
        pipe.set(f"rl:{link}:ut", int(time.time()))
        pipe.set(f"rl:{link}:s", relation["s"])
        pipe.execute()
        for uid in link.split(":"):
            rl = self._get_relation(uid, link)
            for tmp in self.server.online.copy():
                if tmp.uid != uid:
                    continue
                tmp.send(["rl.new", rl])
                break

    def _update_relation(self, link, relation):
        pipe = self.server.redis.pipeline()
        pipe.set(f"rl:{link}:p", 0)
        pipe.set(f"rl:{link}:st", int(time.time()))
        pipe.set(f"rl:{link}:ut", int(time.time()))
        pipe.set(f"rl:{link}:s", relation["s"])
        pipe.execute()
        for uid in link.split(":"):
            rl = self._get_relation(uid, link)
            for tmp in self.server.online.copy():
                if tmp.uid != uid:
                    continue
                tmp.send(["rl.crs", rl])
                break

    def _remove_relation(self, link):
        pipe = self.server.redis.pipeline()
        pipe.delete(f"rl:{link}:p")
        pipe.delete(f"rl:{link}:st")
        pipe.delete(f"rl:{link}:ut")
        pipe.delete(f"rl:{link}:s")
        pipe.delete(f"rl:{link}:t")
        for uid in link.split(":"):
            pipe.srem(f"rl:{uid}", link)
        pipe.execute()
        for uid in link.split(":"):
            if link.split(":")[0] == uid:
                second_uid = link.split(":")[1]
            else:
                second_uid = link.split(":")[0]
            for tmp in self.server.online.copy():
                if tmp.uid != uid:
                    continue
                tmp.send(["rl.rmv", {"uid": second_uid}])

    def add_progress(self, action, link):
        value = self.progresses[action]
        s = int(self.server.redis.get(f"rl:{link}:s"))
        p = int(self.server.redis.get(f"rl:{link}:p"))
        if 100 in self.statuses[s]["progress"]:
            max_value = 100
        else:
            max_value = 0
        if -100 in self.statuses[s]["progress"]:
            min_value = -100
        else:
            min_value = 0
        total = p + value
        if total >= max_value:
            total = 100
        elif min_value < min_value:
            total = -100
        if total in self.statuses[s]["progress"]:
            self.server.redis.set(f"rl:{link}:p", 0)
            self.server.redis.set(f"rl:{link}:s",
                                  self.statuses[s]["progress"][total])
            command = "rl.crs"
        else:
            self.server.redis.set(f"rl:{link}:p", total)
            command = "rl.urp"
        for uid in link.split(":"):
            rl = self._get_relation(uid, link)
            rl["chprr"] = action
            for tmp in self.server.online.copy():
                if tmp.uid != uid:
                    continue
                tmp.send([command, rl])
                break

    def get_link(self, uid1, uid2):
        rlts = self.server.redis.smembers(f"rl:{uid1}")
        if f"{uid1}:{uid2}" in rlts:
            return f"{uid1}:{uid2}"
        elif f"{uid2}:{uid1}" in rlts:
            return f"{uid2}:{uid1}"
        else:
            return None

    def _get_relation(self, uid, link):
        if link.split(":")[0] == uid:
            second_uid = link.split(":")[1]
        else:
            second_uid = link.split(":")[0]
        pipe = self.server.redis.pipeline()
        for item in ["p", "st", "ut", "s", "t"]:
            pipe.get(f"rl:{link}:{item}")
        result = pipe.execute()
        rl = {"uid": second_uid, "rlt": {"p": int(result[0]),
                                         "st": int(result[1]),
                                         "ut": int(result[2]),
                                         "s": int(result[3]),
                                         "t": result[4]}}
        return rl

import logging


class Inventory():
    def __init__(self, server, uid):
        self.server = server
        self.uid = uid
        self.expire = None
        self._get_inventory()

    def get(self):
        return self.inv

    def add_item(self, name, type_, amount=1):
        if "_" in name:
            tid, iid = name.split("_")
        else:
            tid = name
            iid = ""
        item = self.server.redis.lrange(f"uid:{self.uid}:items:{name}",
                                        0, -1)
        if item:
            if type_ == "cls":
                logging.error("Can't be more than one cloth")
                return
            self.server.redis.lset(f"uid:{self.uid}:items:{name}", 1,
                                   int(item[1])+amount)
            for tmp in self.inv["c"][type_]["it"]:
                if tmp["tid"] == tid and tmp["iid"] == iid:
                    tmp["c"] = int(item[1])+amount
                    break
        else:
            self.server.redis.sadd(f"uid:{self.uid}:items", name)
            self.server.redis.rpush(f"uid:{self.uid}:items:{name}", type_,
                                    amount)
            type_items = self.inv["c"][type_]["it"]
            type_items.append({"c": amount, "tid": tid, "iid": iid})

    def take_item(self, item, amount=1):
        items = self.server.redis.smembers(f"uid:{self.uid}:items")
        if item not in items:
            return False
        tmp = self.server.redis.lrange(f"uid:{self.uid}:items:{item}", 0, -1)
        type_ = tmp[0]
        have = int(tmp[1])
        del tmp
        if have < amount:
            return False
        type_items = self.inv["c"][type_]["it"]
        if have > amount:
            self.server.redis.lset(f"uid:{self.uid}:items:{item}", 1,
                                   have - amount)
            for tmp in type_items:
                if tmp["tid"] == item:
                    tmp["c"] = have - amount
                    break
        else:
            self.server.redis.delete(f"uid:{self.uid}:items:{item}")
            self.server.redis.srem(f"uid:{self.uid}:items", item)
            for tmp in type_items:
                if tmp["tid"] == item:
                    type_items.remove(tmp)
                    break
        return True

    def get_item(self, item):
        items = self.server.redis.smembers(f"uid:{self.uid}:items")
        if item not in items:
            return 0
        have = int(self.server.redis.lindex(f"uid:{self.uid}:items:{item}", 1))
        return have

    def change_wearing(self, cloth, wearing):
        if not self.server.redis.lindex(f"uid:{self.uid}:items:{cloth}", 0):
            not_found = True
        else:
            not_found = False
        if "_" in cloth:
            tid, iid = cloth.split("_")
        else:
            tid = cloth
            iid = ""
        type_items = self.inv["c"]["cls"]["it"]
        if wearing:
            if not_found:
                logging.error(f"Cloth {cloth} not found for {self.uid}")
                return
            if "_" in cloth:
                name = cloth.split("_")[0]
            else:
                name = cloth
            self._check_conflicts(name)
            for item in type_items:
                if item["tid"] == tid and item["iid"] == iid:
                    type_items.remove(item)
                    break
            self.server.redis.sadd(f"uid:{self.uid}:wearing", cloth)
        else:
            weared = self.server.redis.smembers(f"uid:{self.uid}:wearing")
            if cloth not in weared:
                logging.error(f"Cloth {cloth} not weared for {self.uid}")
                return
            if not not_found:
                type_items.append({"c": 1, "iid": iid, "tid": tid})
            self.server.redis.srem(f"uid:{self.uid}:wearing", cloth)

    def __get_expire(self):
        return self.__expire

    def __set_expire(self, value):
        self.__expire = value

    expire = property(__get_expire, __set_expire)

    def _get_inventory(self):
        self.inv = {"c": {"frn": {"id": "frn", "it": []},
                          "act": {"id": "act", "it": []},
                          "gm": {"id": "gm", "it": []},
                          "lt": {"id": "lt", "it": []},
                          "cls": {"id": "cls", "it": []}}}
        wearing = self.server.redis.smembers(f"uid:{self.uid}:wearing")
        keys = []
        pipe = self.server.redis.pipeline()
        for item in self.server.redis.smembers(f"uid:{self.uid}:items"):
            if item in wearing:
                continue
            pipe.lrange(f"uid:{self.uid}:items:{item}", 0, -1)
            keys.append(item)
        items = pipe.execute()
        for i in range(len(keys)):
            name = keys[i]
            item = items[i]
            if "_" in name:
                self.inv["c"][item[0]]["it"].append({"c": int(item[1]),
                                                     "iid": name.split("_")[1],
                                                     "tid": name.split("_")[0]}
                                                    )
            else:
                self.inv["c"][item[0]]["it"].append({"c": int(item[1]),
                                                     "iid": "",
                                                     "tid": name})

    def _check_conflicts(self, cloth):
        gender = "boy" if (self.server.get_appearance(self.uid))["g"] == 1 \
                          else "girl"
        category = self.server.modules["a"].get_category(cloth, gender)
        if not category:
            logging.error("Category not found")
            return
        weared = self.server.redis.smembers(f"uid:{self.uid}:wearing")
        for weared_cloth in weared:
            if self._has_conflict(weared_cloth, category, gender):
                self.change_wearing(weared_cloth, False)

    def _has_conflict(self, cloth, category, gender):
        get_category = self.server.modules["a"].get_category
        cloth_category = get_category(cloth, gender)
        if cloth_category == category:
            return True
        for conflict in self.server.conflicts:
            if (conflict[0] == category and
                conflict[1] == cloth_category) or \
               (conflict[1] == category and
               conflict[0] == cloth_category):
                return True
        return False

from modules.base_module import Module

class_name = "Profession"


class Profession(Module):
    prefix = "prf"

    def __init__(self, server):
        self.server = server
        self.commands = {"vsgprp": self.visage_propose,
                         "vsgapprv": self.visage_approve}
        self.colors = {"sh": "shc", "pt": "pc", "ss": "ssc", "fat": "fac"}
        self.propose = {}

    def visage_propose(self, msg, client):
        second_client = None
        for tmp in self.server.online.copy():
            if tmp.uid == msg[2]["uid"]:
                if tmp.room != client.room:
                    break
                second_client = tmp
                break
        if not second_client:
            return
        new_apprnc = {"sh": msg[2]["apprnc"]["sh"],
                      "shc": msg[2]["apprnc"]["shc"],
                      "pt": msg[2]["apprnc"]["pt"],
                      "pc": msg[2]["apprnc"]["pc"],
                      "ss": msg[2]["apprnc"]["ss"],
                      "ssc": msg[2]["apprnc"]["ssc"],
                      "fat": msg[2]["apprnc"]["fat"],
                      "fac": msg[2]["apprnc"]["fac"]}
        apprnc = self.server.get_appearance(msg[2]["uid"])
        price = self._calculate_price(apprnc, new_apprnc)
        if self.server.inv[client.uid].get_item("vsgstBrush") < price:
            return
        apprnc.update(new_apprnc)
        self.propose[second_client.uid] = {"uid": client.uid, "apprnc": apprnc,
                                           "price": price}
        second_client.send(["prf.vsgapprv", {"uid": client.uid,
                                             "apprnc": apprnc}])

    def visage_approve(self, msg, client):
        if client.uid not in self.propose:
            return
        if not msg[2]["apprvd"]:
            del self.propose[client.uid]
            return
        price = self.propose[client.uid]["price"]
        sender = self.propose[client.uid]["uid"]
        if not self.server.inv[sender].take_item("vsgstBrush", price):
            return
        apprnc = self.propose[client.uid]["apprnc"]
        del self.propose[client.uid]
        self.server.modules["a"].update_appearance(apprnc, client)
        apprnc = self.server.get_appearance(client.uid)
        client.send(["a.apprnc.save", {"apprnc": apprnc}])
        for tmp in self.server.online.copy():
            if tmp.uid == sender:
                amount = self.server.inv[sender].get_item("vsgstBrush")
                tmp.send(["ntf.inv", {"it": {"c": amount, "iid": "",
                                             "tid": "vsgstBrush"}}])
                break

    def _calculate_price(self, old_apprnc, new_apprnc):
        gender = "boy" if old_apprnc["g"] == 1 else "girl"
        brush = 0
        for item in ["sh", "pt", "ss", "fat"]:
            if new_apprnc[item] == old_apprnc[item]:
                color = self.colors[item]
                if new_apprnc[color] == old_apprnc[color]:
                    continue
            id_ = new_apprnc[item]
            brush += self.server.appearance[gender][item][id_]["brush"]
        return brush

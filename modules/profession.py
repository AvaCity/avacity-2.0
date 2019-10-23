from modules.base_module import Module

class_name = "Profession"


class Profession(Module):
    prefix = "prf"

    def __init__(self, server):
        self.server = server
        self.commands = {"vsgprp": self.visage_propose,
                         "vsgapprv": self.visage_approve}
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
        apprnc.update(new_apprnc)
        self.propose[second_client.uid] = {"uid": client.uid, "apprnc": apprnc}
        second_client.send(["prf.vsgapprv", {"uid": client.uid,
                                             "apprnc": apprnc}])

    def visage_approve(self, msg, client):
        if client.uid not in self.propose:
            return
        if not msg[2]["apprvd"]:
            return
        apprnc = self.propose[client.uid]["apprnc"]
        del self.propose[client.uid]
        self.server.modules["a"].update_appearance(apprnc, client)
        apprnc = self.server.get_appearance(client.uid)
        client.send(["a.apprnc.save", {"apprnc": apprnc}])

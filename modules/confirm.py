from modules.base_module import Module

class_name = "UserConfirm"


class UserConfirm(Module):
    prefix = "cf"

    def __init__(self, server):
        self.server = server
        self.commands = {"uc": self.user_confirm,
                         "uca": self.user_confirm_approve,
                         "ucd": self.user_confirm_decline}
        self.confirms = {}

    def user_confirm(self, msg, client):
        if msg[2]["uid"] == client.uid:
            return
        for tmp in self.server.online.copy():
            if tmp.uid == msg[2]["uid"]:
                self.confirms[client.uid] = {"uid": msg[2]["uid"],
                                             "at": msg[2]["at"],
                                             "completed": False}
                tmp.send(["cf.uc", {"uid": client.uid, "at": msg[2]["at"]}])
                break

    def user_confirm_approve(self, msg, client):
        for tmp in self.server.online.copy():
            if tmp.uid == msg[2]["uid"]:
                if self.confirms[tmp.uid]["at"] != msg[2]["at"]:
                    return
                if self.confirms[tmp.uid]["uid"] != client.uid:
                    return
                self.confirms[tmp.uid]["completed"] = True
                tmp.send(["cf.uca", {"uid": client.uid, "at": msg[2]["at"]}])
                break

    def user_confirm_decline(self, msg, client):
        for tmp in self.server.online.copy():
            if tmp.uid == msg[2]["uid"]:
                if self.confirms[tmp.uid]["at"] != msg[2]["at"]:
                    return
                if self.confirms[tmp.uid]["uid"] != client.uid:
                    return
                del self.confirms[tmp.uid]
                tmp.send(["cf.ucd", {"uid": client.uid, "at": msg[2]["at"]}])
                break

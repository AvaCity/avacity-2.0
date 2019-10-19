from modules.base_module import Module

class_name = "UserConfirm"


class UserConfirm(Module):
    prefix = "cf"

    def __init__(self, server):
        self.server = server
        self.commands = {"uc": self.user_confirm,
                         "uca": self.user_confirm_approve,
                         "ucd": self.user_confirm_decline}

    def user_confirm(self, msg, client):
        for tmp in self.server.online.copy():
            if tmp.uid == msg[2]["uid"]:
                tmp.send(["cf.uc", {"uid": client.uid, "at": msg[2]["at"]}])
                break

    def user_confirm_approve(self, msg, client):
        for tmp in self.server.online.copy():
            if tmp.uid == msg[2]["uid"]:
                tmp.send(["cf.uca", {"uid": client.uid, "at": msg[2]["at"]}])
                break

    def user_confirm_decline(self, msg, client):
        for tmp in self.server.online.copy():
            if tmp.uid == msg[2]["uid"]:
                tmp.send(["cf.ucd", {"uid": client.uid, "at": msg[2]["at"]}])
                break

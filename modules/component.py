from modules.base_module import Module

class_name = "Component"


class Component(Module):
    prefix = "cp"

    def __init__(self, server):
        self.server = server
        self.commands = {"cht": self.chat}

    def chat(self, msg, client):
        subcommand = msg[1].split(".")[2]
        if subcommand == "sm":  # send message
            msg.pop(0)
            if msg[1]["msg"]["cid"]:
                for uid in msg[1]["msg"]["cid"].split("_"):
                    for tmp in self.server.online.copy():
                        if tmp.uid != uid:
                            continue
                        tmp.send(msg)
                        break
            else:
                for tmp in self.server.online.copy():
                    if tmp.room == msg[1]["rid"]:
                        tmp.send(msg)

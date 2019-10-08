from modules.base_module import Module

class_name = "Mail"

class Mail(Module):
    prefix = "mail"

    def __init__(self, server):
        self.server = server
        self.commands = {"gc": self.get_collection}

    def get_collection(self, msg, client):
        client.send(["mail.gc", {"in": [], "out": []}])

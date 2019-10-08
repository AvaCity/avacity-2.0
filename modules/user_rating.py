from modules.base_module import Module

class_name = "UserRating"


class UserRating(Module):
    prefix = "ur"

    def __init__(self, server):
        self.server = server
        self.commands = {"get": self.get, "gar": self.get_activity}

    def get(self, msg, client):
        client.send(["ur.get", {"bt": []}])

    def get_activity(self, msg, client):
        client.send(["ur.gar", {"bt": []}])

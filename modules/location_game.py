from modules.base_module import Module

class_name = "LocationGame"


class LocationGame(Module):
    prefix = "lg"

    def __init__(self, server):
        self.server = server
        self.commands = {"lst": self.game_list}

    def game_list(self, msg, client):
        client.send(["lg.lst", {"glst": []}])

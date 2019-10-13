from modules.location import Location, gen_plr
import const
import common

class_name = "Outside"


class Outside(Location):
    prefix = "o"

    def __init__(self, server):
        super().__init__(server)
        self.commands.update({"r": self.room, "gr": self.get_room})

    def get_room(self, msg, client):
        online = self.server.online.copy()
        num = 1
        while True:
            i = 0
            for tmp in online:
                if tmp.room == f"{msg[2]['lid']}_{msg[2]['gid']}_{num}":
                    i += 1
            if i >= const.ROOM_LIMIT:
                num += 1
            else:
                break
        room = f"{msg[2]['lid']}_{msg[2]['gid']}_{num}"
        if client.room:
            prefix = common.get_prefix(client.room)
            for tmp in self.server.online.copy():
                if tmp.room != client.room or tmp.uid == client.uid:
                    continue
                client.send([prefix+".r.lv", {"uid": client.uid}])
                client.send([client.room, client.uid], type_=17)
        client.room = room
        client.position = (-1.0, -1.0)
        client.action_tag = ""
        client.state = 0
        client.dimension = 4
        plr = gen_plr(client, self.server)
        for tmp in self.server.online.copy():
            if tmp.room != client.room:
                continue
            tmp.send(["o.r.jn", {"plr": plr}])
            tmp.send([client.room, client.uid], type_=16)
        client.send(["o.gr", {"rid": client.room}])

    def room(self, msg, client):
        subcommand = msg[1].split(".")[2]
        if subcommand == "info":
            rmmb = []
            room = msg[0]
            for tmp in self.server.online.copy():
                if tmp.room != room:
                    continue
                rmmb.append(gen_plr(tmp, self.server))
            client.send(["o.r.info", {"rmmb": rmmb, "evn": None}])
        else:
            super().room(msg, client)

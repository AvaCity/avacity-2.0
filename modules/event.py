import time
import threading
from modules.base_module import Module

class_name = "Event"


class Event(Module):
    prefix = "ev"

    def __init__(self, server):
        self.server = server
        self.commands = {"get": self.get_events, "gse": self.get_self_event,
                         "crt": self.create_event,
                         "cse": self.close_self_event,
                         "evi": self.get_event_info}
        self.events = {}
        thread = threading.Thread(target=self._background)
        thread.daemon = True
        thread.start()

    def get_events(self, msg, client):
        evts = []
        for uid in self.events:
            apprnc = self.server.get_appearance(uid)
            if not apprnc:
                continue
            evts.append(self._get_event(uid))
        client.send(["ev.get", {"c": -1, "tg": "", "evlst": evts}])

    def get_self_event(self, msg, client):
        if client.uid not in self.events:
            return client.send(["ev.gse", {}])
        event = self.events[client.uid]
        client.send(["ev.gse", {"ev": self._get_event(event, client.uid)}])

    def create_event(self, msg, client):
        if client.uid in self.events:
            return
        ev = msg[2]["ev"]
        duration = int(msg[2]["evdrid"].split("eventDuration")[1])
        if ev["r"] > 13:
            user_data = self.server.get_user_data(client.uid)
            if user_data["role"] < 2:
                return
        event = {"name": ev["tt"], "description": ev["ds"],
                 "start": int(time.time()), "uid": client.uid,
                 "finish": int(time.time()+duration*60),
                 "min_lvl": ev["ml"], "category": ev["c"], "active": ev["ac"],
                 "rating": ev["r"]}
        event["location"] = ev["l"]
        self.events[client.uid] = event
        user_data = self.server.get_user_data(client.uid)
        client.send(["ev.crt", {"ev": self._get_event(client.uid),
                                "res": {"gld": user_data["gld"],
                                        "slvr": user_data["slvr"],
                                        "enrg": user_data["enrg"],
                                        "emd": user_data["emd"]},
                                "evtg": []}])

    def close_self_event(self, msg, client):
        if client.uid not in self.events:
            return
        del self.events[client.uid]
        client.send(["ev.cse", {}])

    def get_event_info(self, msg, client):
        id_ = str(msg[2]["id"])
        if id_ not in self.events:
            return
        event = self._get_event(id_)
        apprnc = self.server.get_appearance(id_)
        clths = self.server.get_clothes(id_, type_=2)
        client.send(["ev.evi", {"ev": event,
                                "plr": {"uid": id_, "apprnc": apprnc,
                                        "clths": clths},
                                "id": int(id_)}])

    def _get_event(self, uid):
        event = self.events[uid]
        apprnc = self.server.get_appearance(uid)
        type_ = 0 if event["location"] == "livingroom" else 1
        return {"tt": event["name"], "ds": event["description"],
                "st": event["start"], "ft": event["finish"], "uid": uid,
                "l": event["location"], "id": int(uid), "unm": apprnc["n"],
                "ac": event["active"], "c": event["category"],
                "ci": 0, "fo": False, "r": event["rating"], "lg": 30,
                "tp": type_, "ml": event["min_lvl"]}

    def _background(self):
        while True:
            for uid in self.events.copy():
                if time.time() - self.events[uid]["finish"] > 0:
                    del self.events[uid]
            time.sleep(60)

from datetime import datetime

XML = """<?xml version="1.0"?>
<cross-domain-policy>
<allow-access-from domain="*" to-ports="*" />
</cross-domain-policy>
""".encode()

MAX_NAME_LEN = 20
ROOM_LIMIT = 15
EVENT_ROOM_LIMIT = 40
FREE_GOLD = True

room_items = [{"tpid": "wall15", "d": 3, "oid": 1, "x": 0.0, "y": 0.0,
               "z": 0.0},
              {"tpid": "wall15", "d": 5, "oid": 2, "x": 13.0, "y": 0.0,
               "z": 0.0},
              {"tpid": "floor4", "d": 5, "oid": 3, "x": 0.0, "y": 0.0,
               "z": 0.0},
              {"tpid": "door4", "d": 3, "oid": 4, "x": 3.0, "y": 0.0,
               "z": 0.0, "rid": "outside"}]
campaigns = []

clans = False
mobile = True
fortune2 = True
professions = True
reputation = False

if clans:
    campaigns.append({"st": 1, "v": 1,
                      "cil": [{"sc": 0, "gl": 0, "si": 0, "id": 8151,
                               "tid": "clans", "cid": 643},
                              {"sc": 0, "gl": 0, "si": 0, "id": 8152,
                               "tid": "clanRating_off", "cid": 643}],
                      "id": 643, "iu": "", "tp": 9,
                      "ed": datetime(2047, 5, 31, 11, 46)})
if mobile:
    campaigns.append({"st": 1, "v": 1,
                      "cil": [{"sc": 0, "gl": 0, "si": 0, "id": 2514,
                               "tid": "mobile", "cid": 316}],
                      "id": 316, "iu": "", "tp": 9,
                      "ed": datetime(2022, 7, 31, 2, 0)})
if fortune2:
    campaigns.append({"st": 2, "v": 1,
                      "cil": [{"sc": 0, "gl": 0, "si": 0, "id": 2434,
                               "tid": "fortune2", "cid": 299}],
                      "id": 299, "iu": "", "tp": 9,
                      "ed": datetime(2030, 10, 31, 2, 0)})
if professions:
    campaigns.append({"st": 1, "v": 1,
                      "cil": [{"sc": 0, "gl": 0, "si": 0, "id": 1110,
                               "tid": "professions", "cid": 114},
                              {"sc": 0, "gl": 0, "si": 0, "id": 1111,
                               "tid": "grdnr", "cid": 114},
                              {"sc": 0, "gl": 0, "si": 0, "id": 1112,
                               "tid": "jntr", "cid": 114},
                              {"sc": 0, "gl": 0, "si": 0, "id": 1577,
                               "tid": "vsgst", "cid": 114},
                              {"sc": 0, "gl": 0, "si": 0, "id": 1578,
                               "tid": "phtghr", "cid": 114}],
                      "id": 114, "iu": "", "tp": 9,
                      "ed": datetime(2015, 8, 27, 2, 0)})
if reputation:
    campaigns.append({"st": 1, "v": 1,
                      "cil": [{"sc": 0, "gl": 0, "si": 0, "id": 1109,
                               "tid": "reputation", "cid": 113}],
                      "id": 113, "iu": "", "tp": 9,
                      "ed": datetime(2015, 8, 18, 2, 0)})

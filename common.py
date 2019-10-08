import logging


def get_prefix(location):
    prefix = location.split("_")[0]
    if prefix in ["cafe", "club", "street", "yard", "skiResort", "publicBeach",
                  "couturier", "ballroom", "park", "canyon", "salon",
                  "photoSalon", "weddingBeach", "iceRink", "podium", "garden",
                  "avaCitySchool", "islBeach", "avaBirthday2016Beach"]:
        return "o"
    elif prefix == "house":
        return "h"
    elif prefix == "work":
        return "w"
    else:
        logging.warning(f"Location prefix {prefix} not found")
        return "o"

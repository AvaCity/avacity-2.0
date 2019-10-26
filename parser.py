from lxml import etree


class Parser():
    def __init__(self):
        self.parser = etree.XMLParser(remove_comments=True)
        self.apprnc_map = ["sc", "et", "brt", "at", "ht", "bt", "sh", "rg",
                           "ss", "pt", "fat", "fft"]

    def parse_clothes(self):
        clothes = {"boy": {}, "girl": {}}
        for filename in ["boyClothes.xml", "girlClothes.xml"]:
            if filename == "boyClothes.xml":
                gender = "boy"
            else:
                gender = "girl"
            doc = etree.parse("config_all_ru/inventory/"+filename,
                              parser=self.parser)
            root = doc.getroot()
            for category in root.findall(".//category[@logCategory2]"):
                name = gender+category.attrib["logCategory2"][1:]
                clothes[gender][name] = self.parse_clothes_category(category)
        return clothes

    def parse_clothes_category(self, category):
        tmp = {}
        for item in category:
            if item.tag == "category":
                tmp.update(self.parse_clothes_category(item))
                continue
            name = item.attrib["id"]
            tmp[name] = {}
            for attr in ["gold", "rating", "silver"]:
                if attr in item.attrib:
                    tmp[name][attr] = int(item.attrib[attr])
                else:
                    tmp[name][attr] = 0
        return tmp

    def parse_cloth_sets(self):
        doc = etree.parse("config_all_ru/inventory/extend/clothesSets.xml",
                          parser=self.parser)
        root = doc.getroot()
        sets = {"boy": {}, "girl": {}}
        for set_ in root.findall(".//clothesSet"):
            id_ = set_.attrib["id"]
            gender = set_.attrib["gender"]
            sets[gender][id_] = []
            for item in set_.findall("item"):
                sets[gender][id_].append(item.attrib["itemId"])
        return sets

    def parse_furniture(self):
        furniture = {}
        for filename in ["furniture.xml", "kitchen.xml", "bathroom.xml",
                         "decor.xml", "present.xml", "roomLayout.xml"]:
            doc = etree.parse(f"config_all_ru/inventory/{filename}",
                              parser=self.parser)
            root = doc.getroot()
            for item in root.findall(".//item"):
                name = item.attrib["id"]
                furniture[name] = {}
                for attr in ["gold", "rating", "silver"]:
                    if attr in item.attrib:
                        furniture[name][attr] = int(item.attrib[attr])
                    else:
                        furniture[name][attr] = 0
        return furniture

    def parse_conflicts(self):
        doc = etree.parse("config_all_ru/inventory/extend/clothesRules.xml",
                          parser=self.parser)
        root = doc.getroot()
        conflicts = []
        for rule in root.findall(".//rule"):
            conflicts.append([rule.attrib["category1"],
                              rule.attrib["category2"]])
        return conflicts

    def parse_privileges(self):
        doc = etree.parse("config_all_ru/modules/acl.xml", parser=self.parser)
        root = doc.getroot()
        privileges = {}
        for item in root.findall(".//privilege"):
            privileges[item.attrib["name"]] = int(item.attrib["minAuthority"])
        return privileges

    def parse_game_items(self):
        doc = etree.parse("config_all_ru/inventory/game.xml",
                          parser=self.parser)
        root = doc.getroot()
        items = {}
        for category in root.findall(".//category"):
            cat_name = category.attrib["id"]
            items[cat_name] = {}
            for item in category.findall(".//item"):
                name = item.attrib["id"]
                items[cat_name][name] = {}
                for attr in ["gold", "silver", "saleSilver"]:
                    if attr in item.attrib:
                        items[cat_name][name][attr] = int(item.attrib[attr])
                    else:
                        if attr == "saleSilver":
                            continue
                        items[cat_name][name][attr] = 0
        return items

    def parse_achievements(self):
        doc = etree.parse("config_all_ru/modules/achievements.xml",
                          parser=self.parser)
        root = doc.getroot()
        ac = []
        for item in root.findall(".//achievement"):
            ac.append(item.attrib["id"])
        return ac

    def parse_trophies(self):
        doc = etree.parse("config_all_ru/modules/trophies.xml",
                          parser=self.parser)
        root = doc.getroot()
        tr = []
        for item in root.findall(".//trophy"):
            tr.append(item.attrib["id"])
        return tr

    def parse_craft(self):
        doc = etree.parse("config_all_ru/modules/craft.xml",
                          parser=self.parser)
        root = doc.getroot()
        items = {}
        for item in root.findall(".//craftedItem"):
            id_ = item.attrib["itemId"]
            items[id_] = {"items": {}}
            if "craftedId" in item.attrib:
                items[id_]["craftedId"] = item.attrib["craftedId"]
                items[id_]["count"] = int(item.attrib["count"])
            for tmp in item.findall("component"):
                itemId = tmp.attrib["itemId"]
                count = int(tmp.attrib["count"])
                items[id_]["items"][itemId] = count
        return items

    def parse_appearance(self):
        doc = etree.parse("config_all_ru/avatarAppearance/appearance.xml",
                          parser=self.parser)
        root = doc.getroot()
        apprnc = {"boy": {}, "girl": {}}
        for gender in ["boy", "girl"]:
            el = root.find(gender)
            for category in el.findall("category"):
                id_ = int(category.attrib["id"])
                map_ = self.apprnc_map[id_]
                apprnc[gender][map_] = {}
                for item in category.findall("item"):
                    kind = int(item.attrib["kind"])
                    apprnc[gender][map_][kind] = {}
                    for attr in ["silver", "gold", "brush", "visagistLevel"]:
                        if attr in item.attrib:
                            value = int(item.attrib[attr])
                            apprnc[gender][map_][kind][attr] = value
                    for attr in ["salonOnly"]:
                        if attr in item.attrib:
                            apprnc[gender][map_][kind][attr] = True
        return apprnc

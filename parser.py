from lxml import etree


class Parser():
    def __init__(self):
        self.parser = etree.XMLParser(remove_comments=True)

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

    def parse_priveleges(self):
        doc = etree.parse("config_all_ru/modules/acl.xml", parser=self.parser)
        root = doc.getroot()
        priveleges = {}
        for item in root.findall(".//privilege"):
            priveleges[item.attrib["name"]] = int(item.attrib["minAuthority"])
        return priveleges

    def parse_game_items(self):
        doc = etree.parse("config_all_ru/inventory/game.xml",
                          parser=self.parser)
        root = doc.getroot()
        items = {}
        for item in root.findall(".//item"):
            name = item.attrib["id"]
            items[name] = {}
            for attr in ["gold", "silver"]:
                if attr in item.attrib:
                    items[name][attr] = int(item.attrib[attr])
                else:
                    items[name][attr] = 0
        return items

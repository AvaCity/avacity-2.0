import os
import json
import time
import shutil
import asyncio
import zipfile
import hashlib
import configparser
import aiohttp
from lxml import etree

download_url = "http://cdn-sp.tortugasocial.com/avataria-ru/"
versions = {}
with open("update.json", "r") as f:
    config = json.load(f)


async def main():
    async with aiohttp.ClientSession() as session:
        async with session.get(download_url+"versions.json") as resp:
            data = await resp.json()
            print("Got versions.json")
    tasks = []
    loop = asyncio.get_event_loop()
    async with aiohttp.ClientSession() as session:
        for item in data:
            if data[item] in item or "island" in item.lower():
                continue
            if item in config["ignore"]:
                continue
            tasks.append(loop.create_task(download_file(item, data[item],
                                                        session)))
        await asyncio.wait(tasks)
    print("Processing config")
    if "data/config_all_ru.zip" not in versions:
        print("Error - config_all_ru.zip not found")
    else:
        await process_config(versions["data/config_all_ru.zip"])
    async with aiohttp.ClientSession() as session:
        for filename in ["pnz-city.swf", "pnz-city-container.swf"]:
            async with session.get(f"{download_url}app/{filename}") as resp:
                if resp.status != 200:
                    print(f"Can't get {filename}")
                    return
                content = await resp.read()
            with open(f"files/{filename}", "wb") as f:
                f.write(content)
            print(f"Got {filename}")
        for filename in config["misc"]:
            tmp = filename.split("/")
            tmp.pop()
            folder = "/".join(tmp)
            async with session.get(f"{download_url}{filename}") as resp:
                if resp.status != 200:
                    print("Can't get {filename}")
                    return
                content = await resp.read()
            os.makedirs(f"files/{folder}", exist_ok=True)
            with open(f"files/{filename}", "wb") as f:
                f.write(content)
            print(f"Got {filename}")
    webconfig = configparser.ConfigParser()
    webconfig.read("web.ini")
    webconfig["webserver"]["update_time"] = str(int(time.time()))
    with open("web.ini", "w") as f:
        webconfig.write(f)


async def process_config(version):
    directory = "config_all_ru"
    if os.path.exists(directory):
        shutil.rmtree(directory)
    os.makedirs(directory)
    file = f"files/data/config_all_ru_{version}.zip"
    with zipfile.ZipFile(file, 'r') as zip_ref:
        zip_ref.extractall(directory)
    parser = etree.XMLParser(remove_comments=True)
    for filename in ["boyClothes", "girlClothes"]:
        doc = etree.parse(f"{directory}/inventory/{filename}.xml",
                          parser=parser)
        root = doc.getroot()
        for el in root.xpath("//item[@canBuy='0']"):
            del el.attrib["canBuy"]
        for el in root.xpath("//item[@wedding='1']"):
            del el.attrib["wedding"]
        for el in root.xpath("//item[@holiday]"):
            del el.attrib["holiday"]
        for el in root.xpath("//item[@clanOnly='1']"):
            del el.attrib["clanOnly"]
        string = etree.tostring(root, pretty_print=True,
                                xml_declaration=True).decode()
        with open(f"{directory}/inventory/{filename}.xml", "w") as f:
            f.write(string)
    doc = etree.parse(f"{directory}/avatarAppearance/appearance.xml",
                      parser=parser)
    root = doc.getroot()
    for el in root.xpath("//item[@clanOnly='1']"):
        del el.attrib["clanOnly"]
    string = etree.tostring(root, pretty_print=True,
                            xml_declaration=True).decode()
    with open(f"{directory}/avatarAppearance/appearance.xml", "w") as f:
        f.write(string)
    doc = etree.parse(f"{directory}/inventory/stickerPack.xml",
                      parser=parser)
    root = doc.getroot()
    for el in root.xpath("//item"):
        el.attrib["vipOnly"] = "1"
    string = etree.tostring(root, pretty_print=True,
                            xml_declaration=True).decode()
    with open(f"{directory}/inventory/stickerPack.xml", "w") as f:
        f.write(string)
    for filename in ["furniture", "kitchen", "bathroom", "decor",
                     "roomLayout"]:
        doc = etree.parse(f"{directory}/inventory/{filename}.xml",
                          parser=parser)
        root = doc.getroot()
        for el in root.findall(".//item[@canBuy='0']"):
            del el.attrib["canBuy"]
        string = etree.tostring(root, pretty_print=True,
                                xml_declaration=True).decode()
        with open(f"{directory}/inventory/{filename}.xml", "w") as f:
            f.write(string)
        tasks = []
        loop = asyncio.get_event_loop()
        async with aiohttp.ClientSession() as session:
            for el in root.findall(".//item"):
                name = el.attrib["name"]
                folder = filename
                if folder == "roomLayout":
                    if name == "RoomBase":
                        continue
                    folder = "house"
                elif folder == "decor":
                    parent = el.getparent()
                    if parent.attrib["id"] == "achievementsDecor":
                        continue
                url = f"{download_url}swf/furniture/{folder}/{name}.swf"
                tasks.append(loop.create_task(download_furniture(url,
                                                                 session)))
            await asyncio.wait(tasks)
    shutil.copyfile("files/avacity_ru.xml",
                    "config_all_ru/translation/avacity_ru.xml")
    z = zipfile.ZipFile("files/data/config_all_ru.zip", mode="w")
    for root, dirs, files in os.walk(directory):
        for file in files:
            z.write(os.path.join(root, file),
                    arcname=os.path.join(root,
                                         file).split("config_all_ru/")[1])
    z.close()
    with open("files/data/config_all_ru.zip", mode="rb") as f:
        hash_ = hashlib.md5(f.read()).hexdigest()
    os.rename("files/data/config_all_ru.zip",
              f"files/data/config_all_ru_{hash_}.zip")
    versions["data/config_all_ru.zip"] = hash_
    with open("files/versions.json", "w") as f:
        f.write(json.dumps(versions))


async def download_file(filename, version, session):
    if "music" in filename:
        final = filename
    else:
        final = filename.split(".")[0]+f"_{version}."+filename.split(".")[1]
    if os.path.exists("files/"+final):
        if "music" not in filename:
            versions[filename] = version
        return
    async with session.get(download_url+final) as resp:
        if resp.status != 200:
            print(f"Can't get {final}")
            return
        content = await resp.read()
    tmp = filename.split("/")
    tmp.pop()
    folder = "/".join(tmp)
    os.makedirs("files/"+folder, exist_ok=True)
    with open("files/"+final, "wb") as f:
        f.write(content)
    if "music" not in filename:
        versions[filename] = version
    print(f"Got {final}")


async def download_furniture(url, session):
    folder = url.split("/")[-2]
    final = f"swf/furniture/{folder}/{url.split('/')[-1]}"
    if os.path.exists("files/"+final):
        return
    async with session.get(url) as resp:
        if resp.status != 200:
            print(f"Can't get {url.split('/')[-2]}/{url.split('/')[-1]}")
            return
        content = await resp.read()
    os.makedirs(f"files/swf/furniture/{folder}", exist_ok=True)
    with open("files/"+final, "wb") as f:
        f.write(content)
    print(f"Got {url.split('/')[-2]}/{url.split('/')[-1]}")

asyncio.run(main())

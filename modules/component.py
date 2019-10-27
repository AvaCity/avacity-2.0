import time
from modules.base_module import Module
import utils.bot_common

class_name = "Component"


class Component(Module):
    prefix = "cp"

    def __init__(self, server):
        self.server = server
        self.commands = {"cht": self.chat, "m": self.moderation,
                         "ms": self.message}
        self.privileges = self.server.parser.parse_privileges()
        self.mute = {}

    def chat(self, msg, client):
        subcommand = msg[1].split(".")[2]
        if subcommand == "sm":  # send message
            msg.pop(0)
            if client.uid in self.mute:
                time_left = self.mute[client.uid]-time.time()
                if time_left > 0:
                    client.send(["cp.ms.rsm", {"txt": "У вас мут ещё на "
                                                      f"{int(time_left)} "
                                                      "секунд"}])
                    return
                else:
                    del self.mute[client.uid]
            if msg[1]["msg"]["cid"]:
                for uid in msg[1]["msg"]["cid"].split("_"):
                    for tmp in self.server.online.copy():
                        if tmp.uid != uid:
                            continue
                        tmp.send(msg)
                        break
            else:
                if "msg" in msg[1]["msg"] and \
                   msg[1]["msg"]["msg"].startswith("!"):
                    return self.system_command(msg[1]["msg"]["msg"], client)
                for tmp in self.server.online.copy():
                    if tmp.room == msg[1]["rid"]:
                        tmp.send(msg)

    def moderation(self, msg, client):
        subcommand = msg[1].split(".")[2]
        if subcommand == "ar":  # access request
            user_data = self.server.get_user_data(client.uid)
            if user_data["role"] >= self.privileges[msg[2]["pvlg"]]:
                success = True
            else:
                success = False
            client.send(["cp.m.ar", {"pvlg": msg[2]["pvlg"],
                                     "sccss": success}])
        elif subcommand == "bu":
            uid = msg[2]["uid"]
            return self.ban_user(uid, client)

    def ban_user(self, uid, client):
        user_data = self.server.get_user_data(client.uid)
        if user_data["role"] < self.privileges["AVATAR_BAN"]:
            return
        uid_user_data = self.server.get_user_data(uid)
        if uid_user_data["role"] > 2:
            return
        redis = self.server.redis
        banned = redis.get(f"uid{uid}:banned")
        if banned:
            client.send(["cp.ms.rsm", {"txt": f"У UID {uid} уже есть бан"
                                              f"от администратора {banned}"}])
            return
        redis.set(f"uid:{uid}:banned", client.uid)
        ban_time = int(time.time()*1000)
        redis.set(f"uid:{uid}:ban_time", ban_time)
        for tmp in self.server.online.copy():
            if tmp.uid != uid:
                continue
            tmp.send([10, "User is banned",
                      {"duration": 999999, "banTime": ban_time,
                       "notes": "", "reviewerId": client.uid, "reasonId": 0,
                       "unbanType": "none", "leftTime": 0, "id": None,
                       "reviewState": 1, "userId": uid,
                       "moderatorId": client.uid}], type_=2)
            tmp.connection.shutdown(2)
            break
        client.send(["cp.ms.rsm", {"txt": f"UID {uid} получил бан"}])

    def unban_user(self, uid, client):
        user_data = self.server.get_user_data(client.uid)
        if user_data["role"] < self.privileges["AVATAR_BAN"]:
            return
        redis = self.server.redis
        banned = redis.get(f"uid:{uid}:banned")
        if not banned:
            client.send(["cp.ms.rsm", {"txt": f"У UID {uid} нет бана"}])
            return
        redis.delete(f"uid:{uid}:banned")
        redis.delete(f"uid:{uid}:ban_time")
        client.send(["cp.ms.rsm", {"txt": f"Снят бан UID {uid} от "
                                          f"администратора {banned}"}])

    def message(self, msg, client):
        subcommand = msg[1].split(".")[2]
        if subcommand == "smm":  # send moderator message
            user_data = self.server.get_user_data(client.uid)
            if user_data["role"] < self.privileges["MESSAGE_TO_USER"]:
                return
            uid = msg[2]["rcpnts"]
            message = msg[2]["txt"]
            sccss = False
            for tmp in self.server.online.copy():
                if tmp.uid == uid:
                    tmp.send(["cp.ms.rmm", {"sndr": client.uid,
                                            "txt": message}])
                    sccss = True
                    break
            client.send(["cp.ms.smm", {"sccss": sccss}])

    def system_command(self, msg, client):
        command = msg[1:]
        if " " in command:
            command = command.split(" ")[0]
        if command == "ssm":
            return self.send_system_message(msg, client)
        elif command == "mute":
            return self.mute_player(msg, client)
        elif command == "ban":
            uid = msg.split()[1]
            return self.ban_user(uid, client)
        elif command == "unban":
            uid = msg.split()[1]
            return self.unban_user(uid, client)
        elif command == "reset":
            uid = msg.split()[1]
            return self.reset_user(uid, client)

    def send_system_message(self, msg, client):
        user_data = self.server.get_user_data(client.uid)
        if user_data["role"] < self.privileges["SEND_SYSTEM_MESSAGE"]:
            return self.no_permission(client)
        message = msg.split("!ssm ")[1]
        for tmp in self.server.online.copy():
            tmp.send(["cp.ms.rsm", {"txt": message}])

    def mute_player(self, msg, client):
        user_data = self.server.get_user_data(client.uid)
        if user_data["role"] < self.privileges["CHAT_BAN"]:
            return self.no_permission(client)
        uid = msg.split()[1]
        minutes = int(msg.split()[2])
        apprnc = self.server.get_appearance(uid)
        if not apprnc:
            client.send(["cp.ms.rsm", {"txt": "Игрок не найден"}])
            return
        self.mute[uid] = time.time()+minutes*60
        for tmp in self.server.online.copy():
            if tmp.uid != uid:
                continue
            tmp.send(["cp.m.bccu", {"bcu": {"notes": "", "reviewerId": "0",
                                            "mid": "0", "id": None,
                                            "reviewState": 1, "userId": uid,
                                            "mbt": int(time.time()*1000),
                                            "mbd": minutes,
                                            "categoryId": 14}}])
            break
        client.send(["cp.ms.rsm", {"txt": f"Игроку {apprnc['n']} выдан мут "
                                          f"на {minutes} минут"}])

    def reset_user(self, uid, client):
        user_data = self.server.get_user_data(client.uid)
        if user_data["role"] < 5:
            return self.no_permission(client)
        apprnc = self.server.get_appearance(uid)
        if not apprnc:
            client.send(["cp.ms.rsm", {"txt": "Аккаунт и так сброшен"}])
            return
        for tmp in self.server.online.copy():
            if tmp.uid != uid:
                continue
            tmp.connection.shutdown(2)
            break
        utils.bot_common.reset_account(self.server.redis, uid)
        client.send(["cp.ms.rsm", {"txt": f"Аккаунт {uid} был сброшен"}])

    def no_permission(self, client):
        client.send(["cp.ms.rsm", {"txt": "У вас недостаточно прав, чтобы "
                                          "выполнить эту команду"}])

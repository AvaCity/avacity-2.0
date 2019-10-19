import string
import random


def random_string(string_length=20):
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for i in range(string_length))


def new_account(redis):
    redis.incr("uids")
    uid = redis.get("uids")
    while True:
        passwd = random_string()
        if redis.get(f"auth:{passwd}"):
            continue
        break
    pipe = redis.pipeline()
    pipe.set(f"auth:{passwd}", uid)
    pipe.set(f"uid:{uid}:slvr", 1000)
    pipe.set(f"uid:{uid}:gld", 6)
    pipe.set(f"uid:{uid}:enrg", 100)
    pipe.set(f"uid:{uid}:exp", 500000)
    pipe.set(f"uid:{uid}:emd", 0)
    pipe.set(f"uid:{uid}:lvt", 0)
    pipe.sadd(f"uid:{uid}:items", "blackMobileSkin")
    pipe.rpush(f"uid:{uid}:items:blackMobileSkin", "gm", 1)
    pipe.sadd(f"rooms:{uid}", "livingroom")
    pipe.rpush(f"rooms:{uid}:livingroom", "#livingRoom", 1)
    for i in range(1, 6):
        pipe.sadd(f"rooms:{uid}", i)
        pipe.rpush(f"rooms:{uid}:{i}", f"Комната {i}", 2)
    pipe.execute()
    return (uid, passwd)

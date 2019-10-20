import configparser
import redis
from aiogram import Bot, Dispatcher, executor, types
import bot_common
config = configparser.ConfigParser()
config.read('bot.ini')
TOKEN = config["bot"]["tg_token"]
issues_link = "https://github.com/AvaCity/avacity-2.0/issues"

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
r = redis.Redis(decode_responses=True)


@dp.message_handler(commands=["start", "help"])
async def send_welcome(message: types.Message):
    await message.reply("Привет!\nЯ бот для выдачи паролей для сервера на "
                        "базе исходного кода AvaCity 2.0! Администрация "
                        "этого сервера никак не связана с AvaCity.\n"
                        "Чтобы получить пароль, введите команду /password\n"
                        "Смена пароля - /change_password\nСброс аккаунта - "
                        f"/reset\nОбо всех багах писать на {issues_link}\n"
                        "Приятной игры!")


@dp.message_handler(commands=["password"])
async def password(message: types.Message):
    passwd = r.get(f"tg:{message.from_user.id}")
    if passwd:
        uid = r.get(f"auth:{passwd}")
    else:
        uid, passwd = bot_common.new_account(r)
        r.set(f"tg:{message.from_user.id}", passwd)
    await message.reply(f"Ваш логин: {uid}\nВаш пароль: {passwd}")


@dp.message_handler(commands=["change_password"])
async def change_password(message: types.Message):
    passwd = r.get(f"tg:{message.from_user.id}")
    if not passwd:
        return await message.reply("Ваш аккаунт не создан")
    while True:
        new_passwd = bot_common.random_string()
        if r.get(f"auth:{new_passwd}"):
            continue
        break
    uid = r.get(f"auth:{passwd}")
    r.delete(f"auth:{passwd}")
    r.set(f"auth:{new_passwd}", uid)
    r.set(f"tg:{message.from_user.id}", new_passwd)
    await message.reply(f"Ваш новый пароль: {new_passwd}")


@dp.message_handler(commands=["reset"])
async def reset(message: types.Message):
    passwd = r.get(f"tg:{message.from_user.id}")
    if not passwd:
        return await message.reply("Ваш аккаунт не создан")
    uid = r.get(f"auth:{passwd}")
    bot_common.reset_account(r, uid)
    await message.reply(f"Ваш аккаунт был сброшен")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

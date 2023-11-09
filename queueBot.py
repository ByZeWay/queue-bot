import telebot
from telebot import types

from Requests import ReqParser

with open('token.txt') as file:
    lines = [line.rstrip() for line in file]
    token = lines[0]

bot=telebot.TeleBot(token)

parser = ReqParser(bot)

@bot.message_handler(func=lambda message: not message.text.startswith('/'))
def handle_text(message):
    if message.from_user.id in parser.setNameList:
        name = message.text
        bot.reply_to(message, "отображаемое имя установлено")
        parser.setNameList.remove(message.from_user.id)

@bot.message_handler(commands=['start'])
def start_message(message):
    markup = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton("Возможности", callback_data="possibility")
    button2 = types.InlineKeyboardButton("Команды", callback_data="commands")
    markup.row(button1, button2)
    bot.send_message(message.chat.id,"Привет! Я бот для составления очередей.\nТы можешь воспользоваться следующими "
                                     "командами, что бы более подробно узнать что я умею:", reply_markup=markup)

@bot.message_handler(commands=['help'])
def help_message(message):
    parser.commandsList(message)

@bot.message_handler(commands=['create'])
def create_message(message):
    parser.createCommand(message)

@bot.message_handler(commands=['delete'])
def delete_message(message):
    parser.deleteCommand(message)

@bot.message_handler(commands=['member'])
def member_message(message):
    parser.memberCommand(message)

@bot.message_handler(commands=['show'])
def show_message(message):
    parser.showCommand(message)

@bot.callback_query_handler(func = lambda callback: True)
def callback_message(callback):
    if "createNum_" in callback.data:
        numStr = callback.data.strip("createNum_")
        numSubj = int(numStr)
        bot.send_message(callback.message.chat.id, "Создана очередь по " + parser.subjList[numSubj])

    elif "deleteNum_" in callback.data:
        numStr = callback.data.strip("deleteNum_")
        numSubj = int(numStr)
        bot.send_message(callback.message.chat.id, "Удалена очередь по " + parser.subjList[numSubj])

    elif "showNum_" in callback.data:
        numStr = callback.data.strip("showNum_")
        numSubj = int(numStr)
        bot.send_message(callback.message.chat.id, "Очередь по " + parser.subjList[numSubj] + ":\n")

    else:
        match callback.data:
            case "help_member":
                callback.message.from_user = callback.from_user
                parser.memberCommand(callback.message)
            case "help_show":
                parser.showCommand(callback.message)
            case "help_delete":
                parser.deleteCommand(callback.message)
            case "help_create":
                parser.createCommand(callback.message)
            case "commands":
                parser.commandsList(callback.message)
            case "possibility":
                bot.send_message(callback.message.chat.id, "Бот, который поможет тебе не потеряться в бесконечных "
                                                           "очередях.🤡\n С его помощью ты можешь создать очередь и "
                                                           "добавиться в нее, вывести список добавленных пользователей."
                                                           " Бот позволяет не только выйти из очереди, если ты захотел "
                                                           "пойти на допсу, но и поменяться с другим человеком, если, "
                                                           "конечно, он будет на это согласен😈")
            case "member_cancel" | "show_cancel" | "create_cancel" | "delete_cancel":
                bot.delete_message(callback.message.chat.id, callback.message.id)
            case "member_add":
                if callback.from_user.id in parser.sendedMemberList:
                    bot.send_message(callback.message.chat.id, "Введи имя. которое будет отображаться при выводе сообщений:")
                    parser.setNameList.append(callback.from_user.id)
                    parser.sendedMemberList.remove(callback.from_user.id)

            case _:
                return

bot.infinity_polling()
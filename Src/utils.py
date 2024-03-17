import re
import time

import telebot

from Entities.Queue import Queue
from Requests.RuntimeInfoManager import RuntimeInfoManager
from Services.QueueService import QueueService


def checkNumPlace(message):
        try:
            entryNum = int(message)
            if entryNum <= 0:
                entryNum = -1
            return entryNum
        except:
            return -1


def removeBlank(string: str) -> str:
    return ' '.join(string.split())


def checkSubjectTitle(title: str) -> bool:
    return bool(re.fullmatch('([A-Za-zА-Яа-яёЁ]+ ?)+', title)) and (len(title) <= 30)


def checkMemberName(name: str) -> bool:
    return bool(re.fullmatch('([A-Za-zА-Яа-яёЁ]+[ \'-]?)+', name)) and (len(name) <= 30)


def checkMessage(message: telebot.types.Message, chatId=None, timeout=5) -> bool:
    if timeout is not None and time.time() - message.date > timeout:
        print(f'failed timeout for \'{message.text}\'. time.time()={time.time()}, message.date={message.date}')
        return False
    if chatId is not None and (message.chat.id != chatId):
        print(f'failed chatId for \'{message.text}\'')
        return False
    return True


def formQueueText(queue: Queue):
    qList = {}
    for qmember in queue.members:
        val =  " - " + qmember.member.name + "\n"
        qList [qmember.placeNumber] = val

    sortedQ = {k: v for k, v in sorted(qList.items())}
    resStr = ''
    for q in sortedQ:
        resStr += str(q) + sortedQ[q]

    return "Очередь по " + queue.subject.title + ":\n" + resStr

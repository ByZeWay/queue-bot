import pytest

import time
import os

import telebot
from telebot import types
from pyrogram import Client
from dotenv import load_dotenv

from DbUtils.db import Database

load_dotenv()
bot_id = int(os.getenv('bot_id'))
chat_id = int(os.getenv('chat_id'))

DELAY = 0.8

def waitBotMessage(client, timeout = 30):
    startTime = time.time()
    while True:
        message = next(client.get_chat_history(chat_id, limit=1))
        if message.from_user.id == bot_id:
            break
        if time.time() - startTime > timeout:
            assert False
            break
        time.sleep(DELAY)
    return message

def sendAndWaitAny(client, text: str):
    message = client.send_message(chat_id, text)
    waitBotMessage(client)
    return message

def checkResponce(client, text: str, responceText: str, timeout = 30):
    lastMessage = client.send_message(chat_id, text)
    startTime = time.time()
    while True:
        message : telebot.types.Message = next(client.get_chat_history(chat_id, limit=1))
        if (message.from_user.id == bot_id) and (message != lastMessage):
            break
        if time.time() - startTime > timeout:
            assert False
            break
        time.sleep(DELAY)
    assert message.text == responceText
    return lastMessage.from_user.id

@pytest.fixture(scope="session")
def client():
    load_dotenv()
    api_id = os.getenv('api_id')
    api_hash = os.getenv('api_hash')
    session_string = os.getenv('session_string')
    client = Client(name='client1', api_id=api_id, api_hash=api_hash, in_memory=True, session_string=session_string)
    client.start()
    yield client
    client.stop()

@pytest.fixture(scope="session")
def client2():
    load_dotenv()
    api_id2 = os.getenv('api_id2')
    api_hash2 = os.getenv('api_hash2')
    session_string2 = os.getenv('session_string2')
    client2 = Client(name='client2', api_id=api_id2, api_hash=api_hash2, in_memory=True, session_string=session_string2)
    client2.start()
    yield client2
    client2.stop()

@pytest.fixture(scope='session')
def databaseTest():
    return Database()

@pytest.fixture(autouse=True)
def beforeTest(databaseTest):
    clearDatabase(databaseTest)

    yield

def create_user(client):
    checkResponce(client, '/member', 'Для продолжения нажми кнопку ввод')
    sendAndWaitAny(client, 'Ввод')
    checkResponce(client, 'test-name', 'Отображаемое имя установлено')

def create_test_subj(client):
    sendAndWaitAny(client, '/subject')
    sendAndWaitAny(client, 'subjj')

def delete_test_subj(client):
    sendAndWaitAny(client, '/delete')
    sendAndWaitAny(client, 'Очередь по subjj')
    sendAndWaitAny(client, '/removesubject')
    sendAndWaitAny(client, 'subjj')

def create_test_queue(client):
    create_test_subj(client)

    checkResponce(client, '/create', 'По какому предмету ты хочешь создать очередь?')
    sendAndWaitAny(client, 'subjj')

def clearDatabase(database):
    with database.connection.cursor() as cur:
        cur.execute("truncate queuemembers, queuesubjects, subjects, members")

def createMember(client):
    message: types.Message = sendAndWaitAny(client, '/member')
    sendAndWaitAny(client, 'Ввод')
    sendAndWaitAny(client, message.from_user.first_name)
    return message

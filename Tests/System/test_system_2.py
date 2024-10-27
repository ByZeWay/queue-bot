import pytest

import time
import os

import telebot
from telebot import types
from pyrogram import Client
from dotenv import load_dotenv

from Services.MemberService import MemberService
from Services.SubjectService import SubjectService
from Services.QueueService import QueueService
from Entities import Queue

from test_common import *
from utils import formReplaceRequest


# 13
@pytest.mark.system
def test_create_cancel(client, databaseTest):
    beforeQueuesCount = len(QueueService.getQueues(databaseTest))

    checkResponce(client, '/create', 'По какому предмету ты хочешь создать очередь?')
    checkResponce(client, '❌ Отмена', 'Команда отменена')

    afterQueuesCount = len(QueueService.getQueues(databaseTest))

    assert beforeQueuesCount == afterQueuesCount

# 14
@pytest.mark.system
def test_create_exists(client, databaseTest):
    create_test_queue(client)
    subject = SubjectService.getSubjectByTitle(databaseTest, 'subjj')
    
    assert QueueService.isQueueExist(databaseTest, subject.id)
    beforeQueuesCount = len(QueueService.getQueues(databaseTest))

    checkResponce(client, '/create', 'По какому предмету ты хочешь создать очередь?')
    checkResponce(client, 'subjj', 'Очередь по этому предмету уже существует')

    assert QueueService.isQueueExist(databaseTest, subject.id)
    
    afterQueuesCount = len(QueueService.getQueues(databaseTest))
    assert beforeQueuesCount == afterQueuesCount
    
# 15
# @pytest.mark.system
def test_join_last(client, client2, databaseTest):
    createMember(client)
    createMember(client2)
    create_test_queue(client)

    count = MemberService.getMembersCount(databaseTest)

    checkResponce(client, '/join', 'Выбрана очередь по subjj:\nВыбери место для записи')
    expected = f'Ты записан на {count} место'
    id1 = checkResponce(client, 'Последнее свободное', expected)

    checkResponce(client2, '/join', 'Выбрана очередь по subjj:\nВыбери место для записи')
    expected = f'Ты записан на {count - 1} место'
    id2 = checkResponce(client2, 'Последнее свободное', expected)

    queue: Queue = QueueService.getQueueBySubjectTitle(databaseTest, 'subjj')
    assert len(list(filter(lambda m: int(m.member.tgNum) == id1 and m.placeNumber == count, queue.members))) == 1
    assert len(list(filter(lambda m: int(m.member.tgNum) == id2 and m.placeNumber == count-1, queue.members))) == 1

# 16
# @pytest.mark.system
def test_join_first(client, client2, databaseTest):
    createMember(client)
    createMember(client2)
    create_test_queue(client)

    checkResponce(client, '/join', 'Выбрана очередь по subjj:\nВыбери место для записи')
    id1 = checkResponce(client, 'Первое свободное', 'Ты записан на 1 место')

    checkResponce(client2, '/join', 'Выбрана очередь по subjj:\nВыбери место для записи')
    id2 = checkResponce(client2, 'Первое свободное', 'Ты записан на 2 место')
    
    queue: Queue = QueueService.getQueueBySubjectTitle(databaseTest, 'subjj')
    assert len(list(filter(lambda m: int(m.member.tgNum) == id1 and m.placeNumber == 1, queue.members))) == 1
    assert len(list(filter(lambda m: int(m.member.tgNum) == id2 and m.placeNumber == 2, queue.members))) == 1

# 17
# @pytest.mark.system
def test_join_num(client, client2, databaseTest):
    createMember(client)
    createMember(client2)
    create_test_queue(client)
    
    checkResponce(client, '/join', 'Выбрана очередь по subjj:\nВыбери место для записи')
    checkResponce(client, 'Определенное', 'Введи место для записи')
    id1 = checkResponce(client, '2', 'Ты записан на 2 место')

    checkResponce(client2, '/join', 'Выбрана очередь по subjj:\nВыбери место для записи')
    checkResponce(client2, 'Определенное', 'Введи место для записи')
    id2 = checkResponce(client2, '2', 'Желаемое место уже занято. Ты записан на 1 место')

    queue: Queue = QueueService.getQueueBySubjectTitle(databaseTest, 'subjj')
    assert len(list(filter(lambda m: int(m.member.tgNum) == id1 and m.placeNumber == 2, queue.members))) == 1
    assert len(list(filter(lambda m: int(m.member.tgNum) == id2 and m.placeNumber == 1, queue.members))) == 1

# 18
# @pytest.mark.system
def test_confirm(client, client2, databaseTest):
    createMember(client)
    createMember(client2)
    create_test_queue(client)

    sendAndWaitAny(client, '/join')
    sendAndWaitAny(client, 'Определенное')
    msg1: types.Message = sendAndWaitAny(client, '1')

    sendAndWaitAny(client2, '/join')
    sendAndWaitAny(client2, 'Определенное')
    msg2: types.Message = sendAndWaitAny(client2, '2')

    queue: Queue = QueueService.getQueueBySubjectTitle(databaseTest, 'subjj')
    assert len(list(filter(lambda m: int(m.member.tgNum) == msg1.from_user.id and m.placeNumber == 1, queue.members))) == 1
    assert len(list(filter(lambda m: int(m.member.tgNum) == msg2.from_user.id and m.placeNumber == 2, queue.members))) == 1

    replaceRequestText = formReplaceRequest(msg1.from_user.username, msg2.from_user.username, 'subjj', 1, 2)
    checkResponce(client2, '/replace', 'Выбрана очередь по subjj:\nВведи место с которым хочешь поменяться')
    checkResponce(client2, '1', replaceRequestText)

    queue: Queue = QueueService.getQueueBySubjectTitle(databaseTest, 'subjj')
    assert len(list(filter(lambda m: int(m.member.tgNum) == msg1.from_user.id and m.placeNumber == 1, queue.members))) == 1
    assert len(list(filter(lambda m: int(m.member.tgNum) == msg2.from_user.id and m.placeNumber == 2, queue.members))) == 1

    checkResponce(client, '/confirm', 'Смена мест произошла успешно!')

    queue: Queue = QueueService.getQueueBySubjectTitle(databaseTest, 'subjj')
    assert len(list(filter(lambda m: int(m.member.tgNum) == msg1.from_user.id and m.placeNumber == 2, queue.members))) == 1
    assert len(list(filter(lambda m: int(m.member.tgNum) == msg2.from_user.id and m.placeNumber == 1, queue.members))) == 1

# 19
@pytest.mark.system
def test_auto_upd(client, databaseTest):
    create_test_queue(client)
    checkResponce(client, '/show', 'По какому предмету ты хочешь просмотреть очередь?')
    checkResponce(client, 'subjj', 'Очередь по subjj:')

    create_user(client)

    checkResponce(client, '/join', 'Выбрана очередь по subjj:\nВыбери место для записи')
    checkResponce(client, 'Первое свободное', 'Ты записан на 1 место')

    for message in client.get_chat_history(chat_id, limit=10):
        if 'Очередь по subjj:' in message.text:
            assert message.text != 'Очередь по subjj:\n1 - test-name'

# 20
# @pytest.mark.system
def test_notification(client, client2, databaseTest):
    create_test_queue(client)
    create_user(client)
    create_user(client2)
    checkResponce(client, '/join', 'Выбрана очередь по subjj:\nВыбери место для записи')
    sendAndWaitAny(client, 'Первое свободное')
    checkResponce(client2, '/join', 'Выбрана очередь по subjj:\nВыбери место для записи')
    mes = sendAndWaitAny(client2, 'Первое свободное')
    checkResponce(client, '/removefrom', 'Из какой очереди ты хочешь выйти')
    sendAndWaitAny(client, 'Очередь по subjj')
    
    gen = client.get_chat_history(chat_id, limit=2)
    notifMsg = next(gen)
    exitMsg = next(gen)
    assert exitMsg.text == 'Ты вышел из этой очереди'
    assert notifMsg.text == '@' + mes.from_user.username + ' твоя очередь сдавать'

# 21
@pytest.mark.system
def test_remove(client, databaseTest):
    create_test_queue(client)
    create_user(client)
    checkResponce(client, '/join', 'Выбрана очередь по subjj:\nВыбери место для записи')
    mes = sendAndWaitAny(client, 'Первое свободное')
    queue = QueueService.getQueueBySubjectTitle(databaseTest, 'subjj')
    member = MemberService.getMemberByTgNum(databaseTest, mes.from_user.id)
    assert QueueService.isMemberInQueue(databaseTest, queue.id, member.id)
    checkResponce(client, '/removefrom', 'Из какой очереди ты хочешь выйти')
    checkResponce(client, 'Очередь по subjj', 'Ты вышел из этой очереди')
    assert not QueueService.isMemberInQueue(databaseTest, queue.id, member.id)

# 22
# @pytest.mark.system
def test_join_num_last(client, client2, databaseTest):
    createMember(client)
    createMember(client2)
    create_test_queue(client)
    
    checkResponce(client, '/join', 'Выбрана очередь по subjj:\nВыбери место для записи')
    checkResponce(client, 'Определенное', 'Введи место для записи')
    id1 = checkResponce(client, '2', 'Ты записан на 2 место')

    checkResponce(client2, '/join', 'Выбрана очередь по subjj:\nВыбери место для записи')
    id2 = checkResponce(client2, 'Последнее свободное', 'Ты записан на 1 место')

    queue: Queue = QueueService.getQueueBySubjectTitle(databaseTest, 'subjj')
    assert len(list(filter(lambda m: int(m.member.tgNum) == id1 and m.placeNumber == 2, queue.members))) == 1
    assert len(list(filter(lambda m: int(m.member.tgNum) == id2 and m.placeNumber == 1, queue.members))) == 1

# 23
@pytest.mark.system
def test_remove_subject_with_queue(client, databaseTest):
    create_test_queue(client)
    assert SubjectService.isSubjectExist(databaseTest, 'subjj')
    
    subject = SubjectService.getSubjectByTitle(databaseTest, 'subjj')
    assert QueueService.isQueueExist(databaseTest, subject.id)
    
    checkResponce(client, '/removesubject', 'Удалить предмет')
    checkResponce(client, 'subjj', 'Предмет удален. По этому предмету была очередь, она тоже удалена')
    
    # Проверяем, что предмет и очередь были удалены
    assert not SubjectService.isSubjectExist(databaseTest, 'subjj')
    assert not QueueService.isQueueExist(databaseTest, subject.id)
    
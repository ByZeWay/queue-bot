import pytest

import time
import os

import telebot
from pyrogram import Client
from dotenv import load_dotenv

from Services.MemberService import MemberService
from Services.SubjectService import SubjectService
from Services.QueueService import QueueService

from test_common import *


# 1
@pytest.mark.system
def test_add_invalid_member(client, databaseTest):
    clientId = checkResponce(client, '/member', 'Для продолжения нажми кнопку ввод')
    sendAndWaitAny(client, 'Ввод')
    checkResponce(client, 'invalid*((&', 'Отображаемое имя некорректно.\n'
                                      'Используйте не более 30 символов русского и английского алфавита.'
                                      'Также дефис, апостроф, пробел (но не более одного такого символа подряд).')
    # Проверяем, что пользователь НЕ был добавлен
    assert not MemberService.isMemberExistByTgNum(databaseTest, int(clientId))


# 2
@pytest.mark.system
def test_add_valid_member(client, databaseTest):
    clientId = checkResponce(client, '/member', 'Для продолжения нажми кнопку ввод')
    sendAndWaitAny(client, 'Ввод')
    checkResponce(client, 'test-name', 'Отображаемое имя установлено')
    assert MemberService.getMemberByTgNum(databaseTest, int(clientId)).name == 'test-name'
    # Проверяем второй раз, что мы меняем имя тому же пользователю
    clientId = checkResponce(client, '/member', 'Для продолжения нажми кнопку ввод')
    sendAndWaitAny(client, 'Ввод')
    checkResponce(client, 'another-name', 'Отображаемое имя установлено')
    assert MemberService.getMemberByTgNum(databaseTest, int(clientId)).name == 'another-name'


# 3
@pytest.mark.system
def test_add_invalid_subject(client, databaseTest):
    checkResponce(client, '/subject', 'Введи название нового предмета')
    checkResponce(client, 'thisisverylongtitleforsubjectmore30letters', 'Название предмета некорректно.\nИспользуйте не более 30 символов русского и английского алфавита.')
    # Проверяем, что предмет НЕ был добавлен
    assert not SubjectService.isSubjectExist(databaseTest, 'thisisverylongtitleforsubjectmore30letters')


# 4
@pytest.mark.system
def test_add_valid_subject(client, databaseTest):

    assert not SubjectService.isSubjectExist(databaseTest, 'subjj')
    checkResponce(client, '/subject', 'Введи название нового предмета')
    checkResponce(client, 'subjj', 'Предмет subjj добавлен')
    # Проверяем, что предмет был добавлен
    assert SubjectService.getSubjectByTitle(databaseTest, 'subjj').title == 'subjj'

    checkResponce(client, '/subject', 'Введи название нового предмета')
    checkResponce(client, 'subjj', 'Предмет subjj уже существует')
    # Проверяем, что таких предметов все равно осталась одна штука
    assert SubjectService.isSubjectExist(databaseTest, 'subjj')

    sendAndWaitAny(client, '/removesubject')
    sendAndWaitAny(client, 'subjj')


# 5
@pytest.mark.system
def test_remove_subject(client, databaseTest):
    create_test_subj(client)
    assert SubjectService.isSubjectExist(databaseTest, 'subjj')
    checkResponce(client, '/removesubject', 'Удалить предмет')
    checkResponce(client, 'subjj', 'Предмет удален')
    # Проверяем, что предмет был удален
    assert not SubjectService.isSubjectExist(databaseTest, 'subjj')


# 6
@pytest.mark.system
def test_create_queue(client, databaseTest):
    create_test_subj(client)
    subjId = SubjectService.getSubjectByTitle(databaseTest, 'subjj').id
    assert not QueueService.isQueueExist(databaseTest, subjId)

    checkResponce(client, '/create', 'По какому предмету ты хочешь создать очередь?')
    sendAndWaitAny(client, 'subjj')

    assert QueueService.isQueueExist(databaseTest, subjId)

# 7
@pytest.mark.system
def test_delete(client, databaseTest):
    create_test_queue(client)

    checkResponce(client, '/delete', 'По какому предмету ты хочешь удалить очередь?')

    subjId = SubjectService.getSubjectByTitle(databaseTest, 'subjj').id
    assert QueueService.isQueueExist(databaseTest, subjId)

    checkResponce(client, 'Очередь по subjj', 'Очередь удалена')

    subjId = SubjectService.getSubjectByTitle(databaseTest, 'subjj').id
    assert not QueueService.isQueueExist(databaseTest, subjId)

#8
@pytest.mark.system
def test_delete_cancel(client, databaseTest):
    create_test_queue(client)

    subjId = SubjectService.getSubjectByTitle(databaseTest, 'subjj').id

    checkResponce(client, '/delete', 'По какому предмету ты хочешь удалить очередь?')
    
    assert QueueService.isQueueExist(databaseTest, subjId)
    checkResponce(client, '❌ Отмена', 'Команда отменена')
    assert QueueService.isQueueExist(databaseTest, subjId)

    checkResponce(client, '/delete', 'По какому предмету ты хочешь удалить очередь?')

    assert QueueService.isQueueExist(databaseTest, subjId)
    checkResponce(client, 'incorrect_sub:?', 'Команда отменена')
    assert QueueService.isQueueExist(databaseTest, subjId)

# 9
@pytest.mark.system
def test_show(client, databaseTest):
    create_test_queue(client)

    checkResponce(client, '/show', 'По какому предмету ты хочешь просмотреть очередь?')
    checkResponce(client, 'subjj', 'Очередь по subjj:')

    subjId = SubjectService.getSubjectByTitle(databaseTest, 'subjj').id
    queuqId = QueueService.getQueueBySubjectId(databaseTest, subjId).id
    assert QueueService.getCountMembersInQueue(databaseTest, queuqId) == 0

# 10
@pytest.mark.system
def test_confirm_empty(client):
    checkResponce(client, '/confirm', 'Для использования этой команды тебе нужно записаться в списочек member-ов')

    createMember(client)
    checkResponce(client, '/confirm', 'Извините, у вас еще нет запросов на смену места')


# 11
@pytest.mark.system
def test_reject_empty(client):
    createMember(client)
    checkResponce(client, '/reject', 'Ты еще не записан ни в одну очередь. Ух, ты!')

    create_test_queue(client)
    checkResponce(client, '/join', 'Выбрана очередь по subjj:\nВыбери место для записи')
    checkResponce(client, 'Первое свободное', 'Ты записан на 1 место')
    checkResponce(client, '/reject', 'Вы не начинали смену мест')

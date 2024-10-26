from unittest.mock import Mock, patch
import pytest
from Requests.UserHandlers import UserHandlers
from Requests.RuntimeInfoManager import RuntimeInfoManager
from telebot import types, TeleBot
import TgUtils.KeyboardMarkups as km
from Services.MemberService import MemberService


@pytest.fixture
def userHandlers():
    return UserHandlers(Mock(), Mock(), RuntimeInfoManager())

@pytest.mark.integration
def test_UserHandlers_memberCommand(userHandlers):
    message = Mock()
    userHandlers.memberCommand(message)

    userHandlers.bot.reply_to.assert_called_once_with(message, 'Для продолжения нажми кнопку ввод', reply_markup=km.EnterCancel)
    assert message.from_user.id in userHandlers.runtimeInfoManager.sendBarrier.data['member1']

@pytest.mark.integration
def test_UserHandlers_setNameTextHandler_enter(userHandlers):
    message = Mock()
    message.text = 'Ввод'

    userHandlers.runtimeInfoManager.sendBarrier.add('member1', message.from_user.id)

    userHandlers.setNameTextHandler(message)

    userHandlers.bot.reply_to.assert_called_once_with(message, 'Введи имя, которое будет отображаться при выводе сообщений', reply_markup=km.Remove)
    assert 'member1' not in userHandlers.runtimeInfoManager.sendBarrier.data
    assert message.from_user.id in userHandlers.runtimeInfoManager.sendBarrier.data['member2']

@pytest.mark.integration
def test_UserHandlers_setNameTextHandler_cancel(userHandlers):
    message = Mock()
    message.text = '❌ Отмена'

    userHandlers.runtimeInfoManager.sendBarrier.add('member1', message.from_user.id)

    userHandlers.setNameTextHandler(message)

    userHandlers.bot.reply_to.assert_called_once_with(message, 'Ввод отображаемого имени отменен', reply_markup=km.Remove)
    assert 'member1' not in userHandlers.runtimeInfoManager.sendBarrier.data
    assert 'member2' not in userHandlers.runtimeInfoManager.sendBarrier.data

@pytest.mark.integration
def test_UserHandlers_setNameTextHandler_name(userHandlers):
    message = Mock()
    message.text = 'Какое то имя'

    userHandlers.runtimeInfoManager.sendBarrier.add('member2', message.from_user.id)
    
    with patch.object(MemberService, 'addMember') as mock_addMember:
        userHandlers.setNameTextHandler(message)

        mock_addMember.assert_called_once_with(userHandlers.database, message.text, message.from_user.id)

    userHandlers.bot.reply_to.assert_called_once_with(message, 'Отображаемое имя установлено')
    assert 'member1' not in userHandlers.runtimeInfoManager.sendBarrier.data
    assert 'member2' not in userHandlers.runtimeInfoManager.sendBarrier.data

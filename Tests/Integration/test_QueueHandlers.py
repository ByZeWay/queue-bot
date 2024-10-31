import pytest
from unittest.mock import Mock, patch

from Entities.Subject import Subject
from Requests.QueueEntity import QueueEntity
from Requests.RuntimeInfoManager import RuntimeInfoManager
from telebot import types, TeleBot
import TgUtils.KeyboardMarkups as km
from Services.SubjectService import SubjectService
from Services.QueueService import QueueService



@pytest.fixture
def queueHandlers():
    return QueueEntity(Mock(), Mock(), RuntimeInfoManager())

@pytest.mark.integration
def test_QueueHandlers_createCommand(queueHandlers):
    message = Mock()
    subjects = [Subject(1, 'subj1'), Subject(2, 'subj2')]
    
    with patch.object(SubjectService, 'getSubjects') as mock_getSubjects:
        mock_getSubjects.return_value = subjects

        queueHandlers.createCommand(message)

        queueHandlers.bot.reply_to.assert_called_once()
        args, kwargs = queueHandlers.bot.reply_to.call_args_list[0]
        assert args == (message, 'По какому предмету ты хочешь создать очередь?')
        assert kwargs['reply_markup'].to_json() == km.makeSubjectListMarkup(subjects).to_json()

        mock_getSubjects.assert_called_once_with(queueHandlers.database)

        assert message.from_user.id in queueHandlers.runtimeInfoManager.sendBarrier.data['create']

@pytest.mark.integration
def test_QueueHandlers_queueTextHandler_createCancel(queueHandlers):
    message = Mock()
    message.text = '❌ Отмена'
    
    queueHandlers.runtimeInfoManager.sendBarrier.add('create', message.from_user.id)

    queueHandlers.queueTextHandler(message)

    queueHandlers.bot.reply_to.assert_called_once_with(message, 'Команда отменена', reply_markup=km.Remove)
    assert 'create' not in queueHandlers.runtimeInfoManager.sendBarrier.data

@pytest.mark.integration
def test_QueueHandlers_queueTextHandler_create_subjectNotExists(queueHandlers):
    message = Mock()
    
    queueHandlers.runtimeInfoManager.sendBarrier.add('create', message.from_user.id)

    with (
        patch.object(SubjectService, 'isSubjectExist', return_value = False) as mock_isSubjectExist,
        patch.object(SubjectService, 'getSubjectByTitle') as mock_getSubjectByTitle,
        patch.object(QueueService, 'isQueueExist') as mock_isQueueExist,
        patch.object(QueueService, 'createQueue') as mock_createQueue,
    ):
        queueHandlers.queueTextHandler(message)

        mock_isSubjectExist.assert_called_once_with(queueHandlers.database, message.text)
        mock_getSubjectByTitle.assert_not_called()
        mock_isQueueExist.assert_not_called()
        mock_createQueue.assert_not_called()
        queueHandlers.bot.reply_to.assert_called_once_with(message, 'Такого предмета нет', reply_markup=km.Remove)
        assert 'create' not in queueHandlers.runtimeInfoManager.sendBarrier.data

# @pytest.mark.integration
def test_QueueHandlers_queueTextHandler_create(queueHandlers):
    message = Mock()
    subject = Subject(1, 'subjj')

    queueHandlers.runtimeInfoManager.sendBarrier.add('create', message.from_user.id)

    with (
        patch.object(SubjectService, 'isSubjectExist', return_value=True) as mock_isSubjectExist,
        patch.object(SubjectService, 'getSubjectByTitle', return_value=subject) as mock_getSubjectByTitle,
        patch.object(QueueService, 'isQueueExist', return_value=False) as mock_isQueueExist,
        patch.object(QueueService, 'createQueue') as mock_createQueue,
    ):
        queueHandlers.queueTextHandler(message)

        mock_isSubjectExist.assert_called_once_with(queueHandlers.database, message.text)
        mock_getSubjectByTitle.assert_called_once_with(queueHandlers.database, message.text)
        mock_isQueueExist.assert_called_once_with(queueHandlers.database, subject.id)
        mock_createQueue.assert_called_once_with(queueHandlers.database, subject.id)
        queueHandlers.bot.reply_to.assert_called_once_with(message, f'Создана очередь по {subject.title}', reply_markup=km.Remove)

@pytest.mark.integration
def test_QueueHandlers_queueTextHandler_create_queueExists(queueHandlers):
    message = Mock()
    subject = Subject(1, 'subjj')

    queueHandlers.runtimeInfoManager.sendBarrier.add('create', message.from_user.id)

    with (
        patch.object(SubjectService, 'isSubjectExist', return_value=True) as mock_isSubjectExist,
        patch.object(SubjectService, 'getSubjectByTitle', return_value=subject) as mock_getSubjectByTitle,
        patch.object(QueueService, 'isQueueExist', return_value=True) as mock_isQueueExist,
        patch.object(QueueService, 'createQueue') as mock_createQueue,
    ):
        queueHandlers.queueTextHandler(message)

        mock_isSubjectExist.assert_called_once_with(queueHandlers.database, message.text)
        mock_getSubjectByTitle.assert_called_once_with(queueHandlers.database, message.text)
        mock_isQueueExist.assert_called_once_with(queueHandlers.database, subject.id)
        mock_createQueue.assert_not_called()
        queueHandlers.bot.reply_to.assert_called_once_with(message, 'Очередь по этому предмету уже существует', reply_markup=km.Remove)

@pytest.mark.integration
def test_QueueHandlers_deleteCommand_forbidden(queueHandlers):
    message = Mock()
    chatMember = Mock()
    chatMember.status = 'member'

    with (
        patch.object(queueHandlers.bot, 'get_chat_member', return_value=chatMember) as mock_get_chat_member
    ):
        queueHandlers.deleteCommand(message)

        mock_get_chat_member.assert_called_once_with(message.chat.id, message.from_user.id)
        queueHandlers.bot.reply_to.assert_called_once_with(message, 'Эту команду могут выполнять только администраторы')

@pytest.mark.integration
def test_QueueHandlers_deleteCommand(queueHandlers):
    message = Mock()
    chatMember = Mock()
    chatMember.status = 'administrator'

    subjects = [Subject(1, 'subj1'), Subject(2, 'subj2')]

    with (
        patch.object(queueHandlers.bot, 'get_chat_member', return_value=chatMember) as mock_get_chat_member,
        patch.object(SubjectService, 'getSubjects', return_value=subjects) as mock_getSubjects,
        patch.object(QueueService, 'isQueueExist', return_value=True) as mock_isQueueExist
    ):
        queueHandlers.deleteCommand(message)

        mock_get_chat_member.assert_called_once_with(message.chat.id, message.from_user.id)

        queueHandlers.bot.reply_to.assert_called_once()
        args, kwargs = queueHandlers.bot.reply_to.call_args_list[0]
        assert args == (message, 'По какому предмету ты хочешь удалить очередь?')
        assert kwargs['reply_markup'].to_json() == km.makeQueueListMarkup(subjects).to_json()
        assert message.from_user.id in queueHandlers.runtimeInfoManager.sendBarrier.data['delete']

        mock_getSubjects.assert_called_once_with(queueHandlers.database)

        assert mock_isQueueExist.call_count == len(subjects)
        for s in subjects:
            mock_isQueueExist.assert_any_call(queueHandlers.database, s.id)

@pytest.mark.integration
def test_QueueHandlers_queueTextHandler_delete_cancel(queueHandlers):
    message = Mock()
    message.text = '❌ Отмена'
    
    queueHandlers.runtimeInfoManager.sendBarrier.add('delete', message.from_user.id)

    queueHandlers.queueTextHandler(message)

    queueHandlers.bot.reply_to.assert_called_once_with(message, 'Команда отменена', reply_markup=km.Remove)
    assert 'delete' not in queueHandlers.runtimeInfoManager.sendBarrier.data

@pytest.mark.integration
def test_QueueHandlers_queueTextHandler_delete_subjectNotExists(queueHandlers):
    message = Mock()
    
    queueHandlers.runtimeInfoManager.sendBarrier.add('delete', message.from_user.id)

    with (
        patch.object(SubjectService, 'isSubjectExist', return_value=False) as mock_isSubjectExist,
        patch.object(SubjectService, 'getSubjectByTitle') as mock_getSubjectByTitle,
        patch.object(QueueService, 'isQueueExist') as mock_isQueueExist,
        patch.object(QueueService, 'createQueue') as mock_createQueue,
    ):
        queueHandlers.queueTextHandler(message)

        mock_isSubjectExist.assert_called_once_with(queueHandlers.database, message.text.removeprefix('Очередь по '))
        mock_getSubjectByTitle.assert_not_called()
        mock_isQueueExist.assert_not_called()
        mock_createQueue.assert_not_called()
        queueHandlers.bot.reply_to.assert_called_once_with(message, 'Такого предмета не существует', reply_markup=km.Remove)
        assert 'delete' not in queueHandlers.runtimeInfoManager.sendBarrier.data

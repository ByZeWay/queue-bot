from unittest.mock import Mock, patch
import pytest
from Entities.Queue import Queue
from Entities.Subject import Subject
from Requests.SubjectHandlers import SubjectHandlers
from Requests.RuntimeInfoManager import RuntimeInfoManager
from telebot import types, TeleBot
from Services.QueueService import QueueService
from Services.SubjectService import SubjectService
import TgUtils.KeyboardMarkups as km
from Services.MemberService import MemberService


@pytest.fixture
def subjectHandlers():
    return SubjectHandlers(Mock(), Mock(), RuntimeInfoManager())

# @pytest.mark.integration
def test_SubjectHandlers_subjectCommand(subjectHandlers):
    message = Mock()

    subjectHandlers.subjectCommand(message)

    subjectHandlers.bot.reply_to.assert_called_once_with(message, 'Введи название нового предмета')
    assert message.from_user.id in subjectHandlers.runtimeInfoManager.sendBarrier.data['subject']

# @pytest.mark.integration
def test_SubjectHandlers_removesubjectCommand(subjectHandlers):
    message = Mock()
    subjects = [Subject(1, 'subj1'), Subject(2, 'subj2')]

    with patch.object(SubjectService, 'getSubjects') as mock_getSubjects:
        mock_getSubjects.return_value = subjects

        subjectHandlers.removesubjectCommand(message)

    subjectHandlers.bot.reply_to.assert_called_once()

    args, kwargs = subjectHandlers.bot.reply_to.call_args_list[0]
    assert args == (message, 'Удалить предмет')
    assert kwargs['reply_markup'].to_json() == km.makeSubjectListMarkup(subjects).to_json()

    assert message.from_user.id in subjectHandlers.runtimeInfoManager.sendBarrier.data['removesubject']

# @pytest.mark.integration
def test_SubjectHandlers_subjectTextHandler_addNew(subjectHandlers):
    message = Mock()
    message.text = 'subjj'

    subjectHandlers.runtimeInfoManager.sendBarrier.add('subject', message.from_user.id)

    with (
        patch.object(SubjectService, 'isSubjectExist') as mock_isSubjectExist,
        patch.object(SubjectService, 'addSubject') as mock_addSubject
    ):
        mock_isSubjectExist.return_value = False
        subjectHandlers.subjectTextHandler(message)

        mock_isSubjectExist.assert_called_once_with(subjectHandlers.database, message.text)
        mock_addSubject.assert_called_once_with(subjectHandlers.database, message.text)

        subjectHandlers.bot.reply_to.assert_called_once_with(message, f'Предмет {message.text} добавлен')

# @pytest.mark.integration
def test_SubjectHandlers_subjectTextHandler_addExists(subjectHandlers):
    message = Mock()
    message.text = 'subjj'

    subjectHandlers.runtimeInfoManager.sendBarrier.add('subject', message.from_user.id)

    with (
        patch.object(SubjectService, 'isSubjectExist', return_value = True) as mock_isSubjectExist,
        patch.object(SubjectService, 'addSubject') as mock_addSubject
    ):
        subjectHandlers.subjectTextHandler(message)

        mock_isSubjectExist.assert_called_once_with(subjectHandlers.database, message.text)
        mock_addSubject.assert_not_called()

        subjectHandlers.bot.reply_to.assert_called_once_with(message, f'Предмет {message.text} уже существует')

@pytest.mark.integration
def test_SubjectHandlers_subjectTextHandler_removeExistsWithoutQueue(subjectHandlers):
    message = Mock()
    subject = Subject(1, 'subjj')
    message.text = subject.title

    subjectHandlers.runtimeInfoManager.sendBarrier.add('removesubject', message.from_user.id)

    with (
        patch.object(SubjectService, 'isSubjectExist', return_value = True) as mock_isSubjectExist,
        patch.object(SubjectService, 'getSubjectByTitle', return_value = subject) as mock_getSubjectByTitle,
        patch.object(QueueService, 'isQueueExist', return_value = False) as mock_isQueueExist,
        patch.object(SubjectService, 'removeSubject') as mock_removeSubject
    ):
        subjectHandlers.subjectTextHandler(message)

        mock_isSubjectExist.assert_called_once_with(subjectHandlers.database, subject.title)
        mock_getSubjectByTitle.assert_called_once_with(subjectHandlers.database, subject.title)
        mock_isQueueExist.assert_called_once_with(subjectHandlers.database, subject.id)
        mock_removeSubject.assert_called_once_with(subjectHandlers.database, subject.title)

        subjectHandlers.bot.reply_to.assert_called_once_with(message, 'Предмет удален', reply_markup=km.Remove)

@pytest.mark.integration
def test_SubjectHandlers_subjectTextHandler_removeNotExists(subjectHandlers):
    message = Mock()
    subject = Subject(1, 'subjj')
    message.text = subject.title

    subjectHandlers.runtimeInfoManager.sendBarrier.add('removesubject', message.from_user.id)

    with (
        patch.object(SubjectService, 'isSubjectExist', return_value = False) as mock_isSubjectExist,
        patch.object(SubjectService, 'getSubjectByTitle') as mock_getSubjectByTitle,
        patch.object(QueueService, 'isQueueExist') as mock_isQueueExist,
        patch.object(SubjectService, 'removeSubject') as mock_removeSubject
    ):
        subjectHandlers.subjectTextHandler(message)

        mock_isSubjectExist.assert_called_once_with(subjectHandlers.database, subject.title)
        mock_getSubjectByTitle.assert_not_called()
        mock_isQueueExist.assert_not_called()
        mock_removeSubject.assert_not_called()

        subjectHandlers.bot.reply_to.assert_called_once_with(message, 'Такого предмета и так не было. Зачем удалять то...', reply_markup=km.Remove)

# @pytest.mark.integration
def test_SubjectHandlers_subjectTextHandler_removeExistsWithQueue(subjectHandlers):
    message = Mock()
    subject = Subject(1, 'subjj')
    queue = Queue(1, subject, False, [])
    message.text = subject.title

    subjectHandlers.runtimeInfoManager.sendBarrier.add('removesubject', message.from_user.id)

    with (
        patch.object(SubjectService, 'isSubjectExist', return_value = True) as mock_isSubjectExist,
        patch.object(SubjectService, 'getSubjectByTitle', return_value = subject) as mock_getSubjectByTitle,
        patch.object(QueueService, 'isQueueExist', return_value = True) as mock_isQueueExist,
        patch.object(SubjectService, 'removeSubject') as mock_removeSubject,
        patch.object(QueueService, 'getQueueBySubjectId', return_value=queue) as mock_getQueueBySubjectId,
        patch.object(QueueService, 'deleteQueue') as mock_deleteQueue,

    ):
        subjectHandlers.subjectTextHandler(message)

        mock_isSubjectExist.assert_called_once_with(subjectHandlers.database, subject.title)
        mock_getSubjectByTitle.assert_called_once_with(subjectHandlers.database, subject.title)
        mock_isQueueExist.assert_called_once_with(subjectHandlers.database, subject.id)
        mock_getQueueBySubjectId.assert_called_once_with(subjectHandlers.database, subject.id)
        mock_removeSubject.assert_called_once_with(subjectHandlers.database, subject.title)
        mock_deleteQueue.assert_called_once_with(subjectHandlers.database, queue.id)

        assert subjectHandlers.bot.reply_to.call_count == 1
        subjectHandlers.bot.reply_to.assert_any_call(message, 'Предмет удален. По этому предмету была очередь, она тоже удалена', reply_markup=km.Remove)

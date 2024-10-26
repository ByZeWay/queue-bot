import pytest

from DbUtils.db import Database


@pytest.fixture(scope='session')
def databaseTest():
    return Database()

def clearDatabase(database):
    with database.connection.cursor() as cur:
        cur.execute("truncate queuemembers, queuesubjects, subjects, members")

def fillTestData(database):
    with database.connection.cursor() as cur:
        cur.execute("INSERT INTO public.members (id_member, name, tg_num) VALUES (1, 'artas', '123456')")
        cur.execute("INSERT INTO public.members (id_member, name, tg_num) VALUES (2, 'dmitry', '789101112')")
        cur.execute("INSERT INTO public.members (id_member, name, tg_num) VALUES (3, 'artem', '1314151617')")
        cur.execute("INSERT INTO public.subjects (id_subject, title) VALUES (1, 'trkpo')")
        cur.execute("INSERT INTO public.subjects (id_subject, title) VALUES (2, 'oprkppim')")
        cur.execute("INSERT INTO public.subjects (id_subject, title) VALUES (3, 'pdpu')")
        cur.execute("INSERT INTO public.queuesubjects (id_queue, subject_id, is_last) VALUES (1, 1, false)")
        cur.execute("INSERT INTO public.queuesubjects (id_queue, subject_id, is_last) VALUES (2, 2, false)")
        cur.execute("INSERT INTO public.queuesubjects (id_queue, subject_id, is_last) VALUES (3, 3, true)")
        cur.execute("INSERT INTO public.queuemembers (queue_id, member_id, entry_time, place_number, entry_type) VALUES (1, 1, '2024-02-18 23:19:16.334518', 1, 0)")
        cur.execute("INSERT INTO public.queuemembers (queue_id, member_id, entry_time, place_number, entry_type) VALUES (1, 2, '2024-02-18 23:20:16.334518', 2, 0)")
        cur.execute("INSERT INTO public.queuemembers (queue_id, member_id, entry_time, place_number, entry_type) VALUES (1, 3, '2024-02-18 23:21:16.334518', 3, 0)")
        cur.execute("INSERT INTO public.queuemembers (queue_id, member_id, entry_time, place_number, entry_type) VALUES (2, 1, '2024-02-18 23:34:16.334518', 3, 2)")
        cur.execute("INSERT INTO public.queuemembers (queue_id, member_id, entry_time, place_number, entry_type) VALUES (2, 3, '2024-02-18 23:38:16.334518', 2, 1)")
        cur.execute("SELECT pg_catalog.setval('public.members_id_member_seq', 4, true)")
        cur.execute("SELECT pg_catalog.setval('public.queuesubjects_id_queue_seq', 4, true)")
        cur.execute("SELECT pg_catalog.setval('public.subjects_id_subject_seq', 4, true)")

@pytest.fixture(autouse=True)
def beforeTest(databaseTest):
    clearDatabase(databaseTest)
    fillTestData(databaseTest)
    yield

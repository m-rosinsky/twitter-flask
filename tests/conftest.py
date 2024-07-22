import os
import pytest
import psycopg2

from flask import Flask
from flaskr import create_app
from flaskr.db import get_db, init_db
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

with open(os.path.join(os.path.dirname(__file__), 'data.sql'), 'rb') as f:
    _data_sql = f.read().decode('utf-8')

def create_test_db():
    base_db_url = os.getenv('DATABASE_URL')
    test_db_name = 'test_db'

    conn = psycopg2.connect(base_db_url)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    cursor.execute(f'DROP DATABASE IF EXISTS {test_db_name}')
    cursor.execute(f'CREATE DATABASE {test_db_name}')
    cursor.close()
    conn.close()

    test_db_url = base_db_url.rsplit('/', 1)[0] + f'/{test_db_name}'
    return test_db_url

def drop_test_db(test_db_url):
    base_db_url = test_db_url.rsplit('/', 1)[0] + '/postgres'
    test_db_name = test_db_url.rsplit('/', 1)[1]

    conn = psycopg2.connect(base_db_url)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    cursor.execute(f'DROP DATABASE IF EXISTS {test_db_name}')
    cursor.close()
    conn.close()

@pytest.fixture
def app():
    test_db_url = create_test_db()

    app = create_app({
        'TESTING': True,
        'DATABASE': test_db_url,
    })

    with app.app_context():
        init_db()
        db = get_db()

        with db.cursor() as cursor:
            cursor.execute(_data_sql)
            db.commit()

    yield app

    drop_test_db(test_db_url)


@pytest.fixture
def client(app: Flask):
    return app.test_client()


@pytest.fixture
def runner(app: Flask):
    return app.test_cli_runner()


class AuthActions(object):
    def __init__(self, client):
        self._client = client

    def login(self, username='test', password='test'):
        return self._client.post(
            '/auth/login',
            data={'username': username, 'password': password}
        )

    def logout(self):
        return self._client.get('/auth/logout')


@pytest.fixture
def auth(client):
    return AuthActions(client)

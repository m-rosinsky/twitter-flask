import pytest
from flask import g, session
from flaskr.db import get_db, DB_CONNECT_ERROR_STR


def test_register(client, app):
    # Test successful GET of registration page.
    assert client.get('/auth/register').status_code == 200

    # Test POST of a new user successfully redirects to login page.
    response = client.post(
        '/auth/register',
        data={
            'username': 'a',
            'password': 'a',
        }
    )
    assert response.headers["Location"] == "/auth/login"

    # Test that the entry was successfully entered into db.
    with app.app_context():
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM users WHERE username = 'a'",
            )
            
            assert cursor.fetchone() is not None


def test_noconnect_register(badclient):
    # Test successful GET of registration page.
    assert badclient.get('/auth/register').status_code == 200

    # Test POST of a new user, which should error since we can't connect
    # to database.
    response = badclient.post(
        '/auth/register',
        data={
            'username': 'a',
            'password': 'a',
        }
    )
    assert DB_CONNECT_ERROR_STR.encode('utf-8') in response.data


@pytest.mark.parametrize(('username', 'password', 'message'), (
    ('', '', b'Username is required'),
    ('a', '', b'Password is required'),
    ('test', 'test', b'already registered'),
))
def test_register_validate_input(client, username, password, message):
    response = client.post(
        '/auth/register',
        data={'username': username, 'password': password},
    )
    assert message in response.data


def test_login(client, auth):
    # Test successful GET of login page.
    assert client.get('/auth/login').status_code == 200

    # Test POST of an existing user that redirects to blog index page.
    response = auth.login()
    assert response.headers["Location"] == "/"

    # Test that the user login info is stored in the session.
    with client:
        client.get('/')
        assert session['user_id'] == 1
        assert g.user['username'] == 'test'


@pytest.mark.parametrize(('username', 'password', 'message'), (
    ('a', 'test', b'Incorrect username.'),
    ('test', 'a', b'Incorrect password.'),
))
def test_login_validate_input(auth, username, password, message):
    response = auth.login(username, password)
    assert message in response.data


def test_logout(client, auth):
    auth.login()

    with client:
        auth.logout()
        assert 'user_id' not in session

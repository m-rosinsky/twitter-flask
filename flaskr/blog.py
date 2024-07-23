from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db, DB_CONNECT_ERROR_STR

bp = Blueprint('blog', __name__)


@bp.route('/')
def index():
    db = get_db()
    if db is None:
        return render_template('blog/index.html', posts='error')

    with db.cursor() as cursor:
        cursor.execute(
            'SELECT p.id, title, body, created, author_id, username'
            ' FROM posts p JOIN users u ON p.author_id = u.id'
            ' ORDER BY created DESC'
        )

        posts = cursor.fetchall()
    return render_template('blog/index.html', posts=posts)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        db = get_db()
        if db is None:
            error = DB_CONNECT_ERROR_STR

        if error is not None:
            flash(error)
        else:
            db = get_db()
            with db.cursor() as cursor:
                cursor.execute(
                    'INSERT INTO posts (title, body, author_id)'
                    ' VALUES (%s, %s, %s)',
                    (title, body, g.user['id'])
                )
                db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/create.html')


def get_post(id, check_author=True):
    db = get_db()
    if db is None:
        return None

    with db.cursor() as cursor:
        cursor.execute(
            'SELECT p.id, title, body, created, author_id, username'
            ' FROM posts p JOIN users u ON p.author_id = u.id'
            ' WHERE p.id = %s',
            (id,)
        )
        post = cursor.fetchone()

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    return post


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

    # Error retrieving posts.
    if post is None:
        return redirect(url_for('blog.index'))

    if request.method == 'POST':
        error = None
        title = request.form['title']
        body = request.form['body']

        if not title:
            error = 'Title is required.'

        db = get_db()
        if db is None:
            error = DB_CONNECT_ERROR_STR

        if error is not None:
            flash(error)
        else:
            with db.cursor() as cursor:
                cursor.execute(
                    'UPDATE posts SET title = %s, body = %s'
                    ' WHERE id = %s',
                    (title, body, id)
                )
                db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/update.html', post=post)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    error = None
    db = get_db()

    if db is None:
        error = DB_CONNECT_ERROR_STR

    if error is not None:
        flash(error)
    else:
        with db.cursor() as cursor:
            cursor.execute(
                'DELETE FROM posts WHERE id = %s',
                (id, )
            )
            db.commit()
    return redirect(url_for('blog.index'))

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_user
from os import environ
from urllib.parse import urlparse, urljoin

from app.forms import LoginForm
from app.models import User

bp = Blueprint('auth', __name__)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        remember = True if form.remember.data else False

        # user = User.query.filter_by(email=email).first()

        # check if the user actually exists
        # take the user-supplied password, hash it, and compare it to the hashed password in the database
        # if not user or not check_password_hash(user.password, password):
        if username != environ.get('USERNAME') or password != environ.get('PASSWORD'):
            flash('Please check your login details and try again', 'error')
            return redirect(url_for('auth.login'))  # if the user doesn't exist or password is wrong, reload the page

        # if the above check passes, then we know the user has the right credentials
        login_user(User(username), remember=remember)
        next_url = request.args.get('next')
        if not is_safe_url(next_url):
            return abort(400)
        return redirect(next_url or url_for('dashboard.index'))
    return render_template('auth/new.html', title='Acceder', form=form)


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

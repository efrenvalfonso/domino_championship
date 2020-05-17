import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SECRET_KEY = os.environ.get(
        'SECRET_KEY') or '4e657ba7a2617012964ee66c05a721b9e6198c7304b5049a502ee2dc1e3fe3493b7c887ccf211280b71b5e32173d83fd780dd696aa63605847820c46ecb7a354'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    if os.environ['FLASK_ENV'] == 'development':
        SQLALCHEMY_ECHO = True
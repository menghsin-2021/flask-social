from flask_wtf import Form
# FlaskWTFDeprecationWarning: "flask_wtf.Form" has been renamed to "FlaskForm"
from wtforms import StringField, PasswordField
from wtforms.validators import (DataRequired, Regexp, ValidationError, Email,
                                Length, EqualTo)

from models import User


def name_exists(form, field):
    if User.select().where(User.username == field.data).exists():
        raise ValidationError('User with that name already exists.')


def email_exists(form, field):
    if User.select().where(User.email == field.data).exists():
        raise ValidationError('User with that name already exists.')

# for sign up
class RegisterForm(Form):
    # put the labels of username/email/password/password2
    username = StringField(
        'Username',
        validators=[
            DataRequired(),  # 如果沒輸入資料會跳訊息
            Regexp(
                r'^[a-zA-Z0-9_]+$',
                message="Username should be one word, letters,"
                        "numbers, and underscores only."
            ),  # regular expression pattern
            name_exists
        ])
    email = StringField(
        'Email',
        validators=[
            DataRequired(),
            Email(),
            email_exists
        ])
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(),
            Length(min=2),
            EqualTo('password2', message='Passwords mus match')
        ])
    password2 = PasswordField(
        'Confirm Password',
        validators=[DataRequired()]
    )


# for sign in
class LoginForm(Form):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
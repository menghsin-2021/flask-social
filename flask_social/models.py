import os
import datetime

from dotenv import load_dotenv
from flask_login import UserMixin
from flask_bcrypt import generate_password_hash
from peewee import *

load_dotenv()
HOST = os.getenv('HOST')
USER = os.getenv('USER')
PASSWORD = os.getenv('PASSWORD')
DATABASE = MySQLDatabase('social', host=HOST, port=3306, user=USER, passwd=PASSWORD)


class MySQLModel(Model):  # Model 為 peewee 內建 Class 用於給要建立的 model 繼承
    """A base model that will use our MySQL database"""

    # 告訴 model 要放到哪個 database，原本要寫到各個 class 底下 但放在這裡用繼承的
    class Meta:
        database = DATABASE
        order_by = ('-joined_at',)

# 建立 User model(Table)
class User(UserMixin, MySQLModel):
    username = CharField(unique=True)
    email = CharField(unique=True)
    password = CharField(max_length=100)
    joined_at = DateTimeField(default=datetime.datetime.now)
    is_admin = BooleanField(default=False)

    @classmethod
    def create_user(cls, username, email, password, admin=False):
        try:
            # If you're constantly getting a locked database, change your User.create_user method to the following:
            with DATABASE.transaction():  # new added because of database locked
                cls.create(
                    username=username,
                    email=email,
                    password=generate_password_hash(password),
                    is_admin=admin
                )
        except IntegrityError:
            raise ValueError('User already exists')

# 確認為使用者後才執行
def initialize():
    DATABASE.connect()
    DATABASE.create_tables([User], safe=True)
    DATABASE.close()

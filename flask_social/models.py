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


# 建立 User model(Table)
class User(UserMixin, Model):
    username = CharField(unique=True)
    email = CharField(unique=True)
    password = CharField(max_length=100)
    joined_at = DateTimeField(default=datetime.datetime.now)
    is_admin = BooleanField(default=False)

    @classmethod
    def create_user(cls, username, email, password, admin=False):
        try:
            # If you're constantly getting a locked database, change your User.create_user method to the following:
            # transaction says tray this thing out, if it doesn't works remove what every you just did
            with DATABASE.transaction():  # new added because of database locked
                cls.create(
                    username=username,
                    email=email,
                    password=generate_password_hash(password),
                    is_admin=admin
                )
        except IntegrityError:
            raise ValueError('User already exists')

    class Meta:
        database = DATABASE
        order_by = ('-joined_at',)  # need to be tuple and comma
        table_name = 'user'

    # select the posts that we want (these are all the posts that belong to a centain user)
    def get_posts(self):
        return Post.select().where(Post.user == self)

    # get change later
    def get_stream(self):
        return Post.select().where(
            # where I'm following and mine
            (Post.user << self.following()) |
            (Post.user == self)
        )

    def following(self):
        '''The users that we are following.'''
        return (
            User.select().join(
                Relationship, on=Relationship.to_user
            ).where(
                Relationship.from_user == self
            )
        )

    def followers(self):
        '''Get users following the current user'''
        return (
            User.select().join(
                Relationship, on=Relationship.from_user
            ).where(
                Relationship.to_user == self
            )
        )

class Post(Model):
    timestamp = DateTimeField(default=datetime.datetime.now)
    # ForeignKeyField - A field that points to another database record.
    user = ForeignKeyField(
        model={User},  # added
        rel_model=User,  # point to the User model
        related_name='posts'  # 給定一個反向引用名稱
        # backref is the correct way -- related_name was used prior to Peewee 3.0 and is deprecated, but they have the same effect.
    )
    content = TextField()

    class Meta:
        database = DATABASE
        order_by = ('-timestamp',)  # need to be tuple and comma
        table_name = 'post'

class Relationship(Model):
    from_user = ForeignKeyField(User, related_name='relationships')
    to_user = ForeignKeyField(User, related_name='related_to')

    class Meta:
        database = DATABASE
        table_name = 'relationship'
        # index tells the databases how to find the data to remember the data
        # it also allows us to specify whether or not a index is unique
        indexes = (
            (('from_user', 'to_user'), True),  # each index is a tupple, unique=True
        )

# 確認為使用者後才執行
def initialize():
    DATABASE.connect()
    DATABASE.create_tables([User, Post, Relationship], safe=True)
    DATABASE.close()

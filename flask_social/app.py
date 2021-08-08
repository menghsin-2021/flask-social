#g: A global object that Flask uses for passing information between views and modules.
from flask import (Flask, g, render_template, flash, redirect, url_for, abort)
from flask_bcrypt import check_password_hash
from flask_login import (LoginManager, login_user, logout_user,
                         login_required, current_user)

# LoginManager- An appliance to handle user authentication.

# login_user- Function to log a user in and set the appropriate cookie
# so they'll be considered authenticated by Flask-Login

import forms
import models

# 主機、PORT 變數
DEBUG = True
PORT = 5000
HOST = 'localhost'

app = Flask(__name__)
app.secret_key = 'aaaaaaaaaaaaaaabbbbbbbbbbbbbbbbbbccccccccccccccc'

# create login manager for handling user authentication
login_manager = LoginManager()
# set up the log in manager for our application
login_manager.init_app(app)
# if not login redirect them somewhere to log in, so cll the view log in
login_manager.login_view = 'login'  # app.route log function


# A decorator to mark the function responsible for loading a user from whatever data source we use.
# A function that the login manager will use when it needs to look up a user.
# 先找看看有沒有該使用者的資料
@login_manager.user_loader
def load_user(userid):
    try:
        return  models.User.get(models.User.id == userid)
    # from models which imports peewee
    except models.DoesNotExist:
        return None


# A decorator to mark a function as running before the request hits a view.
# 再送 request 前先連線到資料庫
@app.before_request
def before_request():
    '''Connect to the database brfore each request.'''
    g.db = models.DATABASE
    g.db.connect()
    g.user = current_user  # to find the current user

# A decorator to mark a function as running before the response is returned.
# 送完後關閉資料庫，並在接收 response 後往下傳遞
@app.after_request
def after_request(response):
    '''Close the database connection after each request.'''
    g.db.close()
    return response

# for sign up
@app.route('/register', methods=('GET', 'POST'))
def register():
    form = forms.RegisterForm()
    # 如果 forms 的 RegisterForm class 成功運行，表示 validation 通過則:
    # automatically check if the data in the form is valid in a POST request
    if form.validate_on_submit():  # link to forms.RegisterForm().validators[...]
        flash('Yaeh, you registered!', 'success')  # flash 第二個欄位是 category
        # 將使用者輸入的 username/password 存到資料庫
        models.User.create_user(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
        )
        return redirect(url_for('index'))  # 登入成功：導到 index
    return render_template('register.html', form=form)  # 反之則導到 register 頁面

@app.route('/login', methods=('GET', 'POST'))
def login():
    form = forms.LoginForm()
    if form.validate_on_submit():
        try:
            user = models.User.get(models.User.email == form.email.data)
        except models.DoesNotExist:
            flash("Your email or password doesn't match!", "error")  # 混淆駭客 其實只是沒有 email
        else:
            if check_password_hash(user.password, form.password.data):
                login_user(user)
                # flask_login function, creating sessions on the user's browser, and giving them a cookie which reference their user account
                flash("You've been logged in", "success")
                return redirect(url_for('index'))
            else:
                flash("Your email or password doesn't match!", "error")
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required  # 和 app.route先後有差
def logout():
    logout_user()  # flask_logout function, delete the user account reference cookie
    flash("You've been logged out! Come back soon", "success")
    return redirect(url_for('index'))

@app.route('/new_post', methods=('GET', 'POST'))
@login_required
def post():
    form = forms.PostForm()
    if form.validate_on_submit():
        # use current user function
        models.Post.create(user=g.user._get_current_object(),
                           content=form.content.data.strip())
        flash("Message posted! Thanks!", "success" )
        return redirect(url_for('index'))
    return render_template('post.html', form=form)


@app.route('/')
def index():
    stream = models.Post.select().limit(100)
    return render_template('stream.html', stream=stream)

@app.route('/stream')
@app.route('/stream/<username>')
def stream(username=None):
    template = 'stream.html'
    if username and username != current_user.username:
        try:
            # ** does a comparison without caring about case
            user = models.User.select().where(models.User.username**username).get()
            stream = user.posts.limit(100)  # Post.user.related_name 一個反向取值的名稱 他名字亂取 所以混淆
        except models.DoesNotExist:
            abort(404)
    else:
        # 把 post 資料表中的資料都取出來
        stream = current_user.get_stream().limit(100)
        user = current_user
    if username:
        template = 'user_stream.html'
    return render_template(template, stream=stream, user=user)

@app.route('/post/<int:post_id>')
def view_post(post_id):
    posts = models.Post.select().where(models.Post.id == post_id)
    if posts.count() == 0:
        abort(404)
    return render_template('stream.html', stream=posts)

@app.route('/follow/<username>')
@login_required
def follow(username):
    try:
        to_user = models.User.get(models.User.username**username)
    except models.DoesNotExist:
        abort(404)
    else:
        try:
            models.Relationship.create(
                from_user=g.user._get_current_object(),
                to_user=to_user
            )
        except models.IntegrityError:
            pass
        else:
            flash("You're now following {}!".format(to_user.username), "success")

    return redirect(url_for('stream', username=to_user.username))

@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
    try:
        to_user = models.User.get(models.User.username**username)
    except models.DoesNotExist:
        abort(404)
    else:
        try:
            models.Relationship.get(
                from_user=g.user._get_current_object(),
                to_user=to_user
            ).delete_instance()
        except models.IntegrityError:
            pass
        else:
            flash("You've unfollowed {}!".format(to_user.username), "success")

    return redirect(url_for('stream', username=to_user.username))

# abort(404)
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


if __name__ == '__main__':
    models.initialize()
    # 先建立一個管理員帳號
    try:
        models.User.create_user(
            username='Jason',
            email='jason@teamtreehouse.com',
            password='password',
            admin=True
        )
    except ValueError:
        pass
    app.run(debug=DEBUG, host=HOST, port=PORT)
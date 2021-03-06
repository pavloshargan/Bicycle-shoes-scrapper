import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from my_package import app, db, bcrypt, mail
from my_package.forms import (RegistrationForm, LoginForm, UpdateAccountForm,
                              RequestResetForm, ResetPasswordForm, SearchForm)
from my_package.models import User, Shoe
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
import pygal
from sqlalchemy import or_

@app.route("/")
@app.route("/shoes", methods=['GET', 'POST'])
def shoes():
    t = "my_title"
    form = SearchForm()
    page = request.args.get('page', 1, type=int)
    shoes = Shoe.query.order_by(Shoe.Date.desc()).paginate(page=page, per_page=20)

    if form.is_submitted():
        t="yes bos"
        target_size_from = 36
        target_size_to = 52
        
        if form.size_from.data:  
            target_size_from = float(form.size_from.data)
        if form.size_to.data:  
            target_size_to = float(form.size_to.data)
        target_price_from = 0
        target_price_to = 9999999
        if form.price_from.data:  
            target_price_from = float(form.price_from.data)
        if form.price_to.data:  
            target_price_to = float(form.price_to.data)
        target_query = ""
        if form.query.data:
            target_query = form.query.data
        shoes = Shoe.query.filter(Shoe.Size >= target_size_from, Shoe.Size <= target_size_to).filter(Shoe.Price >= target_price_from, Shoe.Price <= target_price_to).filter(or_(Shoe.Title.contains(target_query),Shoe.Description.contains(target_query)) ).paginate(page=page, per_page=20)

    return render_template('shoes.html', shoes=shoes, form=form, title=t)

# @app.route("/shoes_update")
# def update_shoes():

    

@app.route("/about")
def about():
    return render_template('about.html', title='About')


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('shoes'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('shoes'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('shoes'))


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form)


# @app.route("/post/new", methods=['GET', 'POST'])
# @login_required
# def new_post():
#     form = PostForm()
#     if form.validate_on_submit():
#         post = Post(title=form.title.data, content=form.content.data, author=current_user)
#         db.session.add(post)
#         db.session.commit()
#         flash('Your post has been created!', 'success')
#         return redirect(url_for('home'))
#     return render_template('create_post.html', title='New Post',
#                            form=form, legend='New Post')



# @app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
# @login_required
# def update_post(post_id):
#     post = Post.query.get_or_404(post_id)
#     if post.author != current_user:
#         abort(403)
#     form = PostForm()
#     if form.validate_on_submit():
#         post.title = form.title.data
#         post.content = form.content.data
#         db.session.commit()
#         flash('Your post has been updated!', 'success')
#         return redirect(url_for('post', post_id=post.id))
#     elif request.method == 'GET':
#         form.title.data = post.title
#         form.content.data = post.content
#     return render_template('create_post.html', title='Update Post',
#                            form=form, legend='Update Post')


# @app.route("/post/<int:post_id>/delete", methods=['POST'])
# @login_required
# def delete_post(post_id):
#     post = Post.query.get_or_404(post_id)
#     if post.author != current_user:
#         abort(403)
#     db.session.delete(post)
#     db.session.commit()
#     flash('Your post has been deleted!', 'success')
#     return redirect(url_for('home'))


# @app.route("/user/<string:username>")
# def user_posts(username):
#     page = request.args.get('page', 1, type=int)
#     user = User.query.filter_by(username=username).first_or_404()
#     posts = Post.query.filter_by(author=user)\
#         .order_by(Post.date_posted.desc())\
#         .paginate(page=page, per_page=5)
#     return render_template('user_posts.html', posts=posts, user=user)


def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender='noreply@demo.com',
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('reset_token', token=token, _external=True)}
If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)


@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title='Reset Password', form=form)


# @app.route('/graph/')
# def pygalexample():
#     graph = pygal.Line()
#     graph.title = '% Change Coolness of programming languages over time.'
#     graph.x_labels = ['2011','2012','2013','2014','2015','2016']
#     graph.add('Python',  [15, 31, 89, 200, 356, 900])
#     graph.add('Java',    [15, 45, 76, 80,  91,  95])
#     graph.add('C++',     [5,  51, 54, 102, 150, 201])
#     graph.add('All others combined!',  [5, 15, 21, 55, 92, 105])
#     graph_data = graph.render_data_uri()
#     return render_template("graph.html", graph_data = graph_data)



from flask import Blueprint, redirect, url_for, request, render_template, flash
from flask_login import login_user, logout_user, current_user

from werkzeug.security import generate_password_hash, check_password_hash

from manager.models import db, User

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=["GET", "POST"])
def login():

    if request.method == "GET":
        # return """<form method=post>
        # Email: <input name="email"><br>
        # Password: <input name="password" type=password><br>
        # <button>Log In</button>
        # </form>"""
        return render_template('auth/login.html', user=current_user)

    if request.method == "POST":

        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        user = User.query.filter_by(email=email).first()

        print("testing user")
        print(user)
        print(user.password)
        print(check_password_hash(user.password, password))

        if user is None or not check_password_hash(user.password, password):
            flash('Please check your login details and try again.')
            return redirect(url_for("auth.login"))

        login_user(user, remember=remember)
        return redirect(url_for("manager.index"))

@auth.route('/signup', methods=['GET', 'POST'])
def signup():

    if request.method == "GET":
        return render_template('auth/signup.html', user=current_user)

    if request.method == "POST":
        # code to validate and add user to database goes here
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')

        print(email)
        print(name)
        print(password)

        user = User.query.filter_by(email=email).first() # if this returns a user, then the email already exists in database
        print(user)

        if user: # if a user is found, we want to redirect back to signup page so user can try again
            flash('Email address already exists')
            return redirect(url_for('auth.signup'))

        # create a new user with the form data. Hash the password so the plaintext version isn't saved.
        new_user = User(email=email, name=name, password=generate_password_hash(password, method='pbkdf2:sha256'))

        print(new_user)

        # add the new user to the database
        db.session.add(new_user)
        db.session.commit()

        print("committed")
        flash("user created, you can now sign in")

        return redirect(url_for('auth.login'))

@auth.route('/logout')
def logout():
    logout_user()
    return redirect(url_for("manager.index"))

from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from flask_login import login_user, login_required, logout_user, current_user

auth = Blueprint('auth', __name__)  # sets up a Blueprint for flask application
#using JINGA, we can pass values to the templates and use them inside the templates
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')           #email from the form sent
        password = request.form.get('password')     #password from the form sent

        userDocument = db.usersCollection.find_one( { "email" : email })   #finding email from database that matches one on form sent
        user = User.documentToUserInst(userDocument)                    #from to userInstance, this is now user from DB
        
        if user:
            if check_password_hash(userDocument.get('password'), password):     #(DB password for email, password entered in form)
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')

    return render_template("login.html", user=current_user)

@auth.route('/logout')
@login_required #decorator that makes sure you can't access route unless user is logged in
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        firstName = request.form.get('firstName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
    
        user = db.usersCollection.find_one( { "email" : email })
        if user:
            flash('Email already exists.', category='error')
        elif len(email) < 4:
            flash('Email must be greater than 3 characters.', category='error')
        elif len(firstName) < 2:
            flash('First name must be greater then 1 character.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        elif len(password1) < 7:
            flash('Password must be at least 7 characters.', category='error')
        else:
            password1 = generate_password_hash(password1,method='pbkdf2:sha256')
            newUser = User(email = email, firstName = firstName, password = password1)
            
            newUserDocument = newUser.create_document()
            db.usersCollection.insert_one(newUserDocument)

            login_user(newUser, remember=True)
            flash('Account created!', category='success')
            return redirect(url_for('views.home')) #returning the url for what maps to the home function in views

    return render_template("sign_up.html", user=current_user)
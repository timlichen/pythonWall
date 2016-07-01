from flask import Flask, render_template, redirect, request, session, flash
from mysqlconnection import MySQLConnector
import process
import re
from flask_bcrypt import Bcrypt
app = Flask(__name__)
app.secret_key = "yeeee"
bcrypt = Bcrypt(app)
mySql = MySQLConnector(app, 'the_wall')

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9\.\+_-]+@[a-zA-Z0-9\._-]+\.[a-zA-Z]*$')
number_check = re.compile(r'^[a-zA-Z]+$')

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    errFlag = False

    if not number_check.match(request.form['first_name']):
        flash("Only letters can be used in first name!")
        errFlag = False
    if not number_check.match(request.form['last_name']):
        flash("Only letters can be used in last name!")
        errFlag = True
    if len(request.form['email']) < 1:
        flash("Email cannot be blank!")
        errFlag = True
    if not EMAIL_REGEX.match(request.form['email']):
        flash("Invalid Email Address!")
        errFlag = True
    if len(request.form['first_name']) < 1:
        flash("First name cannot be blank!")
        errFlag = True
    if len(request.form['last_name']) < 1:
        flash("Last name cannot be blank!")
        errFlag = True
    if len(request.form['password']) < 1:
        flash("Password cannot be blank!")
        errFlag = True
    if not request.form['password'] == request.form['cPassword']:
        flash("Passwords don't match!")
        errFlag = True

    if not errFlag:
        password = request.form['password']
        pw_hash = bcrypt.generate_password_hash(password)
        insert_query = "INSERT INTO users (email, first_name, last_name, password, created_at, updated_at) VALUES (:email, :first_name, :last_name, :password, NOW(), NOW())"
        q_data = {
            'email': request.form['email'],
            'first_name': request.form['first_name'],
            'last_name': request.form['last_name'],
            'password': pw_hash
        }
        mySql.query_db(insert_query, q_data)

        flash("Successfully Registered!")

    return redirect('/')

@app.route('/login', methods=['POST'])
def login():
    errFlag = False
    if not EMAIL_REGEX.match(request.form['email']):
        flash("Invalid Email Address!")
        errFlag = True

    if len(request.form['password']) < 1:
        flash("Password cannot be blank!")
        errFlag = True

    if not errFlag:
        password = request.form['password']
        login_query = "SELECT * from users WHERE email = :email LIMIT 1"
        data = {
            'email': request.form['email']
        }
        login_data = mySql.query_db(login_query, data)

        if len(login_data) == 1:
            try:
                bcrypt.check_password_hash(login_data[0]['password'], password)
                session['user_id'] = login_data[0]['id']
                flash("Successfully Logged In!")
                return redirect('/theWall')
            except:
                flash("Failed to Login!")
                return redirect('/')
    else:
        return redirect('/')

@app.route('/theWall')
def theWall():
    query = "SELECT messages.id AS messageID, messages.message, messages.user_id, messages.created_at, users.first_name, users.last_name FROM messages LEFT JOIN users on messages.user_id = users.id"
    query2 = "SELECT comments.id AS comment_id, comments.comment, comments.user_id, comments.message_id, comments.user_id, users.id, users.first_name, users.last_name FROM comments LEFT JOIN users on comments.user_id = users.id"
    messages = mySql.query_db(query)
    comments = mySql.query_db(query2)
    # print comments
    return render_template('wall.html', all_messages = messages, all_comments = comments)

@app.route('/createMessage', methods=['POST'])
def postMessage():
    # print session['user_id']
    query = "INSERT INTO messages (user_id, message, created_at, updated_at) VALUES (:user_id, :message, NOW(), NOW())"
    data = {
        'message': request.form['message'],
        'user_id': session['user_id']
    }
    mySql.query_db(query, data)
    return redirect('/theWall')

@app.route('/comment', methods=['POST'])
def postComment():
    query = "INSERT INTO comments (message_id, user_id, comment, created_at, updated_at) VALUES (:message_id, :user_id, :comment, NOW(), NOW())"
    data = {
        'user_id': session['user_id'],
        'message_id': request.form['message_id'],
        'comment': request.form['comment']
    }
    mySql.query_db(query, data)
    return redirect('/theWall')

@app.route('/logOff')
def clearSession():
    session.clear()
    return redirect('/')

@app.route('/delete', methods=['POST'])
def deleteMessage():
    # PYTHON ENFORCES REFERENTIAL INTENGRITY
    query1 = "DELETE FROM comments WHERE message_id = :message_id"
    query2= "DELETE FROM messages WHERE id = :message_id"
    data = {"message_id": request.form['messageID']}
    mySql.query_db(query1, data)
    mySql.query_db(query2, data)
    return redirect('/theWall')

@app.route('/deleteComment', methods=['POST'])
def deleteComment():
    query = "DELETE FROM comments where id = :comment_id"
    data = { "comment_id": request.form['commentID'] }
    print data
    mySql.query_db(query, data)
    return redirect('/theWall')
app.run(debug=True)

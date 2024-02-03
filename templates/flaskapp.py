import sqlite3
from flask import Flask, request, g, render_template, send_file

DB_PATH = '/var/www/html/flaskapp/example.db'

webapp = Flask(__name__)
webapp.config['DATABASE'] = DB_PATH

def db_connect():
    return sqlite3.connect(webapp.config['DATABASE'])

def retrieve_db():
    database = getattr(g, '_database', None)
    if database is None:
        database = g._database = db_connect()
    return database

@webapp.teardown_appcontext
def close_db_connection(exception):
    database = getattr(g, '_database', None)
    if database is not None:
        database.close()

def run_query(query, parameters=()):
    cursor = retrieve_db().execute(query, parameters)
    fetched_rows = cursor.fetchall()
    cursor.close()
    return fetched_rows

def save_changes():
    retrieve_db().commit()

@webapp.route("/")
def home():
    run_query("DROP TABLE IF EXISTS members")
    run_query("CREATE TABLE members (username TEXT, password TEXT, firstname TEXT, lastname TEXT, email TEXT, wordcount INTEGER)")
    return render_template('home.html')

@webapp.route('/user_login', methods=['POST', 'GET'])
def user_login():
    alert = ''
    if request.method == 'POST' and str(request.form['username']) and str(request.form['password']):
        user = str(request.form['username'])
        passcode = str(request.form['password'])
        fetch_result = run_query("""SELECT firstname, lastname, email, wordcount FROM members WHERE username = (?) AND password = (?)""", (user, passcode))
        if fetch_result:
            for record in fetch_result:
                return display_info(record[0], record[1], record[2], record[3])
        else:
            alert = 'Wrong username or password!'
    elif request.method == 'POST':
        alert = 'Enter your username and password.'
    return render_template('login.html', alert=alert)

@webapp.route('/user_registration', methods=['GET', 'POST'])
def user_registration():
    alert = ''
    if request.method == 'POST' and all(str(request.form[field]) for field in ['username', 'password', 'firstname', 'lastname', 'email']):
        user = str(request.form['username'])
        passcode = str(request.form['password'])
        first_name = str(request.form['firstname'])
        last_name = str(request.form['lastname'])
        mail = str(request.form['email'])
        file_content = request.files['textfile']
        if not file_content:
            file_name, word_count = None, None
        else:
            file_name = file_content.filename
            word_count = count_words(file_content)
        check_user = run_query("""SELECT * FROM members WHERE username = (?)""", (user,))
        if check_user:
            alert = 'Username already exists!'
        else:
            run_query("""INSERT INTO members (username, password, firstname, lastname, email, wordcount) VALUES (?, ?, ?, ?, ?, ?)""", (user, passcode, first_name, last_name, mail, word_count))
            save_changes()
            fetch_user = run_query("""SELECT firstname, lastname, email, wordcount FROM members WHERE username = (?) AND password = (?)""", (user, passcode))
            if fetch_user:
                for record in fetch_user:
                    return display_info(record[0], record[1], record[2], record[3])
    elif request.method == 'POST':
        alert = 'Please fill in all fields!'
    return render_template('register.html', alert=alert)

@webapp.route("/file_download")
def file_download():
    file_path = "Limerick.txt"
    return send_file(file_path, as_attachment=True)

def count_words(file):
    content = file.read()
    words = content.split()
    return len(words)

def display_info(first_name, last_name, mail, word_count):
    return """ First Name :  """ + first_name + """ <br> Last Name : """ + last_name + """ <br> Email : """ + mail + """ <br> Word Count : """ + str(word_count) + """ <br><br> <a href="/file_download" >Download File</a> """

if __name__ == '__main__':
    webapp.run()


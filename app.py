import hmac
import sqlite3
import datetime

from flask import Flask, request
from flask_jwt import JWT, jwt_required, current_identity
from flask_cors import CORS
from flask_mail import Mail, Message


class User(object):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password


def fetch_users():
    with sqlite3.connect('project.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user")
        users = cursor.fetchall()

        new_data = []

        for data in users:
            new_data.append(User(data[0], data[3], data[4]))
    return new_data


def init_user_table():
    conn = sqlite3.connect('project.db')
    print("Opened database successfully")
    # creating user table
    conn.execute("CREATE TABLE IF NOT EXISTS user(user_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                 "first_name TEXT NOT NULL,"
                 "last_name TEXT NOT NULL,"
                 "username TEXT NOT NULL,"
                 "password TEXT NOT NULL)")
    print("user table created successfully")
    conn.close()


def init_comic_table():
    with sqlite3.connect('project.db') as conn:
        # creating product table
        conn.execute("CREATE TABLE IF NOT EXISTS comics(id INTEGER PRIMARY KEY AUTOINCREMENT,"
                     "title TEXT NOT NULL,"
                     "description TEXT NOT NULL,"
                     "price TEXT NOT NULL,"
                     "category TEXT NOT NULL,"
                     "era TEXT NOT NULL,"
                     "date_created TEXT NOT NULL)")
    print("comics table created successfully.")


def init_character_table():
    with sqlite3.connect('project.db') as conn:
        # creating characters table
        conn.execute("CREATE TABLE IF NOT EXISTS characters (id INTEGER PRIMARY KEY AUTOINCREMENT,"
                     "name TEXT NOT NULL,"
                     "alias TEXT NOT NULL,"
                     "debut TEXT NOT NULL,"
                     "species TEXT NOT NULL,"
                     "universe TEXT NOT NULL,"
                     "powers_abilities TEXT NOT NULL,"
                     "quote TEXT NOT NULL,"
                     "description TEXT NOT NULL)")
    print("characters table created successfully.")


init_user_table()
init_comic_table()
init_character_table()

users = fetch_users()


username_table = {u.username: u for u in users}
userid_table = {u.id: u for u in users}


def authenticate(username, password):
    user = username_table.get(username, None)
    if user and hmac.compare_digest(user.password.encode('utf-8'), password.encode('utf-8')):
        return user


def identity(payload):
    user_id = payload['identity']
    return userid_table.get(user_id, None)


app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'super-secret'
# allows an extension on the token time limit
app.config['JWT_EXPIRATION_DELTA'] = datetime.timedelta(seconds=4000)
CORS(app)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = "fledermausdevin@gmail.com"
app.config['MAIL_PASSWORD'] = "Fleddy97"
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

jwt = JWT(app, authenticate, identity)


@app.route('/protected')
@jwt_required()
def protected():
    return '%s' % current_identity


# Function to register users
@app.route('/registration/', methods=["POST"])
def user_registration():
    response = {}

    if request.method == "POST":

        first_name = request.form['first_name']
        last_name = request.form['last_name']
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        with sqlite3.connect("project.db") as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO user("
                           "first_name,"
                           "last_name,"
                           "username,"
                           "password) VALUES(?, ?, ?, ?)", (first_name, last_name, username, password))
            conn.commit()
            response["message"] = "success"
            response["status_code"] = 201

            if response['status_code'] == 201:
                msg = Message('success', sender='fledermausdevin@gmail.com', recipients=[email])
                msg.body = 'Registration successful.'
                mail.send(msg)
                return "Message sent"


# Function to add products to the cart
@app.route('/add-comic/', methods=["POST"])
@jwt_required()
def add_product():
    response = {}

    if request.method == "POST":
        try:
            title = request.form['title']
            description = request.form['description']
            price = request.form['price']
            category = request.form['category']
            era = request.form['era']
            date_created = datetime.datetime.now()
            with sqlite3.connect('project.db') as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO comics("
                               "title,"
                               "description,"
                               "price,"
                               "category,"
                               "era,"
                               "date_created) VALUES(?, ?, ?, ?, ?, ?)", (title, description, price, category, era, date_created))
                conn.commit()
                response["status_code"] = 201
                response['description'] = "Product added successfully"
        except Exception as x:
            conn.rollback()
            response['description'] = "Error occurred adding comic: " + str(x)
        finally:
            conn.close()
            return response


# function to view the entire cart
@app.route('/view-all/', methods=["GET"])
def get_cart():
    response = {}
    with sqlite3.connect("project.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM comics")

        products = cursor.fetchall()

    response['status_code'] = 200
    response['data'] = products
    return response


# function to remove a product from cart
@app.route("/remove-comic/<int:product_id>")
@jwt_required()
def remove_product(product_id):
    response = {}
    with sqlite3.connect("project.db") as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM comics WHERE id=" + str(product_id))
        conn.commit()
        response['status_code'] = 200
        response['message'] = "Product removed successfully."
    return response


# function to edit a specific characteristic of a product
@app.route('/edit-comic/<int:product_id>/', methods=["PUT"])
@jwt_required()
def edit_product(product_id):
    response = {}

    if request.method == "PUT":
        with sqlite3.connect('project.db') as conn:
            incoming_data = dict(request.json)
            put_data = {}

            if incoming_data.get("title") is not None:
                put_data["title"] = incoming_data.get("title")
                with sqlite3.connect('project.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE comics SET title =? WHERE id=?", (put_data["title"], product_id))
                    conn.commit()

                    response['message'] = "Update to title was successful"
                    response['status_code'] = 200
            if incoming_data.get("description") is not None:
                put_data['description'] = incoming_data.get('description')

                with sqlite3.connect('project.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE comics SET description =? WHERE id=?", (put_data["description"], product_id))
                    conn.commit()

                    response["description"] = "Update to description successful"
                    response["status_code"] = 200
            if incoming_data.get("price") is not None:
                put_data['price'] = incoming_data.get('price')

                with sqlite3.connect('project.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE comics SET price =? WHERE id=?", (put_data["price"], product_id))
                    conn.commit()

                    response["price"] = "Update to price was successful"
                    response["status_code"] = 200
            if incoming_data.get("category") is not None:
                put_data['category'] = incoming_data.get('category')

                with sqlite3.connect('project.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE comics SET category =? WHERE id=?", (put_data["category"], product_id))
                    conn.commit()

                    response["category"] = "Update to category was successful"
                    response["status_code"] = 200
            if incoming_data.get("era") is not None:
                put_data['era'] = incoming_data.get('era')

                with sqlite3.connect('project.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE comics SET era =? WHERE id=?", (put_data["era"], product_id))
                    conn.commit()

                    response["era"] = "Update to era was successful"
                    response["status_code"] = 200
    return response


# Function to add character to the cart
@app.route('/add-character/', methods=["POST"])
@jwt_required()
def add_character():
    response = {}

    if request.method == "POST":
        try:
            name = request.form['name']
            alias = request.form['alias']
            debut = request.form['debut']
            species = request.form['species']
            universe = request.form['universe']
            powers_abilites = request.form['powers_abilities']
            quote = request.form['quote']
            description = request.form['description']
            with sqlite3.connect('project.db') as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO comics("
                               "name,"
                               "alias,"
                               "debut,"
                               "species,"
                               "universe,"
                               "powers_abilities,"
                               "quote,"
                               "description) VALUES(?, ?, ?, ?, ?, ?, ?, ?)", (name, alias, debut, species, universe, powers_abilites, quote, description))
                conn.commit()
                response["status_code"] = 201
                response['description'] = "Character added successfully"
        except Exception as x:
            conn.rollback()
            response['description'] = "Error occurred adding character: " + str(x)
        finally:
            conn.close()
            return response


# function to view the entire cart
@app.route('/view-characters/', methods=["GET"])
def get_characters():
    response = {}
    with sqlite3.connect("project.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM characters")

        characters = cursor.fetchall()

    response['status_code'] = 200
    response['data'] = characters
    return response


# function to remove a product from cart
@app.route("/remove-character/<int:character_id>")
@jwt_required()
def remove_character(character_id):
    response = {}
    with sqlite3.connect("project.db") as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM characters WHERE id=" + str(character_id))
        conn.commit()
        response['status_code'] = 200
        response['message'] = "Character removed successfully."
    return response


# running program
if __name__ == "__main__":
    app.run()

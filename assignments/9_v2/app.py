"""
    Assignment 9
    @author: Hans Ludvig Kleivdal
"""
import os
from flask import Flask, request, render_template, g, flash, redirect, url_for, session, send_from_directory
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

import json

UPLOAD_FOLDER = 'static'
ALLOWED_EXTENSIONS = ["txt", "pdf", "png", "jpg", "jpeg", "gif"]

app = Flask(__name__)
app.debug = True

# Application config
app.config["DATABASE_USER"] = "root"
app.config["DATABASE_PASSWORD"] = "admin"
app.config["DATABASE_DB"] = "test_storage"
app.config["DATABASE_HOST"] = "localhost"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.secret_key = "any random string"


class Database_product_info:

    def __init__(self, db):
        self.products = []
        self._load_products(db)

    def _load_products(self, db):

        db.ping(True)
        cur = db.cursor()

        try:
            sql = "select * from product_info;"
            cur.execute(sql)
            for i in cur:
                id, name, description, normal_price, bonus_price, photo = i
                self.products.append({
                    "id": id,
                    "name": name,
                    "description": description,
                    "normal_price": float(normal_price) if float(normal_price).is_integer() else None,
                    "bonus_price": float(bonus_price) if bonus_price else None,
                    "photo": photo
                })
        except mysql.connector.Error as err:
            print(err)
        finally:
            cur.close()
            db.close()

    def get_products(self):
        return self.products

    def get_product(self, id):
        for i in self.products:
            if int(id) == i['id']:
                return i
        return None
class Database_order:

    def __init__(self, db):
        self.orders = []
        self._load_orders(db)

    def _load_orders(self, db):

        db.ping(True)
        cur = db.cursor()

        try:
            sql = "select order_id, fname, lname, email, phone, street, postcode, city from order_head;"
            cur.execute(sql)
            for i in cur:
                id, fname, lname, email, phone, street, postcode, city = i
                self.orders.append({
                    "id": id,
                    "fname": fname,
                    "lname": lname,
                    "email": email,
                    "phone": phone,
                    "street": street,
                    "postcode": postcode,
                    "city": city
                })
        except mysql.connector.Error as err:
            print(err)
        finally:
            cur.close()
            db.close()

    def get_orders(self):
        return self.orders

    def get_order(self, id):
        for i in self.orders:
            if int(id) == i['id']:
                return i
        return None
class Database_order_list:

    def __init__(self, db):
        self.order_list = []
        self._load_order_list(db)

    def _load_order_list(self, db):

        db.ping(True)
        cur = db.cursor()

        try:
            sql = "select order_items.order_id, order_items.product_id, product_info.name, product_info.normal_price, product_info.bonus_price, order_items.qt from order_items inner join product_info on order_items.product_id=product_info.id;"
            cur.execute(sql)
            for i in cur:
                order_id, product_id, name, normal_price, bonus_price, qt= i
                self.order_list.append({
                    "order_id": order_id,
                    "product_id": product_id,
                    "name": name,
                    "normal_price": normal_price,
                    "bonus_price": bonus_price,
                    "qt": qt,
                    "sum": bonus_price * qt if bonus_price else normal_price * qt
                })
        except mysql.connector.Error as err:
            print(err)
            flash(err, "remove")
        finally:
            cur.close()
            db.close()

    def get_orders(self):
        return self.order_list

    def get_order(self, id):
        id_orders = []
        for i in self.order_list:
            if int(id) == i['order_id']:
                id_orders.append(i)
        return id_orders

def get_db():
    if not hasattr(g, "_database"):
        g._database = mysql.connector.connect(host=app.config["DATABASE_HOST"], user=app.config["DATABASE_USER"],
                                              password=app.config["DATABASE_PASSWORD"], database=app.config["DATABASE_DB"])
    return g._database


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

with app.app_context():
    app.config["PRODUCTS"] = Database_product_info(get_db())
    app.config["ORDERS"] = Database_order(get_db())
    app.config["ORDER_LIST"] = Database_order_list(get_db())


@app.route("/")
def index():
    return redirect(url_for('login'))

@app.route("/product/<id>") #not done
def product(id):
    db = app.config["PRODUCTS"]

    return render_template("product.html", username=session.get("username", None), product=db.get_product(id))

@app.route("/statistics")
def statistics():
    db = get_db()
    db.ping(True)
    cur = db.cursor()

    try:
        sta = []
        sql = "select order_items.product_id, product_info.name, product_info.normal_price, product_info.bonus_price, sum(order_items.qt) as Quantity from order_items inner join product_info on order_items.product_id=product_info.id group by order_items.product_id;"
        cur.execute(sql)
        for i in cur:
            id, name, price, bonus_price, qt = i
            sta.append({
                "id": id,
                "name": name,
                "price": price,
                "bonus_price": bonus_price,
                "qt": qt
            })
        return render_template("statistics.html", sta=sta, username=session.get("username", None))

    except mysql.connector.Error as err:
        flash(err, "remove")
    finally:
        cur.close()
        db.close()

@app.route("/products")
def products():

    db = app.config["PRODUCTS"]
    print(db.get_products())

    return render_template("products.html", products=db.get_products(), username=session.get("username", None))

@app.route("/orders")
def orders():

    db = app.config["ORDERS"]

    return render_template("orders.html", orders=db.get_orders(), username=session.get("username", None))

@app.route("/order/<id>")
def order(id):
    db_order = app.config["ORDERS"]
    db_order_list = app.config["ORDER_LIST"]
    order_list = db_order_list.get_order(id)

    total = 0
    for i in order_list:
        total += i["sum"]

    return render_template("order.html", order_info=db_order.get_order(id), order_list=order_list, total=total, username=session.get("username", None))



@app.route("/edit/<id>")
def edit(id):
    products = app.config["PRODUCTS"]
    if id:
        return render_template("edit.html", product=products.get_product(id), username=session.get("username", None))
    else:
        flash("Product to not exist")


@app.route("/submit", methods=['POST'])
def submit():
    db = app.config["PRODUCTS"]
    id = request.form.get("id")
    name = request.form.get("name")
    desc = request.form.get("description")
    price = request.form.get("normal_price")
    bonus_price = request.form.get("bonus_price")
    curent_product = db.get_product(id)
    file = request.files["file"]
    new_photo = False

    if file.filename == "":
        file = curent_product["photo"]
        new_photo = False
    else:
        new_photo = True

    print(new_photo)
    print(file)
    if bonus_price == "":
        bonus_price = None
    else:
        bonus_price = float(bonus_price)

    product = db.get_product(id)

    if int(id) == product['id'] and name == product['name'] and desc == product['description'] and float(price) == product['normal_price'] and bonus_price == product['bonus_price'] and file == product["photo"]: # feil HERRRR!!!!!!!!
        flash("Noting to update!", "remove")
        print("NO UPDATE")

        return redirect(url_for('products'))
    else:
        if bonus_price == None:
            bonus_price = "NULL"
        if new_photo:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                photo = "../"+path
                sub = db_update_product(id, name, desc, price, bonus_price, photo)
                if sub is True:
                    file.save(path)
                    flash("Product #" + id + " updated!", "set")
                    return redirect(url_for('products'))
                else:
                    return redirect(url_for('products'))
        else:
            sub = db_update_product(id, name, desc, price, bonus_price, file)
            if sub is True:
                flash("Product #" + id + " updated!", "set")
                return redirect(url_for('products'))
            else:
                return redirect(url_for('products'))


@app.route("/add")
def add():
    return render_template("add.html", username=session.get("username", None))


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route("/add_product", methods=['POST'])
def add_product():
    name = request.form.get("name")
    desc = request.form.get("description")
    price = request.form.get("normal_price")
    bonus_price = request.form.get("bonus_price")
    file = request.files["file"]
    print(file)
    print(file.filename)

    db = app.config["PRODUCTS"]

    if file and allowed_file(file.filename):
        # "secure" the filename (form input may be forged and filenames can be dangerous)
        filename = secure_filename(file.filename)
        # save the file to the upload folder
        path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        print(path)
        if bonus_price == "":
            bonus_price = "NULL"
        print("bonus: " + bonus_price)
        db_add = db_add_product(name, desc, price, bonus_price, path)
        if db_add:
            file.save(path)
            flash("File uploaded", "set")
            return redirect(url_for("products"))
        else:
            return redirect(url_for("products"))
    else:
        flash("Not allowed file type", "set")
        return redirect(url_for("products"))


@app.route("/delete/<id>")
def delete(id):
    db_del = db_delete_product(id)
    if db_del:
        flash("Product #" + id + " has been removed", "remove")
        return redirect(url_for('products'))
    else:
        return redirect(url_for('products'))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":  # if the form was submitted (otherwise we just display form)
        if valid_login(request.form["username"], request.form["password"]):
            session["username"] = request.form["username"]
            return redirect(url_for("products"))
        else:
            flash("Invalid username or password!", "remove")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("username")
    flash("You are now logged out!", "set")
    return redirect(url_for("login"))


def valid_login(username, password):
    """Checks if username-password combination is valid."""
    db = get_db()
    db.ping(True)
    cur = db.cursor()

    try:
        sql = "SELECT password FROM users WHERE user_name = '{}';".format(username)
        cur.execute(sql)
        for i in cur:
            return check_password_hash(i[0], password)
        return False
    except mysql.connector.Error as err:
        flash(err, "set")
        return False
    finally:
        cur.close()
        db.close()

def db_delete_product(id):
    db = get_db()
    db.ping(True)
    cur = db.cursor()

    try:
        sql = "DELETE FROM product_info WHERE id={};".format(id)
        cur.execute(sql)
        db.commit()
        return True
    except mysql.connector.Error as err:
        flash(err, "remove")
        print(err)
        return False
    finally:
        cur.close()
        db.close()
        app.config["PRODUCTS"] = Database_product_info(get_db())


def db_update_product(id, name, desc, price, bonus_price, photo):
    db = get_db()
    db.ping(True)
    cur = db.cursor()

    try:
        sql = "UPDATE product_info SET name='{}', description='{}', normal_price='{}', bonus_price={}, photo='{}' WHERE id={};".format(name, desc, price, bonus_price, photo, id)
        print(sql)
        cur.execute(sql)
        db.commit()
        print("TRY")
        return True
    except mysql.connector.Error as err:
        flash(err, "remove")
        print(err)
        print("FAIL")
        return False
    finally:
        cur.close()
        db.close()
        app.config["PRODUCTS"] = Database_product_info(get_db())

def db_add_product(name, desc, price, bonus_price, img):
    db = get_db()
    db.ping(True)
    cur = db.cursor()

    try:
        sql = "INSERT INTO product_info (name, description, normal_price, bonus_price, photo) VALUE ('{}', '{}', {}, {}, '../{}');".format(name, desc, price, bonus_price, img)
        print(sql)
        cur.execute(sql)
        db.commit()
        print("TRY")
        return True
    except mysql.connector.Error as err:
        flash(err, "remove")
        print(err)
        print("FAIL")
        return False
    finally:
        cur.close()
        db.close()
        app.config["PRODUCTS"] = Database_product_info(get_db())

if __name__ == '__main__':
    app.run()
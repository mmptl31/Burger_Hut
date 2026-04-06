import os 
from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import random
from datetime import timedelta
from flask_mail import Mail, Message
from flask_migrate import Migrate

app = Flask(__name__)

# ------------------ MAIL CONFIG ------------------ #
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'manuptl3031@gmail.com'
app.config['MAIL_PASSWORD'] = 'ssen qjbk jjlq uiwm'

mail = Mail(app)

# ------------------ DATABASE CONNECTION ------------------ #
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:root123@localhost/burger_hut'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

app.secret_key = "burgerhut_secret"

# ------------------ IMAGE UPLOAD ------------------ #
UPLOAD_FOLDER = 'static/images/menu'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS

# ------------------ MODELS ------------------ #

class Menu(db.Model):
    __tablename__ = "menu"

    menu_id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    price = db.Column(db.Integer, nullable=False)
    image = db.Column(db.String(255))
    availability = db.Column(db.Boolean, default=True)


class User(db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    dob = db.Column(db.Date)
    gender = db.Column(db.String(20))
    street_address = db.Column(db.String(255))
    area = db.Column(db.String(100))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    code = db.Column(db.String(10))
    phone_number = db.Column(db.String(10), unique=True)
    otp = db.Column(db.String(6))
    otp_expiry = db.Column(db.DateTime)


class DeliveryBoy(db.Model):
    __tablename__ = "delivery_boy"

    delivery_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    __tablename__ = "orders"

    order_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"))
    total_amount = db.Column(db.Integer)
    status = db.Column(db.String(50), default="Pending")
    delivery_id = db.Column(db.Integer, db.ForeignKey("delivery_boy.delivery_id"))
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    accepted_at = db.Column(db.DateTime)




class Cart(db.Model):
    __tablename__ = "cart"

    cart_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"))
    menu_id = db.Column(db.Integer, db.ForeignKey("menu.menu_id"))
    quantity = db.Column(db.Integer, default=1)

class OrderItem(db.Model):
    __tablename__ = "order_items"

    order_item_id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.order_id"))
    menu_id = db.Column(db.Integer)
    quantity = db.Column(db.Integer)
    price = db.Column(db.Integer)


class Feedback(db.Model):
    __tablename__ = "feedback"

    feedback_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"))
    message = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ------------------ ROUTES ------------------ #

@app.route('/')
def home():
    latest_feedback = Feedback.query.order_by(Feedback.feedback_id.desc()).limit(2).all()
    return render_template("home.html",latest_feedback=latest_feedback)

@app.route("/all_feedback")
def all_feedback():
    feedbacks = db.session.query(Feedback, User).join(User).all()
    return render_template("all_feedback.html", feedbacks=feedbacks)

@app.route('/give_feedback', methods=['GET', 'POST'])
def give_feedback():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        message = request.form.get('message')

        if message:
            new_feedback = Feedback(
                user_id=session['user_id'],
                message=message
            )
            db.session.add(new_feedback)
            db.session.commit()
            flash("Feedback submitted successfully!", "success")
            return redirect(url_for('give_feedback'))

    return render_template('give_feedback.html')

@app.route('/menu')
def menu():
    items = Menu.query.filter_by(availability=True).all()
    return render_template("menu.html", items=items)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        # Check user from database
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session["user_id"] = user.user_id

            # If user was adding item before login
            if "next_item" in session:
                menu_id = session.pop("next_item")

                cart_item = Cart(user_id=user.user_id, menu_id=menu_id)
                db.session.add(cart_item)
                db.session.commit()

                return redirect(url_for("cart"))

            return redirect(url_for("profile"))
        else:
            return "Invalid Email or Password"

    return render_template("login.html")

@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"]
        user = User.query.filter_by(email=email).first()

        if not user:
            return "Email not found!"

        otp = str(random.randint(100000, 999999))
        user.otp = otp
        user.otp_expiry = datetime.utcnow() + timedelta(minutes=5)
        db.session.commit()

        msg = Message("Your OTP Code",
                      sender=app.config['MAIL_USERNAME'],
                      recipients=[email])
        msg.body = f"Your OTP is {otp}. Valid for 5 minutes."

        mail.send(msg)

        return redirect(url_for("verify_otp", email=email))

    return render_template("forgot_password.html")

@app.route("/verify_otp/<email>", methods=["GET", "POST"])
def verify_otp(email):
    user = User.query.filter_by(email=email).first()

    if request.method == "POST":
        entered_otp = request.form["otp"]

        if user.otp == entered_otp and user.otp_expiry > datetime.utcnow():
            return redirect(url_for("reset_password", email=email))
        else:
            return "Invalid or Expired OTP"

    return render_template("verify_otp.html")

@app.route("/reset_password/<email>", methods=["GET", "POST"])
def reset_password(email):
    user = User.query.filter_by(email=email).first()

    if request.method == "POST":
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        if new_password != confirm_password:
            return "Passwords do not match!"

        user.password = generate_password_hash(new_password)
        user.otp = None
        user.otp_expiry = None
        db.session.commit()

        return redirect("/login")

    return render_template("reset_password.html")


@app.route('/signup', methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]   # ✅ Added
        dob = request.form["dob"]
        gender = request.form["gender"]
        street_address = request.form["street_address"]
        area = request.form["area"]
        city = request.form["city"]
        state = request.form["state"]
        code = request.form["code"]
        phone_number = request.form["phone_number"]

        # ✅ Password Match Check Added
        if password != confirm_password:
            return "Passwords do not match!"

        # Check if email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return "Email already registered!"

        hashed_password = generate_password_hash(password)

        new_user = User(
            name=name,
            email=email,
            password=hashed_password,
            dob=datetime.strptime(dob, "%Y-%m-%d"),
            gender=gender,
            street_address=street_address,
            area=area,
            city=city,
            state=state,
            code=code,
            phone_number=phone_number
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect("/login")

    return render_template("signup.html")


@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect("/login")

    user = User.query.get(session["user_id"])

    return render_template("profile.html", user=user)

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():

    # 🔒 Login check
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])

    if request.method == 'POST':

        # 📌 Get form data
        name = request.form.get('name')
        email = request.form.get('email')

        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        # 📝 Update basic details
        user.name = name
        user.email = email

        # 🔐 Password change logic
        if new_password and current_password:

            # Check current password
            if not check_password_hash(user.password, current_password):
                return "Current password incorrect!"

            # Confirm new password match
            if new_password != confirm_password:
                return "New passwords do not match!"

            # Save new hashed password
            user.password = generate_password_hash(new_password)

        db.session.commit()

        return redirect(url_for('profile'))

    return render_template('edit_profile.html', user=user)

@app.route('/delete_account', methods=['GET', 'POST'])
def delete_account():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])

    if request.method == 'POST':

        password = request.form.get('password')

        if not check_password_hash(user.password, password):
            return "Incorrect password!"

        db.session.delete(user)
        db.session.commit()

        session.clear()
        return redirect(url_for('home'))

    return render_template('delete_account.html')



@app.route("/logout_user")
def logout_user():
    session.pop("user_id", None)
    session.pop("user_name", None)
    return redirect("/")

@app.route("/add_to_cart/<int:menu_id>", methods=["POST"])
def add_to_cart(menu_id):

    if "user_id" not in session:
        # Store item id in session temporarily
        session["next_item"] = menu_id
        return redirect(url_for("login"))

    # Add item to cart
    cart_item = Cart(user_id=session["user_id"], menu_id=menu_id)
    db.session.add(cart_item)
    db.session.commit()

    return redirect(url_for("cart"))

@app.route("/cart")
def cart():
    if "user_id" not in session:
        return redirect("/login")

    cart_items = Cart.query.filter_by(user_id=session["user_id"]).all()

    total = 0
    detailed_items = []

    for item in cart_items:
        menu_item = Menu.query.get(item.menu_id)
        subtotal = menu_item.price * item.quantity
        total += subtotal

        detailed_items.append({
            "id": item.cart_id,
            "name": menu_item.item_name,
            "price": menu_item.price,
            "quantity": item.quantity,
            "subtotal": subtotal
        })

    return render_template("cart.html",
                           items=detailed_items,
                           total=total)

@app.route("/place_order", methods=["POST"])
def place_order():
    if "user_id" not in session:
        return redirect("/login")

    cart_items = Cart.query.filter_by(user_id=session["user_id"]).all()

    total = 0
    for item in cart_items:
        menu_item = Menu.query.get(item.menu_id)
        total += menu_item.price * item.quantity

    new_order = Order(
        user_id=session["user_id"],
        total_amount=total,
        status="Pending"
    )

    db.session.add(new_order)
    db.session.commit()

    # Save order items
    for item in cart_items:
        menu_item = Menu.query.get(item.menu_id)

        order_item = OrderItem(
            order_id=new_order.order_id,
            menu_id=item.menu_id,
            quantity=item.quantity,
            price=menu_item.price
        )
        db.session.add(order_item)

    Cart.query.filter_by(user_id=session["user_id"]).delete()
    db.session.commit()

    return redirect("/my_orders")



@app.route("/update_quantity/<int:cart_id>", methods=["POST"])
def update_quantity(cart_id):
    cart_item = Cart.query.get(cart_id)
    cart_item.quantity = int(request.form["quantity"])
    db.session.commit()
    return redirect(url_for("cart"))


@app.route("/remove_from_cart/<int:cart_id>", methods=["POST"])
def remove_from_cart(cart_id):
    cart_item = Cart.query.get(cart_id)
    db.session.delete(cart_item)
    db.session.commit()
    return redirect(url_for("cart"))

@app.route("/my_orders")
def my_orders():
    if "user_id" not in session:
        return redirect("/login")

    orders = Order.query.filter_by(user_id=session["user_id"]).all()

    return render_template("my_orders.html", orders=orders)

@app.route("/cancel_order/<int:order_id>", methods=["POST"])
def cancel_order(order_id):

    if "user_id" not in session:
        return redirect("/login")

    order = Order.query.get(order_id)

    if order.user_id != session["user_id"]:
        return "Unauthorized"

    if order.status == "Pending":
        order.status = "Cancelled"
        db.session.commit()

    return redirect("/my_orders")


@app.route("/order_details/<int:order_id>")
def order_details(order_id):

    if "user_id" not in session:
        return redirect("/login")

    order = Order.query.get(order_id)

    if order.user_id != session["user_id"]:
        return "Unauthorized Access"

    items = OrderItem.query.filter_by(order_id=order_id).all()

    detailed_items = []

    for item in items:
        menu_item = Menu.query.get(item.menu_id)
        detailed_items.append({
            "name": menu_item.item_name,
            "quantity": item.quantity,
            "price": item.price
        })

    return render_template("order_details.html",
                           order=order,
                           items=detailed_items)

# ------------------ ADMIN LOGIN ------------------ #

@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "1234":
            session["admin"] = True
            return redirect("/admin_dashboard")
        else:
            return "Invalid Credentials"

    return render_template("admin_login.html")

@app.route("/admin/view_orders")
def view_orders():
    if "admin" not in session:
        return redirect("/admin")

    orders = Order.query.all()
    return render_template("admin_view_orders.html", orders=orders)


@app.route("/admin_dashboard")
def admin_dashboard():
    if "admin" not in session:
        return redirect("/admin")

    total_menu = Menu.query.count()
    total_orders = Order.query.count()
    total_users = User.query.count()

    return render_template(
        "admin_dashboard.html",
        total_menu=total_menu,
        total_orders=total_orders,
        total_users=total_users
    )

@app.route("/admin/view_feedback")
def view_feedback():
    feedbacks = db.session.query(Feedback, User).join(User, Feedback.user_id == User.user_id).all()
    return render_template("admin_view_feedback.html", feedbacks=feedbacks)

@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/")

@app.route("/admin/add_menu", methods=["GET", "POST"])
def admin_add_menu():
    if "admin" not in session:
        return redirect("/admin")

    if request.method == "POST":
        item_name = request.form["item_name"]
        description = request.form["description"]
        price = request.form["price"]

        file = request.files["image"]
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            image_path = f"images/menu/{filename}"  # relative path

        new_item = Menu(
            item_name=item_name,
            description=description,
            price=price,
            image=image_path,
            availability=True
        )

        db.session.add(new_item)
        db.session.commit()

        return redirect("/admin_dashboard")  # back to dashboard after add

    # Render Add Menu form **inside dashboard content area**
    return render_template("admin_add_menu.html")

@app.route("/admin/view_menu")
def view_menu():
    if "admin" not in session:
        return redirect("/admin")

    items = Menu.query.all()
    return render_template("admin_view_menu.html", items=items)

@app.route("/admin/delete_menu/<int:menu_id>")
def delete_menu(menu_id):
    if "admin" not in session:
        return redirect("/admin")

    item = Menu.query.get(menu_id)

    if item:
        db.session.delete(item)
        db.session.commit()

    return redirect("/admin/view_menu")


@app.route("/admin/edit_menu/<int:menu_id>", methods=["GET", "POST"])
def edit_menu(menu_id):
    if "admin" not in session:
        return redirect("/admin")

    item = Menu.query.get(menu_id)

    if request.method == "POST":
        item.item_name = request.form["item_name"]
        item.description = request.form["description"]
        item.price = request.form["price"]

        file = request.files["image"]

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            item.image = f"images/menu/{filename}"

        db.session.commit()
        return redirect("/admin/view_menu")

    return render_template("admin_edit_menu.html", item=item)

@app.route("/admin/view_users")
def view_users():
    if "admin" not in session:
        return redirect("/admin")

    users = User.query.all()
    return render_template("admin_view_users.html", users=users)

@app.route("/admin/view_delivery")
def view_delivery():

    if "admin" not in session:
        return redirect("/admin")

    boys = DeliveryBoy.query.all()
    return render_template("admin_view_delivery.html", boys=boys)

@app.route("/admin/add_delivery", methods=["GET", "POST"])
def add_delivery():

    if "admin" not in session:
        return redirect("/admin")

    if request.method == "POST":
        name = request.form["name"]
        phone = request.form["phone"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        # Check duplicate email
        existing = DeliveryBoy.query.filter_by(email=email).first()
        if existing:
            return "Email already exists!"

        new_delivery = DeliveryBoy(
            name=name,
            phone=phone,
            email=email,
            password=password
        )

        db.session.add(new_delivery)
        db.session.commit()

        return redirect("/admin/view_delivery")

    return render_template("admin_add_delivery.html")

@app.route("/admin/edit_delivery/<int:id>", methods=["GET", "POST"])
def edit_delivery(id):

    if "admin" not in session:
        return redirect("/admin")

    boy = DeliveryBoy.query.get(id)

    if request.method == "POST":
        boy.name = request.form["name"]
        boy.phone = request.form["phone"]
        boy.email = request.form["email"]

        new_password = request.form.get("password")

        # If admin enters new password
        if new_password:
            boy.password = generate_password_hash(new_password)

        db.session.commit()
        return redirect("/admin/view_delivery")

    return render_template("admin_edit_delivery.html", boy=boy)

@app.route("/admin/delete_delivery/<int:id>")
def delete_delivery(id):

    if "admin" not in session:
        return redirect("/admin")

    boy = DeliveryBoy.query.get(id)

    if boy:
        boy.is_active = False
        db.session.commit()

    return redirect("/admin/view_delivery")
@app.route("/admin/assign_delivery/<int:order_id>", methods=["POST"])
def assign_delivery(order_id):

    if "admin" not in session:
        return redirect("/admin")

    order = Order.query.get(order_id)
    delivery_id = request.form["delivery_id"]

    order.delivery_id = delivery_id
    order.status = "Out for Delivery"

    db.session.commit()

    return redirect("/admin/view_orders")

@app.route("/admin/restore_delivery/<int:id>")
def restore_delivery(id):

    if "admin" not in session:
        return redirect("/admin")

    boy = DeliveryBoy.query.get(id)

    if boy:
        boy.is_active = True
        db.session.commit()

    return redirect("/admin/view_delivery")


# ------------------ Delivery Boy  ------------------ #

@app.route("/delivery_dashboard")
def delivery_dashboard():

    if "delivery_id" not in session:
        return redirect("/delivery_login")

    delivery_id = session["delivery_id"]

    orders = Order.query.filter(
        (Order.status == "Pending") |
        (Order.delivery_id == delivery_id)
    ).all()

    # Monthly income calculation (10% commission)
    current_month = datetime.now().month
    current_year = datetime.now().year

    delivered_orders = Order.query.filter_by(
        delivery_id=delivery_id,
        status="Delivered"
    ).all()

    monthly_income = 0

    for order in delivered_orders:
        if order.order_date.month == current_month and order.order_date.year == current_year:
            monthly_income += order.total_amount * 0.10   # 🔥 10% commission

    return render_template(
        "delivery_dashboard.html",
        orders=orders,
        monthly_income=monthly_income
    )

@app.route("/mark_delivered/<int:order_id>", methods=["POST"])
def mark_delivered(order_id):

    if "delivery_id" not in session:
        return redirect("/delivery_login")

    order = Order.query.get_or_404(order_id)

    # Only allow if accepted by this delivery boy
    if order.status == "Accepted" and order.delivery_id == session["delivery_id"]:
        order.status = "Delivered"
        db.session.commit()

    return redirect("/delivery_dashboard")


@app.route("/delivery_login", methods=["GET", "POST"])
def delivery_login():

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        boy = DeliveryBoy.query.filter_by(email=email, is_active=True).first()

        if boy and check_password_hash(boy.password, password):
            session["delivery_id"] = boy.delivery_id
            session["delivery_name"] = boy.name
            return redirect("/delivery_dashboard")
        else:
            return "Invalid Credentials"

    return render_template("delivery_login.html")

@app.route("/logout_delivery")
def logout_delivery():
    session.pop("delivery_id", None)
    session.pop("delivery_name", None)
    return redirect("/")

@app.route("/accept_order/<int:order_id>", methods=["POST"])
def accept_order(order_id):

    if "delivery_id" not in session:
        return redirect("/delivery_login")

    order = Order.query.get(order_id)

    if order.status == "Pending":
        order.delivery_id = session["delivery_id"]
        order.status = "Accepted"
        db.session.commit()

    return redirect("/delivery_dashboard")


# ------------------ AUTO CREATE TABLES ------------------ #

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)

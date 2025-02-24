from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
import json
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, logout_user, UserMixin, login_required, current_user
from datetime import datetime , timedelta
from functools import wraps  # Import wraps to fix the decorator issue

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SECRET_KEY"] = "welcome"
app.permanent_session_lifetime = timedelta(minutes=10)
# session.permanent = True
def saveReview(load_review):
    with open('reviews.json', 'w') as file:
        json.dump(load_review, file)
def loadReview():
    try:
        with open('reviews.json', 'r') as file:
            data=json.load(file)
            return data
    except:
        return []
review=loadReview()



@app.route("/reviews", methods=[ "GET","POST"])
def reviews():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        review_text = request.form.get("review")
        reviews = loadReview()
        reviews.append({"user_name": name, "user_email": email, "user_review": review_text})
        print(reviews)
        saveReview(reviews)
        flash("Your response has been recorded successfully")
        return redirect(url_for("about"))
    else:
        return "Invalid request"



db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(db.Model, UserMixin):
    _tablename_ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password_hash = db.Column(db.String(200))
    role = db.Column(db.String(100), default="user")

    def save_hash_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_hash_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def role_required(role):
    """Decorator to restrict access to specific roles"""
    def decorator(func):
        @wraps(func)  # Ensure Flask registers the function correctly
        def wrap(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role != role:
                flash("Unauthorized Access")
                return redirect(url_for("login"))
            return func(*args, **kwargs)
        return wrap
    return decorator

@app.route("/register", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        if User.query.filter_by(email=email).first():
            flash("User Already Exists")
            return redirect(url_for("home"))

        user_data = User(username=username, email=email)
        user_data.save_hash_password(password)

        db.session.add(user_data)
        db.session.commit()
        flash("User Registered Successfully")
        return redirect(url_for("login"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user_data = User.query.filter_by(email=email).first()
        if user_data and user_data.check_hash_password(password):
            login_user(user_data)
            # session.permanent= True
            flash("User logged in successfully")

            if user_data.role == "admin":  
                return redirect(url_for("admin_panel"))  # Redirect admin to admin page
            return redirect(url_for("home"))  # Redirect normal users to home
    return render_template("login.html")


# @app.route("/login", methods=["GET", "POST"])
# def login():
#     if request.method == "POST":
#         email = request.form.get("email")
#         password = request.form.get("password")

#         user_data = User.query.filter_by(email=email).first()
#         if user_data and user_data.check_hash_password(password):
#             login_user(user_data)
#             flash("User logged in successfully","succes")

#             # next_page = request.args.get("next")  # Get next page (if any)
#             # return redirect(next_page) if next_page else redirect(url_for("home"))
#         else:
#             if user_data.role == "admin":  
#                 return redirect(url_for("admin_panel"))  # Redirect admin to admin page
#             return redirect(url_for("home"))  # Redirect normal users to home
        
#     flash("Invalid email or password!", "danger")
#     return render_template("login.html")

@app.route("/profile")
@login_required
def profile():
    booking_data = Booking.query.filter_by(user_email=current_user.email).all()
    return render_template("profile.html", booking_data=booking_data)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("User Logged Out Successfully")
    return redirect(url_for("home"))

class Booking(db.Model):
    _tablename_ = "booking"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    user_email = db.Column(db.String(200))
    user_checkin= db.Column(db.Date)
    user_checkout = db.Column(db.Date)
    user_adult = db.Column(db.Integer)
    user_child = db.Column(db.Integer)
    user_room = db.Column(db.Integer)
    user_request = db.Column(db.String(100))

@app.route("/booking", methods=["GET", "POST"])
@login_required
def booking():
    if request.method == "POST":
        name = request.form.get("name")
        user_email = current_user.email  # Get logged-in user's email automatically
        user_checkin_str = request.form.get("user_checkin")
        user_checkout_str = request.form.get("user_checkout")
        user_adult = request.form.get("user_adult")
        user_child = request.form.get("user_child")
        user_room = request.form.get("user_room")
        user_request = request.form.get("user_request")
        user_checkin = datetime.strptime(user_checkin_str, "%Y-%m-%d").date()
        user_checkout = datetime.strptime(user_checkout_str, "%Y-%m-%d").date()

        booking_data = Booking(
            name=name,
            user_email=user_email,
            user_checkin=user_checkin,
            user_checkout=user_checkout,
            user_adult=int(user_adult),
            user_child=int(user_child),
            user_room=int(user_room),
            user_request=user_request
        )
        db.session.add(booking_data)
        db.session.commit()
        flash("Your room is booked successfully")
        return redirect(url_for("dashboard"))
    return render_template("booking.html")





@app.route("/delete/<int:id>")
@login_required
def deleteFunction(id):
    user=db.session.get(Booking,id)
    if user:
        db.session.delete(user)
        db.session.commit()
        flash("Booking deleted successfully")
        return redirect(url_for("home"))
    else:
        flash ("No booking found with the given id")
        return redirect(url_for("home"))

@app.route("/update/<int:booking_id>", methods=["GET", "POST"])
@login_required
def update_booking(booking_id):
    booking = db.session.get(Booking, booking_id)
    if request.method == "POST":
        booking.name = request.form.get("name")
        booking.user_email = request.form.get("user_email")
        booking_checkin_str = request.form.get("user_checkin")
        booking_checkout_str = request.form.get("user_checkout")
        booking.user_adult = int(request.form.get("user_adult"))
        booking.user_child = int(request.form.get("user_child"))
        booking.user_room = int(request.form.get("user_room"))
        booking.user_request = request.form.get("user_request")

        # Convert dates to datetime objects
        booking.user_checkin = datetime.strptime(booking_checkin_str, "%Y-%m-%d").date()
        booking.user_checkout = datetime.strptime(booking_checkout_str, "%Y-%m-%d").date()

        db.session.commit()
        flash("Booking updated successfully!")
        return redirect(url_for("dashboard"))

    return render_template("updateForm.html", data=booking)




@app.route("/dashboard")
@login_required
def dashboard():
    booking_data = Booking.query.filter_by(user_email=current_user.email).all()   
    return render_template("dashboard.html", booking_data=booking_data)

@app.route("/admin")
@login_required
@role_required("admin")
def admin_panel():
    booking_data = Booking.query.all()
    return render_template("admin.html", booking_data=booking_data)

class Contact(db.Model):
    _tablename_ = "contact"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(200))
    subject = db.Column(db.String(200))
    message = db.Column(db.String(100))

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        subject = request.form.get("subject")
        message = request.form.get("message")
        contact_data = Contact(name=name, email=email, subject=subject, message=message)
        db.session.add(contact_data)
        db.session.commit()
        flash("Thank you for your message! We will get back to you soon.")
        return redirect(url_for("home"))
    return render_template("contact.html")

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/goa")
@login_required
def goa():
    return render_template("goa.html")

@app.route("/delhi")
@login_required
def delhi():
    return render_template("delhi.html")

@app.route("/agra")
@login_required
def agra():
    return render_template("agra.html")

@app.route("/room")
@login_required
def room():
    return render_template("rooms.html")

@app.route("/hyderabad")
@login_required
def hyderabad():
    return render_template("hyderabad.html")

@app.route("/mumbai")
@login_required
def mumbai():
    return render_template("mumbai.html")

@app.route("/bengaluru")
@login_required
def bengaluru():
    return render_template("bengaluru.html")

with app.app_context():
    db.create_all()
    if not User.query.filter_by(email="admin@gmail.com").first():
        admin = User(username="admin", email="admin@gmail.com", role="admin")
        admin.save_hash_password('admin')
        db.session.add(admin)
        db.session.commit()

if __name__ == "__main__":
    app.run(debug=True)
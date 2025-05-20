import pyotp, qrcode, io, re
from flask import Flask, request, redirect, render_template, session, send_file
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import InputRequired, Length
from passlib.hash import bcrypt
from db import init_db, add_user, get_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
app.secret_key = "your-very-secret-key"
init_db()

limiter = Limiter(get_remote_address, app=app)

class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[InputRequired()])
    password = PasswordField("Password", validators=[InputRequired(), Length(min=8)])

class LoginForm(FlaskForm):
    username = StringField("Username", validators=[InputRequired()])
    password = PasswordField("Password", validators=[InputRequired()])

def is_secure_password(pw):
    return (
        len(pw) >= 8 and re.search(r"[A-Z]", pw) and re.search(r"[a-z]", pw) and re.search(r"[!@#$%^&*()]", pw)
    )

@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        username, password = form.username.data, form.password.data
        if get_user(username):
            return "Benutzer existiert bereits."
        if not is_secure_password(password):
            return "Passwort zu schwach."
        otp_secret = pyotp.random_base32()
        add_user(username, bcrypt.hash(password), otp_secret)
        session["otp_secret"] = otp_secret
        session["username"] = username
        return redirect("/qrcode")
    return render_template("register.html", form=form)

@app.route("/qrcode")
def qrcode_route():
    otp_secret = session.get("otp_secret")
    username = session.get("username")
    if not otp_secret:
        return redirect("/register")
    uri = pyotp.TOTP(otp_secret).provisioning_uri(name=username, issuer_name="SecureApp")
    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf)
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

@limiter.limit("5 per minute")
@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username, password = form.username.data, form.password.data
        user = get_user(username)
        if user and bcrypt.verify(password, user[1]):
            session["username"] = username
            return redirect("/2fa")
        return "Login fehlgeschlagen."
    return render_template("login.html", form=form)

@app.route("/2fa", methods=["GET", "POST"])
def two_factor():
    if request.method == "POST":
        code = request.form.get("code")
        user = get_user(session.get("username"))
        if pyotp.TOTP(user[2]).verify(code):
            return "Erfolgreich eingeloggt"
        return "Ungültiger Code"
    return render_template("2fa.html")

if __name__ == "__main__":
    app.run(debug=True)

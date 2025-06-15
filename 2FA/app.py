import pyotp, qrcode, io, re
from flask import Flask, request, redirect, render_template, session, send_file
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import InputRequired, Length
from passlib.hash import argon2
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
        len(pw) >= 8 and re.search(r"[A-Z]", pw) and re.search(r"[1-9]", pw) and re.search(r"[a-z]", pw) and re.search(r"[!@#$%^&*()]", pw)
    )

@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    error = None

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        if get_user(username):
            error = "Benutzername ist bereits vergeben."
        elif not is_secure_password(password):
            error = "Passwortanforderungen nicht erfüllt: Groß-/Kleinbuchstaben, Zahl, Sonderzeichen."

        if error:
            return render_template("register.html", form=form, error=error)

        otp_secret = pyotp.random_base32()
        password_hash = argon2.hash(password)
        add_user(username, password_hash, otp_secret)
        session["otp_secret"] = otp_secret
        session["username"] = username
        return render_template("qrcode.html")

    return render_template("register.html", form=form)



@app.route("/qrcode")
def qrcode_route():
    otp_secret = session.get("otp_secret")
    username = session.get("username")
    if not otp_secret or not username:
        return redirect("/login")
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
    error = None

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = get_user(username)
        if user and argon2.verify(password, user[1]):
            session["username"] = username
            return redirect("/2fa")
        else:
            error = "Login fehlgeschlagen: Benutzername oder Passwort ist falsch."

    return render_template("login.html", form=form, error=error)


@app.route("/2fa", methods=["GET", "POST"])
def two_factor():
    if request.method == "POST":
        code = request.form.get("code")
        user = get_user(session.get("username"))
        if pyotp.TOTP(user[2]).verify(code):
            return render_template("success.html")  # statt Rückgabe als Text
        return "Ungültiger Code"
    return render_template("2fa.html")


@app.route("/")
def index():
    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Home Page
@app.route("/")
def index():
    return render_template("index.html")

# Login Page
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        # TODO: Add authentication logic here & Validation
        if email == "test@example.com" and password == "1234":
            return redirect(url_for("index"))
        else:
            return render_template("login.html", error="Invalid email or password")
    return render_template("login.html")

# Register Page
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # handle registration
        pass
    return render_template("register.html")

if __name__ == "__main__":
    app.run(debug=True)

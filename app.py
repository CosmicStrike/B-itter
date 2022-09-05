import os.path
import re
import uuid
from datetime import date
import flask
import random
import Database as db
import send_mail

app = flask.Flask(__name__)

keys = {}

db.initialize("root", "root")

regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'


# TODO: Logout data: send_form("/logout",{"subject":"logout","key":ge tkeyfromstorage,"uname":"getunamefromstorage"})

@app.route("/", methods=["POST", "GET"])
def root():
    if flask.request.method == "GET":
        return flask.render_template("index.html")
    if flask.request.method == "POST":
        try:
            sub = flask.request.form["subject"]
            if sub == "gotoreg2":
                return flask.render_template("reg2.html")
        except KeyError as e:
            pass

        data = flask.request.get_json()

        if data["subject"] == "login":
            return login(data)

        if data["subject"] == "register":
            return register(data)

        if data["subject"] == "reg2_data":
            return update(data)

        if data["subject"] == "forgotpass":
            return forgotpass(data)

        if data["subject"] == "getpost":
            return get_post(data)

        if data["subject"] == "sendpost":
            return send_post(data)

        if data["subject"] == "updatelc":
            return updatelc(data)

        if data["subject"] == "logout":
            return logout(data)


@app.route("/register")
def render_reg():
    return flask.render_template("register.html")


@app.route("/forgotpass")
def render_forgot_pass():
    return flask.render_template("forgotpass.html")


@app.route("/logout", methods=["POST"])
def render_logout():
    data = flask.request.form
    print(data)
    if data["subject"] == "keyerror":
        return flask.render_template("index.html", error="You have been logged out due to other device logging in")
    elif data["subject"] == "logout":
        return flask.render_template("index.html")
    else:
        return {"subject": "error"}


def login(data):
    username = ''
    try:
        username = data["uname"]
        passwd = data["passwd"]

        res = db.check(username, passwd)
        if res:
            key = random.randint(10000000, 99999999)
            keys[username] = key

            resp = {"status": "success", "uname": username, "key": key}
            return resp
        else:
            return {"status": "badpasswd"}

    except KeyError:
        key = data["key"]
        try:
            if str(keys[username]) == key:
                key = random.randint(10000000, 99999999)
                keys[username] = key
                return {"status": "success", "key": key, "uname": username}
            else:
                return {"status": "none"}
        except KeyError:
            return {"status": "none"}


def logout(data):
    uname = data["uname"]
    key = data["key"]
    if str(keys[uname]) == key:
        del keys[uname]
        return {"status": "success"}
    else:
        return {"status": "error"}


def get_post(data):
    try:
        uname = data["uname"]
        key = data["key"]
        if key == str(keys[uname]):
            res = db.retrieve_posts()
            return {"status": "success", "data": res}
        else:
            return {"status": "logout"}
    except KeyError as e:
        return {"status": "keyerror"}


@app.route("/images/<path:path>")
def get_image(path):
    if not os.path.exists(f"static/images/{path}"):
        path = "default.png"
    return flask.send_from_directory("static/images", path)


def register(data):
    username = data["uname"]
    password = data["passwd1"]
    email = data["email"]

    if not re.search(regex, email):
        return {"status": "Invalid Email"}

    if (len(username) < 5 or " " in username) or (len(password) < 5 or " " in password):
        return {"status": "username and password should be between 5 to 20 characters without spaces"}

    res1 = db.retrieve_users()
    res = res1.keys()

    if username in res:
        return {"status": "alreadyuser"}
    uid = uuid.uuid4().hex
    if db.insert_user(uid=uid, uname=username, passwd=password, email=email):
        data = login({"uname": username, "passwd": password})
        key = data["key"]
        return {"status": "success", "uname": username, "key": key}
    else:
        return {"status": "alreadyemail"}


def send_email(email, password):
    try:
        send_mail.send_mail(email, password)
    except Exception as e:
        print(e)
    pass


def updatelc(data):
    uname = data["uname"]
    key = data["key"]
    pid = data["pid"]

    res = db.update_post(pid=pid, l_count=True)
    return {"status": "success" if res else "failure"}


def send_post(data):
    key = data["key"]
    uname = data["uname"]
    if key == str(keys[uname]):
        users = db.retrieve_users()
        uid = users[uname]
        res = db.insert_posts(U_id=uid, cont=data["content"])
        return {"status": "success"} if res else {"status": "failure"}
    else:
        return {"status": "keyerror"}


def forgotpass(data):
    email = data["email"]
    p = db.getemail(email)
    if p:
        send_email(email, p)
        return {"status": "success"}
    else:
        return {"status": "noemail"}


def update(data):
    try:
        uname = data["uname"]
        if data["key"] == str(keys[uname]):
            fname = data["fname"]
            lname = data["lname"]
            gender = data["gender"]
            mob = data["mob"]
            dob = data["dob"]

            if not dob:
                dob = "0000-00-00"
                age = 0
            else:
                age = get_y(dob)

            if not mob:
                mob = 0

            res = db.retrieve_users()

            if db.update(fname=fname, lname=lname, age=age, gender=gender, mob=mob, dob=dob, uid=res[uname]):
                return {"status": "success"}
            else:
                return {"status": "failure"}
        else:
            return {"status": "badkey"}
    except KeyError as e:
        return {"status": "keyerror"}


def get_y(dob: str) -> int:
    _y, _m, _d = dob[:4], dob[5:7], dob[8:]
    cur = str(date.today())
    c_y, c_m, c_d = cur[:4], cur[5:7], cur[8:]
    dif_y, dif_m, dif_d = int(c_y) - int(_y), int(c_m) - int(_m), int(c_d) - int(_d)
    if dif_m < 0:
        dif_y -= 1
    elif dif_m == 0 and dif_d < 0:
        dif_y -= 1
    return dif_y


app.run(host="0.0.0.0", port=5005, debug=True, use_reloader=False)

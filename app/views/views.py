from functools import wraps
import flask
import jwt
from flask import Blueprint
from flask import current_app
from flask import request, jsonify, render_template, make_response
from jwt import ExpiredSignatureError, DecodeError
import app.Database as Data

view_bp = Blueprint("views", __name__)


def token_required(f):
    """
    token_required(f) decorator will validate a token f and return the User Class object defined in
    modules/Database. token should be sent through HTTP header 'x-access-tokens'
    """

    @wraps(f)
    def decorator(*args, **kwargs):

        token = request.cookies.get("token")

        if not token:
            return jsonify({'message': 'a valid token is missing'})

        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = Data.Users.query.filter_by(id=data['id']).first()

            if not current_user.confirmed:
                return {"status": "email"}
        except ExpiredSignatureError:
            return jsonify({'status': 'expired'})
        except DecodeError:
            return jsonify({"status": "invalid"})

        return f(*args, current_user, **kwargs)

    return decorator


@view_bp.route("/", methods=["GET"])
def main():
    """
    The root route of the app. will handle rendering of index.html and forgotpass.html
    """
    token = request.cookies.get("token")
    if not token:
        return render_template("index.html")
    elif token == "success":
        response = flask.make_response(render_template("index.html"))
        response.delete_cookie("token")
        return response
    elif token == "expired":
        response = flask.make_response(render_template("forgotpass.html"))
        response.delete_cookie("token")
        return response
    else:
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = Data.Users.query.filter_by(id=data['id']).first()
            if current_user.confirmed:
                return render_template("main.html")
            else:
                return render_template("confirmemail.html")
        except Exception:
            return render_template("index.html")


@view_bp.route("/register")
def register_render():
    """Renders register.html"""
    token = request.cookies.get("token")
    try:
        data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
        current_user = Data.Users.query.filter_by(id=data['id']).first()
        if current_user.confirmed:
            return flask.redirect("/")
        else:
            return render_template("confirmemail.html")
    except Exception:
        return render_template("register.html")


@view_bp.route("/profile/edit")
def edit_profile():
    """
    Render editprofile.html requires token in cookie
    """
    try:
        token = request.cookies.get("token")
        data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
        current_user = Data.Users.query.filter_by(id=data['id']).first()
        if current_user.confirmed:
            return render_template("editprofile.html")
        else:
            return render_template("index.html")
    except ExpiredSignatureError:
        return jsonify({'message': 'expired'})
    except DecodeError:
        return jsonify({"message": "invalid"})


@view_bp.route("/u/<uname>", methods=["GET"])
def profile(uname):
    """
    renders userprofile.html
    """
    user = Data.get_user(uname)
    if not user:
        return make_response(render_template("404.html", error=f"User {uname} not found"), 404)
    try:
        token = request.cookies.get("token")
        data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
        current_user = Data.Users.query.filter_by(id=data['id']).first()
        if current_user.confirmed:
            if current_user.username == uname:
                return render_template("userprofile.html", uid=user.id, visiting=False, login=True)
            else:
                return render_template("userprofile.html", uid=user.id, visiting=True, login=True)
        else:
            return render_template("confirmemail.html")
    except Exception as e:
        print(repr(e))

    return render_template("userprofile.html", uid=user.id, visiting=True, login=False)


@view_bp.route("/password/reset")
def reset_render():
    """Renders forgotpass.html"""
    return render_template("forgotpass.html")


@view_bp.route("/reset", methods=["GET"])
def reset():
    """
    renders the password reset page by checking the GET method args "id" and "uid" for guid and user id
    """
    guid = request.args.get("id")
    uid = request.args.get("uid")
    if Data.check_reset(guid, uid):
        user = Data.get_user(uid=uid)
        return render_template("resetpass.html", uname=user.username)
    return render_template("forgotpass.html")


@view_bp.route("/confirm", methods=["GET"])
def confirm_email():
    """
    renders the password reset page by checking the GET method args "id" and "uid" for guid and user id
    """
    guid = request.args.get("id")
    uid = request.args.get("uid")
    Data.confirm_email(guid, uid)
    return flask.redirect("/")


@view_bp.route("/search", methods=["GET"])
@token_required
def search(user):
    try:
        search_uname = request.args.get("user")
        users = Data.search(search_uname)
        return render_template("search.html", users=users, uname=user.username)
    except Exception as e:
        print(repr(e))
        return render_template("404.html")
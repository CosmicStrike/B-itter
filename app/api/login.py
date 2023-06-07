import datetime
import flask
import jwt
from flask import request, jsonify
import app.db as Data
from flask_restful import Resource
from flask import current_app

from app.api.token_required import token_required

active_tokens = {}



class Login(Resource):
    def get(self):
        try:
            token = request.cookies.get("token")
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = Data.Users.query.filter_by(id=data['id']).first()
            if current_user.confirmed:
                if token in active_tokens.values():
                    return {"status": "success"}
                else:
                    return {"status": "false"}
            else:
                return {"status": "email"}
        except Exception as e:
            print(repr(e))
            return {"status": "failure"}

    def post(self):
        auth = request.authorization
        if not auth or not auth.username or not auth.password:
            return jsonify({"status": "failure"})

        try:
            user = Data.check_login(auth.username, auth.password)
            if user:
                token = jwt.encode(
                    {'id': user.id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=8000)},
                    current_app.config['SECRET_KEY'], "HS256")
                active_tokens[user.username] = token
                response = flask.make_response(
                    {"status": "success", "uname": flask.escape(user.username), "uid": user.id})
                response.set_cookie("token", token, httponly=True, secure=True, samesite="Strict")
                return response
            else:
                return jsonify({"status": "username or password is incorrect"})

        except Exception:
            return jsonify({"status": "failure"})
        


class Logout(Resource):
    @token_required
    def post(self, user):
        try:
            active_tokens.pop(user.username)
        except KeyError:
            pass
        response = flask.make_response({"status": "success"})
        response.delete_cookie("token")
        return response
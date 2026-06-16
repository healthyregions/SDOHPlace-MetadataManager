import base64
import hashlib
import json
import os
import secrets
from urllib.parse import urlencode
import requests
from flask import Blueprint, redirect, url_for, request, render_template, flash, session
from flask_login import login_user, logout_user, current_user

from werkzeug.security import generate_password_hash, check_password_hash

from manager.models import db, User

auth = Blueprint("auth", __name__)


def is_keycloak_configured():
    return bool(os.getenv("KEYCLOAK_ISSUER") and os.getenv("KEYCLOAK_CLIENT_ID"))


def _keycloak_issuer():
    return os.getenv("KEYCLOAK_ISSUER", "").rstrip("/")


def _keycloak_client_id():
    return os.getenv("KEYCLOAK_CLIENT_ID", "")


def _keycloak_scope():
    return os.getenv("KEYCLOAK_SCOPE", "openid profile email roles")


def _keycloak_manager_role():
    return os.getenv("KEYCLOAK_MANAGER_ROLE", "metadata-manager")


def _keycloak_admin_role():
    return os.getenv("KEYCLOAK_ADMIN_ROLE", "metadata-manager-admin")


def _keycloak_timeout():
    return int(os.getenv("KEYCLOAK_TIMEOUT", "10"))


def _manager_public_url():
    return os.getenv("MANAGER_PUBLIC_URL", "").rstrip("/")


def _manager_url(endpoint):
    public_url = _manager_public_url()
    path = url_for(endpoint)
    if public_url:
        return f"{public_url}{path}"
    return url_for(endpoint, _external=True)


def _manager_home_url():
    public_url = _manager_public_url()
    if public_url:
        return f"{public_url}/"
    return url_for("manager.index", _external=True)


def _decode_jwt_payload(token):
    parts = token.split(".")
    if len(parts) < 2:
        return {}
    padded = parts[1] + "=" * (-len(parts[1]) % 4)
    try:
        return json.loads(base64.urlsafe_b64decode(padded.encode("utf-8")))
    except Exception:
        return {}


def _base64_url(value):
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("utf-8")


def _code_challenge(code_verifier):
    return _base64_url(hashlib.sha256(code_verifier.encode("utf-8")).digest())


def _extract_roles(payload):
    roles = set(payload.get("realm_access", {}).get("roles", []))
    resource_access = payload.get("resource_access", {})
    client_roles = resource_access.get(_keycloak_client_id(), {}).get("roles", [])
    roles.update(client_roles)
    return sorted(roles)


def _has_session_role(role):
    return bool(role and role in session.get("keycloak_roles", []))


def _clear_keycloak_session():
    id_token = session.pop("keycloak_id_token", None)
    had_keycloak_session = session.pop("keycloak_authenticated", False)
    session.pop("keycloak_roles", None)
    session.pop("keycloak_state", None)
    session.pop("keycloak_code_verifier", None)
    return id_token, had_keycloak_session


def is_admin_user():
    if not current_user.is_authenticated:
        return False
    if current_user.name == "admin":
        return True
    return _has_session_role(_keycloak_admin_role())


def _start_keycloak_login():
    state = secrets.token_urlsafe(24)
    code_verifier = secrets.token_urlsafe(64)
    session["keycloak_state"] = state
    session["keycloak_code_verifier"] = code_verifier
    params = {
        "client_id": _keycloak_client_id(),
        "redirect_uri": _manager_url("auth.keycloak_callback"),
        "response_type": "code",
        "scope": _keycloak_scope(),
        "state": state,
        "code_challenge": _code_challenge(code_verifier),
        "code_challenge_method": "S256",
    }
    return redirect(f"{_keycloak_issuer()}/protocol/openid-connect/auth?{urlencode(params)}")


def _exchange_code(code):
    body = {
        "grant_type": "authorization_code",
        "client_id": _keycloak_client_id(),
        "code": code,
        "redirect_uri": _manager_url("auth.keycloak_callback"),
    }
    code_verifier = session.pop("keycloak_code_verifier", None)
    if code_verifier:
        body["code_verifier"] = code_verifier
    client_secret = os.getenv("KEYCLOAK_CLIENT_SECRET", "")
    if client_secret:
        body["client_secret"] = client_secret
    response = requests.post(
        f"{_keycloak_issuer()}/protocol/openid-connect/token",
        data=body,
        timeout=_keycloak_timeout(),
    )
    if not response.ok:
        raise ValueError(response.text or "Token exchange failed")
    return response.json()


def _unique_name(base_name):
    candidate = base_name or "keycloak-user"
    existing = User.query.filter_by(name=candidate).first()
    if not existing:
        return candidate
    index = 2
    while User.query.filter_by(name=f"{candidate}-{index}").first():
        index += 1
    return f"{candidate}-{index}"


def _user_from_keycloak(payload):
    email = payload.get("email") or payload.get("preferred_username") or payload.get("sub")
    user = User.query.filter_by(email=email).first()
    if user:
        return user
    preferred_name = payload.get("preferred_username") or payload.get("name") or email
    user = User(
        name=_unique_name(preferred_name),
        email=email,
        password=generate_password_hash(secrets.token_urlsafe(32), method="pbkdf2:sha256"),
    )
    db.session.add(user)
    db.session.commit()
    return user


@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if is_keycloak_configured() and request.args.get("local") != "true":
            return _start_keycloak_login()
        return render_template("auth/login.html", user=current_user)

    if request.method == "POST":
        _clear_keycloak_session()
        email = request.form.get("email")
        password = request.form.get("password")
        remember = True if request.form.get("remember") else False

        user = User.query.filter_by(email=email).first()

        if user is None or not check_password_hash(user.password, password):
            flash("Please check your login details and try again.")
            return redirect(url_for("auth.login"))

        login_user(user, remember=remember)
        return redirect(url_for("manager.index"))


@auth.route("/auth/callback", methods=["GET"])
def keycloak_callback():
    if not is_keycloak_configured():
        flash("Keycloak is not configured.", "danger")
        return redirect(url_for("auth.login"))

    error = request.args.get("error")
    if error:
        flash(request.args.get("error_description") or error, "danger")
        return redirect(url_for("auth.login", local="true"))

    state = request.args.get("state")
    expected_state = session.pop("keycloak_state", None)
    if not state or state != expected_state:
        session.pop("keycloak_code_verifier", None)
        flash("Invalid login state.", "danger")
        return redirect(url_for("auth.login", local="true"))

    code = request.args.get("code")
    if not code:
        session.pop("keycloak_code_verifier", None)
        flash("Missing authorization code.", "danger")
        return redirect(url_for("auth.login", local="true"))

    try:
        token_response = _exchange_code(code)
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("auth.login", local="true"))

    access_token = token_response.get("access_token", "")
    payload = _decode_jwt_payload(access_token)
    roles = _extract_roles(payload)
    manager_role = _keycloak_manager_role()
    admin_role = _keycloak_admin_role()
    if manager_role and manager_role not in roles and admin_role not in roles:
        flash("Your account does not have Metadata Manager access.", "danger")
        return redirect(url_for("auth.login", local="true"))

    user = _user_from_keycloak(payload)
    session["keycloak_roles"] = roles
    session["keycloak_id_token"] = token_response.get("id_token")
    session["keycloak_authenticated"] = True
    login_user(user, remember=True)
    return redirect(url_for("manager.index"))


@auth.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("auth/signup.html", user=current_user)

    if request.method == "POST":
        # code to validate and add user to database goes here
        email = request.form.get("email")
        name = request.form.get("name")
        password = request.form.get("password")

        user = User.query.filter_by(
            email=email
        ).first()  # if this returns a user, then the email already exists in database

        if user:  # if a user is found, we want to redirect back to signup page so user can try again
            flash("Email address already exists")
            return redirect(url_for("auth.signup"))

        # create a new user with the form data. Hash the password so the plaintext version isn't saved.
        new_user = User(
            email=email,
            name=name,
            password=generate_password_hash(password, method="pbkdf2:sha256"),
        )

        # add the new user to the database
        db.session.add(new_user)
        db.session.commit()

        flash("User created, you can now sign in.")
        return redirect(url_for("auth.login"))


@auth.route("/logout")
def logout():
    id_token, had_keycloak_session = _clear_keycloak_session()
    logout_user()
    if is_keycloak_configured() and had_keycloak_session:
        params = {
            "client_id": _keycloak_client_id(),
            "post_logout_redirect_uri": _manager_home_url(),
        }
        if id_token:
            params["id_token_hint"] = id_token
        return redirect(f"{_keycloak_issuer()}/protocol/openid-connect/logout?{urlencode(params)}")
    return redirect(url_for("manager.index"))

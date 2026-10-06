"""Tests for POST /api/auth/register, /login, /logout, and GET /api/auth/me.

Defects these catch:
- registration that returns 201 without actually creating a working session
  (the returned cookie doesn't authenticate a later request);
- a missing or broken unique-phone constraint, letting a second workshop
  register with a phone number that already belongs to another owner;
- login that reveals whether a phone number is registered by returning a
  different status or body for "unknown phone" vs "wrong password" (user
  enumeration);
- a login endpoint that is wired up but doesn't actually authenticate (no
  working session afterwards);
- a session check (`/me`) that accepts a missing cookie, a tampered token,
  or an expired token as if it were a valid session;
- logout that doesn't actually invalidate the cookie in the browser, leaving
  the user "logged in" after logging out;
- storing the raw password instead of a hash of it.
"""

from datetime import UTC, datetime, timedelta

import jwt
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from taller.identity.adapters.password_hasher import PwdlibPasswordHasher
from taller.shared.config import get_settings

SESSION_COOKIE_NAME = "taller_session"


def test_register_returns_me_and_the_cookie_authenticates_a_later_request(
    client: TestClient, register_payload: dict
) -> None:
    response = client.post("/api/auth/register", json=register_payload)

    assert response.status_code == 201
    body = response.json()
    assert body["user"]["full_name"] == register_payload["owner_name"]
    assert body["user"]["phone"] == "99887766"
    assert body["workshop"]["name"] == register_payload["workshop_name"]

    me_response = client.get("/api/auth/me")
    assert me_response.status_code == 200
    assert me_response.json() == body


def test_register_with_an_already_registered_phone_is_rejected(
    client: TestClient, register_payload: dict
) -> None:
    first = client.post("/api/auth/register", json=register_payload)
    assert first.status_code == 201

    second = client.post(
        "/api/auth/register",
        json={**register_payload, "workshop_name": "Otro taller", "owner_name": "Otra persona"},
    )

    assert second.status_code == 409
    assert second.json() == {"detail": "phone_already_registered"}


def test_login_with_wrong_password_and_unknown_phone_return_the_same_401(
    client: TestClient, register_payload: dict
) -> None:
    client.post("/api/auth/register", json=register_payload)

    wrong_password = client.post(
        "/api/auth/login",
        json={"phone": register_payload["phone"], "password": "not-the-right-password"},
    )
    unknown_phone = client.post(
        "/api/auth/login",
        json={"phone": "22334455", "password": register_payload["password"]},
    )

    assert wrong_password.status_code == 401
    assert unknown_phone.status_code == 401
    assert wrong_password.json() == {"detail": "invalid_credentials"}
    assert unknown_phone.json() == wrong_password.json()


def test_login_with_correct_credentials_authenticates_a_later_request(
    client: TestClient, register_payload: dict
) -> None:
    client.post("/api/auth/register", json=register_payload)
    client.cookies.clear()

    login_response = client.post(
        "/api/auth/login",
        json={"phone": register_payload["phone"], "password": register_payload["password"]},
    )
    assert login_response.status_code == 200

    me_response = client.get("/api/auth/me")
    assert me_response.status_code == 200
    assert me_response.json()["user"]["phone"] == "99887766"


def test_me_without_a_cookie_is_not_authenticated(client: TestClient) -> None:
    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json() == {"detail": "not_authenticated"}


def test_me_with_a_tampered_cookie_is_not_authenticated(
    client: TestClient, register_payload: dict
) -> None:
    client.post("/api/auth/register", json=register_payload)
    token = client.cookies.get(SESSION_COOKIE_NAME)
    assert token is not None
    tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
    client.cookies.set(SESSION_COOKIE_NAME, tampered)

    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json() == {"detail": "not_authenticated"}


def test_me_with_an_expired_cookie_is_not_authenticated(
    client: TestClient, register_payload: dict
) -> None:
    register_response = client.post("/api/auth/register", json=register_payload)
    me_body = register_response.json()

    settings = get_settings()
    expired_token = jwt.encode(
        {
            "sub": me_body["user"]["id"],
            "wid": me_body["workshop"]["id"],
            "iat": datetime.now(UTC) - timedelta(days=31),
            "exp": datetime.now(UTC) - timedelta(days=1),
        },
        settings.jwt_secret,
        algorithm="HS256",
    )
    client.cookies.set(SESSION_COOKIE_NAME, expired_token)

    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json() == {"detail": "not_authenticated"}


def test_logout_clears_the_session_cookie(client: TestClient, register_payload: dict) -> None:
    client.post("/api/auth/register", json=register_payload)

    logout_response = client.post("/api/auth/logout")

    assert logout_response.status_code == 204
    assert client.cookies.get(SESSION_COOKIE_NAME) is None
    assert client.get("/api/auth/me").status_code == 401


def test_password_is_never_stored_in_plain_text(
    client: TestClient, register_payload: dict, db_session: Session
) -> None:
    client.post("/api/auth/register", json=register_payload)

    stored_hash = db_session.execute(
        text("SELECT password_hash FROM users WHERE phone = :phone"),
        {"phone": "99887766"},
    ).scalar_one()

    assert stored_hash != register_payload["password"]
    assert PwdlibPasswordHasher().verify(register_payload["password"], stored_hash)

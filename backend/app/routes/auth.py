"""Routes for Google OAuth login, callback, logout, and current user."""

from authlib.integrations.starlette_client import OAuthError
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app import auth, config, schemas
from app.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])

# Google redirects back here after the user consents.
CALLBACK_PATH = "/auth/callback"


@router.get("/login")
async def login(request: Request):
    """Start the OAuth flow by redirecting the user to Google."""
    redirect_uri = str(request.url_for("auth_callback"))
    # access_type=offline + prompt=consent ensure Google returns a refresh token
    # so we can read Gmail later without the user being present.
    return await auth.oauth.google.authorize_redirect(
        request, redirect_uri, access_type="offline", prompt="consent"
    )


@router.get("/callback", name="auth_callback")
async def auth_callback(request: Request, db: Session = Depends(get_db)):
    """Handle Google's redirect: exchange code, upsert user, set session cookie."""
    try:
        token = await auth.oauth.google.authorize_access_token(request)
    except OAuthError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="OAuth failed"
        )

    claims = token.get("userinfo")
    if not claims:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="No user info returned"
        )

    user = auth.upsert_user(db, claims)
    auth.save_google_tokens(db, user, token)
    session = auth.create_session(db, user)

    response = RedirectResponse(url=config.FRONTEND_URL)
    response.set_cookie(
        key=config.SESSION_COOKIE_NAME,
        value=session.token,
        httponly=True,
        samesite="lax",
        max_age=config.SESSION_TTL_DAYS * 24 * 60 * 60,
        path="/",
    )
    return response


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, db: Session = Depends(get_db)):
    """Delete the current session and clear the cookie."""
    token = request.cookies.get(config.SESSION_COOKIE_NAME)
    if token:
        auth.delete_session(db, token)
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie(key=config.SESSION_COOKIE_NAME, path="/")
    return response


@router.get("/me", response_model=schemas.User)
def me(current_user=Depends(auth.get_current_user)):
    """Return the currently logged-in user."""
    return current_user

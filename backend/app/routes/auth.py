"""Routes for Google OAuth login, callback, logout, and current user."""

from authlib.integrations.starlette_client import OAuthError
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app import auth, config, demo, schemas
from app.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])

# Google redirects back here after the user consents.
CALLBACK_PATH = "/auth/callback"


@router.get("/login")
async def login(request: Request):
    """Start the OAuth flow by redirecting the user to Google.

    Requests identity scopes only (non-sensitive), so any Google user can sign
    in without app verification. Gmail access is a separate opt-in step.
    """
    redirect_uri = str(request.url_for("auth_callback"))
    return await auth.oauth.google.authorize_redirect(request, redirect_uri)


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

    # Login establishes identity only; Gmail tokens are managed by the separate
    # /auth/gmail/connect flow so a plain sign-in never touches Gmail access.
    user = auth.upsert_user(db, claims)
    session = auth.create_session(db, user)

    response = RedirectResponse(url=config.FRONTEND_URL)
    response.set_cookie(
        key=config.SESSION_COOKIE_NAME,
        value=session.token,
        httponly=True,
        samesite=config.COOKIE_SAMESITE,
        secure=config.COOKIE_SECURE,
        max_age=config.SESSION_TTL_DAYS * 24 * 60 * 60,
        path="/",
    )
    return response


@router.get("/gmail/connect", name="gmail_connect")
async def gmail_connect(
    request: Request, current_user=Depends(auth.get_current_user)
):
    """Start the opt-in Gmail authorization for the logged-in user.

    Requests the sensitive gmail.readonly scope via incremental consent.
    access_type=offline + prompt=consent ensure Google returns a refresh token.
    """
    redirect_uri = str(request.url_for("gmail_callback"))
    return await auth.oauth.google_gmail.authorize_redirect(
        request,
        redirect_uri,
        access_type="offline",
        prompt="consent",
        include_granted_scopes="true",
    )


@router.get("/gmail/callback", name="gmail_callback")
async def gmail_callback(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(auth.get_current_user),
):
    """Handle Google's Gmail-consent redirect: store the user's Gmail tokens."""
    try:
        token = await auth.oauth.google_gmail.authorize_access_token(request)
    except OAuthError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="OAuth failed"
        )
    auth.save_google_tokens(db, current_user, token)
    return RedirectResponse(url=config.FRONTEND_URL)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, db: Session = Depends(get_db)):
    """Delete the current session and clear the cookie."""
    token = request.cookies.get(config.SESSION_COOKIE_NAME)
    if token:
        auth.delete_session(db, token)
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie(
        key=config.SESSION_COOKIE_NAME,
        path="/",
        samesite=config.COOKIE_SAMESITE,
        secure=config.COOKIE_SECURE,
    )
    return response


@router.post("/demo", response_model=schemas.User)
def demo_login(response: Response, db: Session = Depends(get_db)):
    """Create a throwaway demo account, seed it, and set a session cookie."""
    if not config.DEMO_MODE_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Demo mode is disabled"
        )
    user = demo.create_demo_user(db)
    session = auth.create_session(db, user)
    response.set_cookie(
        key=config.SESSION_COOKIE_NAME,
        value=session.token,
        httponly=True,
        samesite=config.COOKIE_SAMESITE,
        secure=config.COOKIE_SECURE,
        max_age=config.SESSION_TTL_DAYS * 24 * 60 * 60,
        path="/",
    )
    return user


@router.get("/me", response_model=schemas.User)
def me(current_user=Depends(auth.get_current_user)):
    """Return the currently logged-in user."""
    return current_user


@router.post("/extension-token", response_model=schemas.ExtensionToken)
def create_extension_token(
    db: Session = Depends(get_db),
    current_user=Depends(auth.get_current_user),
):
    """Mint a new session token for the browser extension to use as a bearer.

    This is a distinct session from the web login, so revoking or expiring the
    extension token never signs the user out of the web app (and vice versa).
    """
    session = auth.create_session(db, current_user)
    return schemas.ExtensionToken(token=session.token, expires_at=session.expires_at)

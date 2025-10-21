from json import loads, dumps
from utils import Logger, build_allowlist_from_routes
from fastapi import FastAPI, Query, status, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import FileResponse, JSONResponse
from starlette.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models.requests import CreateWalletRequest, UpdateWalletInfoRequest
from backend.database import dbpool, create_db_and_tables
from models.responses import WalletsResponse
from security.tokenization import test_authorization_token, get_current_user_session
from services.broadcaster import broadcaster
from utils import check_association

logger = Logger("app")

app = FastAPI(title="Wallets Service", version="0.1.0")

# Cross Origins trusted hosts
allowed_origins = ["https://yoursbtc.com", "http://localhost:4200"]
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_origins=allowed_origins
)


@app.on_event("startup")
async def startup_event():
    create_db_and_tables()


@app.get("/robots.txt", include_in_schema=False)
async def robots_txt():
    return FileResponse("static/robots.txt", media_type="text/plain")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon_ico():
    return FileResponse("static/favicon.ico", media_type="image/x-icon")


@app.post("/create", response_model=WalletsResponse)
@test_authorization_token
async def create_wallet(request: CreateWalletRequest, req: Request):
    logger.info("============ Create Wallet ============")
    logger.debug(f"Logging in user {request=}")
    session_id = await get_current_user_session(req)
    if not session_id:
        logger.error(f"cannot login without session id")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    logger.debug(f"session id {session_id=}")
    user = None
    with dbpool as conn:
        logger.debug(f"Searching for user {session_id=}")
        user = conn.find('user', user_id=session_id)
        if not user:
            logger.error(f"not found {user=}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        logger.debug(f"User found {user=}")
        validation_status = await broadcaster.test_wallet(
            address=request.public_address,
            network=request.network,
            auth_token=req.headers.get('Authorization').split(' ')[1]
        ).get('results').get('mempool').get('ok')
        if not validation_status:
            logger.error(f"wallet is invalid")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid wallet")
        wallet = conn.add_wallet(
            user_id=user.user_id,
            name=request.name,
            network=request.network,
            force_testnet=request.force_testnet,
            public_address=request.public_address,
            validated_by_blockchain=validation_status
        )
        logger.debug(f"User create {wallet=}")
        user = conn.update('user', user=user)
        logger.debug(f"User create {user=}")
        return WalletsResponse(user_id=user.user_id, user_wallets=user.wallets)


@app.put("/update", response_model=WalletsResponse)
@test_authorization_token
async def update_wallet(request: UpdateWalletInfoRequest, req: Request):
    logger.info("============ Update Wallet ============")
    logger.debug(f"Registering user {request=}")
    session_id = await get_current_user_session(req)
    if not session_id:
        logger.error(f"cannot register without session id")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    logger.debug(f"session id {session_id=}")
    user = None
    with dbpool as conn:
        logger.debug(f"searching for user {request.username=}")
        user = conn.find('user', user_id=session_id)
        if user:
            logger.error(f"not found {user=}")
            raise HTTPException(status_code=status.HTTP_302_FOUND, detail="User already exists")
        wallet = conn.find('wallet', wallet_id=request.wallet_id)
        if not wallet:
            logger.error(f"wallet not found {request.wallet_id=}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")
        if not check_association(user=user, wallet=wallet):
            logger.error(f"{wallet.wallet_id=} not associated to{user.user_id=}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")
        logger.debug(f"User found {user=}")
        wallet = conn.update('wallet', wallet=request)
        logger.debug(f"User update {wallet=}")
        conn.update('user', user=user)
        logger.debug(f"User update {user=}")
        return WalletsResponse(user_id=user.user_id, user_wallets=user.wallets)


@app.get("/get", response_model=WalletsResponse)
@test_authorization_token
async def get_wallet(
        req: Request,
        wallet_id: str = Query(..., min_length=16),

):
    logger.info("============ Get Wallet ============")
    logger.debug(f"call get_wallet, params({wallet_id=})")
    session_id = await get_current_user_session(req)
    if not session_id:
        logger.error(f"cannot login without session id")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    logger.debug(f"session id {session_id=}")
    user = None
    with dbpool as conn:
        logger.debug(f"Searching for user {wallet_id=}")
        user = conn.find('user', user_id=session_id)
        if not user:
            logger.error(f"{user=} not found")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        logger.debug(f"User found {user=}")
        wallet = conn.find('wallet', wallet_id=wallet_id)
        if not wallet:
            logger.error(f"wallet not found {wallet_id=}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")
        if not check_association(user=user, wallet=wallet):
            logger.error(f"{wallet.wallet_id=} not associated to{user.user_id=}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")
        logger.debug(f"User found {wallet=}")
        return WalletsResponse(user_id=user.user_id, user_wallets=user.wallets)



class PathWhitelistMiddleware(BaseHTTPMiddleware):
    """
    Middleware for restricting access to specific paths based on a whitelist.

    This middleware intercepts incoming HTTP requests and restricts access to
    certain paths that are not explicitly allowed for the application. The
    allowed paths are defined in a whitelist and are checked against each
    request's URL path. It supports both exact string matching and regex-based
    matching for path validation. Requests to paths not in the whitelist are
    blocked, and a 403 Forbidden response is returned, except for CORS `OPTIONS`
    method, which is always allowed.

    Attributes:
        ALLOWED_PATHS: List of paths or regex patterns representing the allowed
        routes.

    Methods:
        dispatch: Asynchronous handler for intercepting HTTP requests and
        enforcing the path-based whitelist logic.
    """
    ALLOWED_PATHS = build_allowlist_from_routes(app)
    async def dispatch(self, request, call_next):
        path = request.url.path
        method = request.method.upper()

        # Always allow OPTIONS for CORS
        if method == "OPTIONS":
            return await call_next(request)

        # Check against whitelist (supports regex)
        for allowed in self.ALLOWED_PATHS:
            if (isinstance(allowed, str) and path == allowed) or \
               (hasattr(allowed, "match") and allowed.match(path)):
                return await call_next(request)

        # Anything not in ALLOWED_PATHS is blocked
        return JSONResponse(content=loads(dumps({"message": "Forbidden path"})), status_code=status.HTTP_403_FORBIDDEN)


app.add_middleware(middleware_class=PathWhitelistMiddleware)

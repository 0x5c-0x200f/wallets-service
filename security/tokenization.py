import jwt
from fastapi import HTTPException, status, Request
from functools import wraps
from decouple import config
from utils import Logger

logger = Logger("security.tokenization")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
SECRET_KEY = bytes.fromhex(config("TOKEN_KEY"))


def test_authorization_token(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        logger.debug(f"call test_authorization_token, on {func.__name__}")
        request = kwargs.get('request')  # Get the request object from kwargs
        if not request or "Authorization" not in request.headers:
            logger.error(f"call test_authorization_token, on {func.__name__} , {request=} or Authorization header missing")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization header missing")
        authorization: str = request.headers.get('Authorization')
        if not authorization:
            logger.error(f"call test_authorization_token, on {func.__name__} , Authorization header is empty")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization header is empty")
        try:
            # Extract the token from the Authorization header
            user_id = await get_current_user_session(request)
            if not user_id:
                logger.error(f"call test_authorization_token, on {func.__name__} , Invalid token")
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
            logger.debug(f"call test_authorization_token, on {func.__name__} , Token is valid")
            return await func(*args, **kwargs)
        except jwt.ExpiredSignatureError:
            logger.error(f"call test_authorization_token, on {func.__name__} , Token has expired")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
        except jwt.PyJWTError:
            logger.error(f"call test_authorization_token, on {func.__name__} , Invalid token")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return wrapper


async def decode_jwt(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user_id = payload.get("sub")
    return user_id


async def get_current_user_session(request: Request):
    if 'docs' in request.url.path or 'openapi.json' in request.url.path:
        return None
    if 'Authorization' not in request.headers:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing AuthHeaders")
    token = request.headers.get('Authorization').split(' ')[1]
    try:
        # return the user_id
        return await decode_jwt(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

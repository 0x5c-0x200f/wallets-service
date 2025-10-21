from __future__ import annotations
from typing import Annotated, Generator, Optional
from decouple import config as EnvConfig
from fastapi import Depends
from sqlmodel import SQLModel, Session, select, create_engine, update
from sqlalchemy.orm import sessionmaker
from backend.tables import Wallet, User
from utils import sm_get_secret_data, Singleton, timestamp_update, Logger

logger = Logger("backend.database")

# ---------- URL & engine ----------
if EnvConfig("LOCAL", default="0") == "1":
    # SQLite for local dev
    database_url = "sqlite:///local.db"
    engine = create_engine(
        database_url,
        echo=False,
        connect_args={"check_same_thread": False},  # needed for SQLite in threaded servers
    )
else:
    # Postgres via AWS Secrets Manager
    data = sm_get_secret_data("database")  # expects username/password in the secret
    # Example: DATABASE_URL="%(username)s:%(password)s@db-host:5432/appdb"
    db_info = EnvConfig("DATABASE_URL") % (data["username"], data["password"], data["username"])
    # If your format is different, adapt the %-formatting above accordingly.
    database_url = f"postgresql+psycopg2://{db_info}?sslmode=require"
    engine = create_engine(
        database_url,
        echo=False,
        pool_pre_ping=True,
        pool_size=int(EnvConfig("DB_POOL_SIZE", default="10")),
        max_overflow=int(EnvConfig("DB_MAX_OVERFLOW", default="20")),
        pool_recycle=int(EnvConfig("DB_POOL_RECYCLE", default="300")),
        pool_timeout=int(EnvConfig("DB_POOL_TIMEOUT", default="10")),
    )

# One session factory for the whole service
SessionLocal = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)

# ---------- helpers for app startup / FastAPI DI ----------
def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency — yields a bound Session per request."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

SessionDep = Annotated[Session, Depends(get_session)]

# ---------- Optional context-managed pool for manual usage ----------
class DbConnectionPool(metaclass=Singleton):
    """
    Lightweight context manager that opens/closes a *bound* Session.
    Usage:
        with dbpool as conn:
            conn.find_user("alice")
    """
    _session: Optional[Session] = None

    def __enter__(self) -> "DbConnectionPool":
        logger.debug("Opening database connection pool")
        self._session = SessionLocal()
        logger.debug(f"Database connection pool opened {self._session}")
        return self

    def __exit__(self, exc_type, exc, tb):
        logger.debug("Closing database connection pool")
        if self._session is None:
            logger.debug("Database connection pool already closed")
            return
        try:
            if exc is None:
                logger.debug("Committing database changes")
                self._session.commit()
            else:
                logger.debug("Rolling back database changes")
                self._session.rollback()
        finally:
            logger.debug("Closing database connection")
            self._session.close()
            logger.debug("Database connection pool closed")
            self._session = None
            logger.debug(f"DbConnectionPool._session={self._session}")


    # ---- CRUD helpers (SQLModel style) ----
    def all_wallets(self):
        logger.debug("call all_wallets")
        if self._session is None:
            logger.error("Session not opened. Use 'with dbpool as conn:'")
            raise RuntimeError("Session not opened. Use 'with dbpool as conn:'")
        return self._session.exec(select(Wallet)).all()

    def find(self, resource: str, user_id: str = None, wallet_id: str = None) -> Optional[Wallet]:
        logger.debug(f"call find_user, params({user_id=}, {wallet_id=})")
        if self._session is None:
            logger.error("Session not opened. Use 'with dbpool as conn:'")
            raise RuntimeError("Session not opened. Use 'with dbpool as conn:'")
        if resource == "wallet":
            resource = Wallet
        elif resource == "user":
            resource = User
        else:
            raise ValueError(f"Unknown resource: {resource}")
        if user_id:
            return self._session.exec(select(resource).where(resource.user_id == user_id)).first()
        elif wallet_id:
            return self._session.exec(select(resource).where(resource.wallet_id == wallet_id)).first()
        else:
            raise ValueError("Either user_id or wallet_id must be provided")

    def add_wallet(self,
                   user_id: str,
                   name: str,
                   network: str,
                   force_testnet: bool,
                   public_address: str,
                   validated_by_blockchain: bool
       ) -> Wallet:
        logger.debug(f"call add_user, params({user_id=}, {name=}, {network=}, {force_testnet=}, {public_address=}, {validated_by_blockchain=})")
        if self._session is None:
            logger.error("Session not opened. Use 'with dbpool as conn:'")
            raise RuntimeError("Session not opened. Use 'with dbpool as conn:'")
        stamp = timestamp_update()
        logger.debug(f"creating user with timestamp={stamp}")
        user = self.find('user', user_id=user_id)
        if not user:
            raise ValueError(f"User with id={user_id} not found")
        wallet = Wallet(
            name=f"wallet-{name}-{stamp}",
            public_address=public_address,
            network=network,
            force_testnet=force_testnet,
            validated_by_blockchain=validated_by_blockchain,
            user_id=user.user_id,
            user=user
        )
        logger.debug(f"user={user}")
        user.wallets.append(wallet)
        user.updated_at = timestamp_update()
        self._session.add(wallet)
        self._session.add(user)
        self._session.flush()   # assign PKs
        self._session.refresh(wallet)
        self._session.refresh(user)
        return user

    def update(self, resource: str, user: User = None, wallet: Wallet = None) -> User | Wallet:
        logger.debug(f"call update_user, user={user}")
        try:
            if self._session is None:
                logger.error("Session not opened. Use 'with dbpool as conn:'")
                raise RuntimeError("Session not opened. Use 'with dbpool as conn:'")
            if resource == "wallet":
                resource = Wallet
            elif resource == "user":
                resource = User
            else:
                raise ValueError(f"Unknown resource: {resource}")
            if user:
                user.updated_at = timestamp_update()
                statement = update(resource).where(resource.user_id == user.user_id).values(
                    {field: getattr(user, field) for field in user.model_fields_set}
                )
            elif wallet:
                wallet.updated_at = timestamp_update()
                statement = update(resource).where(resource.wallet_id == wallet.wallet_id).values(
                    {field: getattr(user, field) for field in user.model_fields_set}
                )

            self._session.exec(statement)
            self._session.commit()
            self._session.flush()
            return user
        except Exception as e:
            logger.error(f"call update_user, end with error : {e}")
            raise e


dbpool = DbConnectionPool()

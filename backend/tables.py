from sqlmodel import SQLModel, Field, Relationship
from uuid import uuid4
from typing import Optional, List
from datetime import datetime
from utils import timestamp_update


class User(SQLModel, table=True):
    __tablename__ = "users_tbl"
    user_id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    name: str = Field(index=True)
    username: str = Field(index=True)
    active: bool = Field(index=True, default=False)
    signed_password: str = Field(index=True)
    last_login: Optional[datetime] = Field(index=True, default=None)
    created_at: datetime = Field(index=True, default_factory=timestamp_update)
    updated_at: datetime = Field(index=True, default_factory=timestamp_update)

    # Relationships
    api_key: Optional["ApiKey"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"lazy": "joined"}
    )
    wallets: List["Wallet"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"lazy": "joined"}
    )
    transactions: List["Transaction"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"lazy": "select"}
    )
    beneficials: List["Beneficial"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"lazy": "select"}
    )


class ApiKey(SQLModel, table=True):
    __tablename__ = "api_keys_tbl"
    api_key_id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    active: bool = Field(index=True, default=False)
    key_content: str = Field(index=True, max_length=320)
    last_used: Optional[datetime] = Field(index=True, default=None)
    created_at: datetime = Field(index=True, default_factory=timestamp_update)
    updated_at: datetime = Field(index=True, default_factory=timestamp_update)

    user_id: str = Field(foreign_key="users_tbl.user_id", unique=True, index=True)
    user: "User" = Relationship(back_populates="api_key")


class Wallet(SQLModel, table=True):
    __tablename__ = "wallets_tbl"
    wallet_id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    name: Optional[str] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=timestamp_update, index=True)
    updated_at: datetime = Field(default_factory=timestamp_update, index=True)
    public_address: Optional[str] = Field(default=None, index=True, max_length=128)
    network: Optional[str] = Field(default=None, index=True)
    force_testnet: bool = Field(default=False, index=True)
    validated_by_blockchain: bool = Field(default=False, index=True)

    user_id: str = Field(foreign_key="users_tbl.user_id", index=True)
    user: "User" = Relationship(back_populates="wallets")
    transactions: List["Transaction"] = Relationship(
        back_populates="wallet",
        sa_relationship_kwargs={"lazy": "select"}
    )
    beneficial: "Beneficial" = Relationship(back_populates="wallets")


class Transaction(SQLModel, table=True):
    __tablename__ = "transactions_tbl"
    transaction_id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    from_wallet: Optional[str] = Field(default=None, index=True)
    to_wallet: Optional[str] = Field(default=None, index=True)
    description: Optional[str] = Field(default=None, index=True, max_length=512)
    amount: Optional[float] = Field(default=None, index=True)
    created_at: Optional[datetime] = Field(default=None, index=True)
    signature: Optional[str] = Field(default=None, index=True)
    network: str = Field(default="bitcoin", index=True)

    # Foreign Keys - REMOVED unique=True constraints
    wallet_id: str = Field(foreign_key="wallets_tbl.wallet_id", index=True)
    user_id: str = Field(foreign_key="users_tbl.user_id", index=True)
    beneficial_id: str = Field(foreign_key="beneficials_tbl.beneficial_id", index=True)

    # Relationships
    wallet: "Wallet" = Relationship(back_populates="transactions")
    user: "User" = Relationship(back_populates="transactions")
    beneficial: "Beneficial" = Relationship(back_populates="transaction")


class Beneficial(SQLModel, table=True):
    __tablename__ = "beneficials_tbl"
    beneficial_id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    legal_name: Optional[str] = Field(default=None, index=True)
    personal_id: Optional[str] = Field(default=None, index=True)
    phone_number: Optional[str] = Field(default=None, index=True)
    address: Optional[str] = Field(default=None, index=True)
    email: Optional[str] = Field(default=None, index=True)
    created_at: Optional[datetime] = Field(default=None, index=True)

    user_id: str = Field(foreign_key="users_tbl.user_id", index=True)
    wallet_id: str = Field(foreign_key="wallets_tbl.wallet_id", index=True)

    # Relationships
    user: "User" = Relationship(back_populates="beneficials")

    wallets: List["Wallet"] = Relationship(
        back_populates="beneficial",
        sa_relationship_kwargs={"lazy": "joined"}
    )

    transaction: Optional["Transaction"] = Relationship(back_populates="beneficial")


class Broadcast(SQLModel, table=True):
    __tablename__ = "broadcasts_tbl"
    broadcast_id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    user_id: str = Field(foreign_key="users_tbl.user_id", index=True)
    transaction_id: str = Field(foreign_key="transactions_tbl.transaction_id", index=True)
    created_at: Optional[datetime] = Field(default=None, index=True)
    updated_at: Optional[datetime] = Field(default=None, index=True)
    txid: str = Field(default=None, index=True, unique=True, nullable=True)
    status: str = Field(default=None, index=True, nullable=True)

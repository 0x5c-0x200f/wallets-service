from typing import Optional
from json import loads, dumps
from pydantic import BaseModel, Field


class BaseResponse(BaseModel):
    def tojson(self): return loads(dumps(self.__dict__))


class UserWalletObject(BaseResponse):
    wallet_name: str                            =   Field(..., alias="wallet_name")
    wallet_id: str                              =   Field(..., alias="wallet_id")
    created_at: str                             =   Field(..., alias="created_at")
    public_address: str                         =   Field(..., alias="public_address")
    network: str                                =   Field(..., alias="network")
    force_testnet: bool                         =   Field(..., alias="force_testnet")
    blockchain_validated: bool                  =   Field(..., alias="blockchain_validated")
    def __repr__(self): return f"<UserWalletObject %e>" % self.tojson()


class WalletsResponse(BaseResponse):
    user_id: str                                =    Field(..., alias="user_id")
    user_wallets: list[UserWalletObject]        =    Field(..., alias="user_wallets")
    def __repr__(self): return f"<WalletsResponse %r>" % self.tojson()


class WalletDeletedResponse(BaseResponse):
    wallet_id: str                              =   Field(..., alias="wallet_id")
    deleted: bool                               =   Field(default=False, alias="deleted")
    def __repr__(self): return f"<WalletDeletedResponse %r>" % self.tojson()

from typing import Optional
from json import loads, dumps
from utils import timestamp_update
from pydantic import BaseModel, Field


class BaseRequest(BaseModel):
    update_at: Optional[str]                =   Field(default_factory=timestamp_update, alias="update_at")
    created_at: Optional[str]               =   Field(default_factory=timestamp_update, alias="created_at")
    def tojson(self): return loads(dumps(self.__dict__))


class CreateWalletRequest(BaseRequest):
    public_address: str                     =   Field(..., alias="public_address")
    wallet_name: str                        =   Field(..., alias="wallet_name")
    force_testnet: Optional[bool]           =   Field(default=False, alias="force_testnet")
    network: Optional[str]                  =   Field(default="bitcoin", alias="network")
    user_id: str                            =   Field(default=None, alias="user_id")
    def __repr__(self): return f"<CreateWalletRequest %r>" % self.tojson()


class UpdateWalletInfoRequest(BaseRequest):
    name: str                               =   Field(..., alias="name")
    wallet_id: Optional[str]                =   Field(default=None, alias="wallet_id")
    network: Optional[str]                  =   Field(default="bitcoin", alias="network")
    force_testnet: Optional[bool]           =   Field(default=False, alias="force_testnet")
    public_address: str                     =   Field(..., alias="public_address")
    validated_by_blockchain: Optional[bool] =   Field(default=False, alias="validated_by_blockchain")
    def __repr__(self): return f"<UpdateWalletInfoRequest %r>" % self.tojson()

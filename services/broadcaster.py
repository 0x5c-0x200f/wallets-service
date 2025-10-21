import requests
from utils import Logger, Singleton

logger = Logger("services.broadcaster")

class Broadcaster(metaclass=Singleton):

    base_url = "https://broadcast.yoursbtc.com"

    headers = {"Content-Type": "application/json"}

    def __init__(self):
        super(Broadcaster, self).__init__()
        self._session = requests.Session()

    async def test_wallet(self, address: str, network: str, auth_token: str):
        try:
            url = f"{self.base_url}/wallets/status?address={address}&network={network}"
            self._session.headers.update({"Authorization": f"Bearer {auth_token}"})
            response = self._session.post(url=url, headers=self.headers)
            response.raise_for_status()
            data = await response.json()
            logger.debug(f"test_wallet response: {data}")
            return data
        except Exception as e:
            logger.error(f"Error testing wallet: {e}")
            raise e

broadcaster = Broadcaster()
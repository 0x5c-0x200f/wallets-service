import re
import boto3
import logging
from json import loads
from decouple import config
from datetime import datetime
from botocore import exceptions
from os.path import join, dirname, abspath, exists
from logging.handlers import RotatingFileHandler



class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Logger(object, metaclass=Singleton):

    logs_dir = join(dirname(abspath(__file__)), "logs")
    def __init__(self, logger_name: str):
        self._logger = logging.getLogger(logger_name)
        self._logger.setLevel(logging.DEBUG)
        handler = RotatingFileHandler(join(self.logs_dir, "runtime.log"), maxBytes=52428800, backupCount=7)
        formatter = logging.Formatter('[%(name)s] %(asctime)s [%(levelname)s] %(message)s')
        handler.setFormatter(formatter)
        self._logger.addHandler(handler)

    def _log(self, message: str, level: int = logging.INFO): self._logger.log(level=level, msg=message)
    def info(self, message: str): self._log(message, level=logging.INFO)
    def debug(self, message: str): self._log(message, level=logging.DEBUG)
    def warning(self, message: str): self._log(message, level=logging.WARN)
    def error(self, message: str): self._log(message, level=logging.ERROR)

logger = Logger("utils")

def get_server_certificate():
    root_dir = dirname(abspath(__file__))
    if exists(join(root_dir, "server.pem")) and exists(join(root_dir, "server.key")):
        return join(root_dir, "server.key"), join(root_dir, "server.pem")
    else:
        raise FileNotFoundError("Server certificate not found")


def timestamp_update():
    return datetime.utcnow()


def build_allowlist_from_routes(app):
    """
        :params - app: FastAPI Application
        This metho iterates through the app.routes which were loaded to the app.
        Any api route is included at the `paths` variable
    """
    paths = []
    for route in app.routes:
        if hasattr(route, "path"):
            regex = route.path.replace("{", "(?P<").replace("}", ">[^/]+)") + "$"
            paths.append(re.compile("^" + regex))
    return paths


def get_aws_credentials():
    return {"access_key_id": config("AWS_ACCESS_KEY"), "secret_access_key": config("AWS_SECRET_ACCESS_KEY")}


def sm_get_secret_data(key: str):
    if not key:
        raise KeyError("Missing key")
    if key == "database":
        key = config("SM_DB_KEY")
    try:
        if config("LOCAL") == "1":
            creds = get_aws_credentials()
            session = boto3.session.Session(
                aws_secret_access_key=creds.get("secret_access_key"),
                aws_access_key_id=creds.get("access_key_id"), region_name="us-east-1").client(
                "secretsmanager"
            )
        else:
            session = boto3.session.Session(region_name="us-east-1").client("secretsmanager")
        return loads(
            session.get_secret_value(SecretId=key).get("SecretString")
        )
    except (Exception, exceptions.ClientError) as e:
        raise e


def check_association(user, wallet):
    found = False
    for user_wallet in user.wallets:
        if user_wallet.wallet_id == wallet.wallet_id:
            found = True
            break
    return found

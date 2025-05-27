import json
from ..utils.retry import retry
import requests
from loguru import logger


class XterioAPI:
    def __init__(self, proxy, user_agent, wallet_address):
        self.name = "Xterio API"
        self.proxy = proxy
        self.wallet_address = wallet_address
        self.user_agent = user_agent
        self.proxies = {"http": self.proxy, "https": self.proxy}
        self.headers = {
            "accept": "application/json",
            "accept-encoding": "gzip,deflate,zstd",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "origin": "https://app.xter.io",
            "priority": "u=1, i",
            "referer": "https://app.xter.io/",
            "user-agent": self.user_agent,
            "sec-fetch-dest": "empty",
            # "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
        }
        self.session = requests.Session()

    @retry
    def get_message(self):
        logger.info(
            f"{self.name} - Getting response message for wallet {self.wallet_address}..."
        )

        url = f"https://api.xter.io/account/v1/login/wallet/{self.wallet_address}"

        response = self.session.get(
            url,
            headers=self.headers,
            proxies=self.proxies,
        )

        if response.status_code == 200:
            for cookie in self.session.cookies:
                self.session.cookies.set(cookie.name, cookie.value)

            return response.json()["data"]["message"]

        raise Exception("Non-200 status code ob login message request")

    @retry
    def login(self, signature: str):
        logger.info(f"{self.name} - Logging in with address {self.wallet_address}")

        url = "https://api.xter.io/account/v1/login/wallet"

        payload = {
            "address": self.wallet_address,
            "invite_code": "",
            "provider": "METAMASK",
            "sign": signature,
            "type": "eth",
        }

        response = self.session.post(
            url, headers=self.headers, proxies=self.proxies, json=payload
        )

        if response.status_code == 200:
            data = json.loads(response.text)["data"]

            for cookie in self.session.cookies:
                self.session.cookies.set(cookie.name, cookie.value)

            return data["id_token"]

        logger.warning("Non - 200 status code")
        raise Exception("Non-200 status code on wallet login")

    @retry
    def get_claim_data(self, access_token: str):
        logger.info(
            f"{self.name} - Getting merkle proof for wallet {self.wallet_address}"
        )

        url = "https://api.xter.io/airdrop/v1/user/query/claim/1b13f586-53bf-4827-8c17-5deed560653d?"

        headers = self.headers
        headers["Authorization"] = f"Bearer {access_token}"

        response = self.session.get(url, headers=headers, proxies=self.proxies)

        if response.status_code == 200:
            data = response.json()["data"][0]
            return int(data["amount"]), data["address_build"]["merkle_proofs"]

        raise Exception("Non-200 status code on claim info")

from src.utils.retry import retry
from loguru import logger
from eth_account.messages import encode_defunct
from src.api.xterio_api import XterioAPI
from src.clients.evm_client import EvmClient
from src.models.network import Binance


class Runner(EvmClient):

    def __init__(
        self,
        account_name=None,
        private_key=None,
        network=Binance,
        user_agent=None,
        proxy=None,
    ):
        super().__init__(account_name, private_key, network, user_agent, proxy)
        self.api = XterioAPI(self.proxy, self.user_agent, self.address)

    def get_claim_data(self):
        logger.info(f"{self.account_name} | {self.address} - getting claim data")

        try:
            text_message = self.api.get_message()
            encoded_message = encode_defunct(text=text_message)
            signed_hash = self.account.sign_message(encoded_message)
            sign = self.w3.to_hex(signed_hash.signature)

            access_token = self.api.login(sign)
            amount, proofs = self.api.get_claim_data(access_token)

            return amount, proofs

        except Exception as e:
            logger.error(
                f"{self.account_name} | {self.address} | Something went wrong on getting claim data: {str(e)}"
            )

    @retry
    def claim(self, contract, amount, merkle_proofs):
        logger.info(
            f"{self.account_name} | {self.address} | Checking balance first to see if we can afford the claim"
        )

        balance = self.get_eth_balance(self.address)

        if balance < self.w3.to_wei(0.00012, "ether"):
            logger.info(
                f"{self.account_name} | {self.address} | Not enough balance to claim, skipping..."
            )
            return

        logger.info(f"{self.account_name} | {self.address} | Running claim")

        tx_data = contract.functions.claim(amount, merkle_proofs).build_transaction(
            {
                "from": self.address,
                "nonce": self.get_nonce(self.address),
                "gasPrice": int(self.w3.eth.gas_price * 1.02),
                "chainId": self.network.chain_id,
            }
        )

        tx_data["gas"] = int(self.w3.eth.estimate_gas(tx_data) * 1.02)

        signed = self.sign_transaction(tx_data)

        if signed:
            tx_hash = self.send_tx(signed)

            if tx_hash:
                return True

            raise Exception("No tx hash")

        raise Exception("Missing signed transaction")

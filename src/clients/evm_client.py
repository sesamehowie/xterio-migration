from web3 import Web3
import random
import time
from decimal import Decimal
from typing import Self
from loguru import logger
from web3.types import Wei
from eth_account import Account
from ..models.network import Network, Binance
from ..common.constants import (
    GAS_LIMIT_MULTIPLIER,
    GAS_PRICE_MULTIPLIER,
    GAS_AMT_MULTIPLIER,
    MAX_DST_WAIT_TIME,
    ACCEPTABLE_L1_GWEI,
    MAX_RETRIES,
)


class EvmClient:

    def __init__(
        self: Self,
        account_name: str | int = None,
        private_key: str | None = None,
        network: Network = Binance,
        user_agent: str = None,
        proxy: str = None,
    ) -> Self:
        self.account_name = account_name
        self.private_key = private_key
        self.account: Account = Account.from_key(self.private_key)
        self.address = Web3.to_checksum_address(self.account.address)
        self.network = network
        self.rpc = self.network.rpc_list[0]
        self.user_agent = user_agent
        self.chain_id = self.network.chain_id
        self.proxy = proxy
        self.request_kwargs = {
            "headers": {
                "User-Agent": self.user_agent,
                "Content-Type": "application/json",
            },
            "proxies": {
                "http": self.proxy,
                "https": self.proxy,
            },
            "timeout": 60,
        }

        self.w3 = Web3(
            Web3.HTTPProvider(endpoint_uri=self.rpc, request_kwargs=self.request_kwargs)
        )

        self.logger = logger
        self.module_name = "EvmClient"

    @staticmethod
    def to_bytes(data) -> bytes:
        return Web3.to_bytes(data)

    @staticmethod
    def to_wei(amount: float | Decimal, decimals: int) -> int | Wei:
        return int(amount * 10**decimals)

    @staticmethod
    def from_wei(amount_wei: int | Wei, decimals: int):
        return amount_wei / 10**decimals

    def get_nonce(self, address: str) -> int:
        return self.w3.eth.get_transaction_count(address)

    def get_contract(self, contract_addr: str, abi=None):
        contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(contract_addr), abi=abi
        )
        return contract

    def get_tx_params(
        self,
        to_address: str | None = None,
        value: int = 0,
        data: bytes = None,
        default_gas: int = 200000,
        eip_1559: bool = True,
        estimate_gas: bool = True,
        is_for_contract_tx: bool = False,
    ) -> dict:

        if is_for_contract_tx:
            return {
                "from": Web3.to_checksum_address(self.address),
                "nonce": self.get_nonce(self.address),
                "chainId": self.chain_id,
            }

        tx_params = {
            "from": Web3.to_checksum_address(self.address),
            "to": Web3.to_checksum_address(to_address),
            "chainId": self.chain_id,
            "nonce": self.get_nonce(self.address),
            "value": value,
        }

        time.sleep(4)

        if data is not None:
            tx_params["data"] = data

        if eip_1559:
            time.sleep(5)
            base_fee_per_gas = self.w3.eth.get_block("latest")["baseFeePerGas"]
            max_priority_fee_per_gas = self.w3.eth.max_priority_fee
            max_fee_per_gas = max_priority_fee_per_gas + int(
                base_fee_per_gas * GAS_LIMIT_MULTIPLIER
            )
            tx_params["maxPriorityFeePerGas"] = int(
                max_priority_fee_per_gas * GAS_PRICE_MULTIPLIER
            )
            tx_params["maxFeePerGas"] = int(max_fee_per_gas * GAS_PRICE_MULTIPLIER)
        else:
            tx_params["gasPrice"] = int(self.w3.eth.gas_price * GAS_PRICE_MULTIPLIER)
            time.sleep(4)

        if estimate_gas:
            try:
                tx_params["gas"] = int(
                    self.w3.eth.estimate_gas(transaction=tx_params) * GAS_AMT_MULTIPLIER
                )
                time.sleep(4)
            except Exception:
                tx_params["gas"] = default_gas

        return tx_params

    def get_token_info(self, token_addr: str):
        contract = self.get_contract(contract_addr=Web3.to_checksum_address(token_addr))
        decimals = contract.functions.decimals().call()
        name = contract.functions.name().call()
        symbol = contract.functions.symbol().call()
        balance = contract.functions.balanceOf(self.address).call()
        return name, symbol, decimals, balance

    def send_tx(self, signed_tx: dict) -> str:
        timeout = 180
        try:
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        except ValueError:
            return

        if tx_hash:

            res = self.w3.eth.wait_for_transaction_receipt(
                tx_hash.hex(), timeout=timeout
            )

            if res:
                if res["status"] == 1:
                    self.logger.success(
                        f"{self.account_name} | {self.address} | {self.module_name} | Transaction: {self.network.scanner}/tx/0x{tx_hash.hex()}"
                    )
                elif res["status"] == 0:
                    self.logger.warning(
                        f"{self.account_name} | {self.address} | {self.module_name} | Transaction failed: {self.network.scanner}/tx/0x{tx_hash.hex()}"
                    )

                return str(tx_hash.hex())

        self.logger.warning(
            f"{self.account_name} | {self.address} | {self.module_name} | Transaction didn't come through after {timeout} seconds."
        )

        return

    def sign_transaction(self, tx_dict: dict):

        return self.w3.eth.account.sign_transaction(
            transaction_dict=tx_dict, private_key=self.private_key
        )

    def get_eth_balance(self, address: str | None = None):

        return (
            self.w3.eth.get_balance(self.address)
            if address is None
            else self.w3.eth.get_balance(address)
        )

    def get_gas_price(self):
        return self.w3.eth.gas_price

    @staticmethod
    def get_human_amount(amount_wei) -> float:
        return float(f'{(float(Web3.from_wei(amount_wei, "ether"))):.6f}')

    def get_percentile(self, percentages: tuple[str, str]):
        min_percent, max_percent = percentages

        balance = self.get_eth_balance()

        percent_amt = random.randint(
            int(balance * float((int(min_percent) / 100))),
            int(balance * float((int(max_percent) / 100))),
        )
        logger.info(f"Got amount: {percent_amt}")
        return percent_amt

    def get_tx_receipt(self, tx_hash):
        return self.w3.eth.get_transaction_receipt(transaction_hash=tx_hash)

    def change_rpc(self):
        self.logger.debug(
            f"{self.account_name} | {self.address} | {self.module_name} | Changing rpc"
        )

        current_rpc_index = self.network.rpc_list.index(self.rpc)

        if len(self.network.rpc_list) > 1:
            if current_rpc_index == len(self.network.rpc_list) - 1:
                next_rpc = self.network.rpc_list[0]
            else:
                next_rpc = self.network.rpc_list[current_rpc_index + 1]
        else:
            next_rpc = self.network.rpc_list[0]

        self.w3 = Web3(
            Web3.HTTPProvider(endpoint_uri=next_rpc, request_kwargs=self.request_kwargs)
        )
        self.rpc = next_rpc
        self.logger.debug(
            f"{self.account_name} | {self.address} | {self.module_name} | RPC successfully changed! New RPC - {next_rpc}"
        )
        return self

    def wait_for_funds_on_dest_chain(
        self, destination_network: Network, original_balance: int
    ) -> bool:

        destination_client = EvmClient(
            account_name=self.account_name,
            private_key=self.private_key,
            network=destination_network,
            user_agent=self.user_agent,
            proxy=self.proxy,
        )

        exc_count = 0
        runtime = 0
        while True:
            if runtime > MAX_DST_WAIT_TIME:
                return False
            start = time.time()
            try:

                dst_bal = destination_client.get_eth_balance()
                if dst_bal > original_balance:
                    self.logger.success(
                        f"{self.account_name} | {self.address} | {self.module_name} | ETH arrived on {destination_client.network.name}"
                    )

                    return True

                time.sleep(random.randint(10, 15))

                end = time.time()
                runtime += int(end - start)

            except Exception as e:
                self.logger.warning(
                    f"{self.account_name} | {self.address} | {self.module_name} | Something went wrong while waiting on balance - {e}"
                )
                self.logger.warning(
                    f"{self.account_name} | {self.address} | {self.module_name} | Retrying..."
                )

                exc_count += 1
                if exc_count >= MAX_RETRIES:
                    self.change_rpc()
                    exc_count = 0

                time.sleep(random.randint(10, 15))
                end = time.time()

    def wait_for_gas(self):

        self.logger.debug(
            f"Waiting for gas on mainnet to be less than {ACCEPTABLE_L1_GWEI}gwei..."
        )

        manager = EvmClient(
            account_name=self.account_name,
            private_key=self.private_key,
            network=Binance,
            user_agent=self.user_agent,
            proxy=self.proxy,
        )

        desired_gas_wei = Web3.to_wei(ACCEPTABLE_L1_GWEI, "gwei")

        while True:
            try:
                gas_price = manager.get_gas_price()
                if gas_price <= desired_gas_wei:
                    return True
                time.sleep(random.randint(5, 10))
            except Exception:
                time.sleep(random.randint(5, 10))

    def get_allowance(
        self,
        token_address: str,
        spender_address: str,
    ):
        contract = self.get_contract(token_address)
        allowance = contract.functions.allowance(self.address, spender_address).call()
        return allowance

    def check_allowance(
        self,
        token_address: str,
        spender_address: str,
        amount_in_wei: int,
    ) -> bool:
        try:
            contract = self.get_contract(token_address)
            symbol = contract.functions.symbol().call()

            self.logger.info(
                f"{self.account_name} | {self.address} | {self.module_name} | Checking for {symbol} approval"
            )

            approved_amount_in_wei = self.get_allowance(
                token_address=token_address, spender_address=spender_address
            )

            if amount_in_wei <= approved_amount_in_wei:
                self.logger.info(
                    f"{self.account_name} | {self.address} | {self.module_name} | Already approved"
                )
                return False

            result = self.approve(token_address, spender_address, amount_in_wei)

            time.sleep(random.randint(5, 10))
            return result
        except Exception as error:
            logger.error(str(error))

    def approve(
        self,
        token_address: str,
        spender_address: str,
        amount_in_wei: int,
    ) -> bool:
        transaction = (
            self.get_contract(token_address)
            .functions.approve(
                spender_address,
                amount_in_wei,
            )
            .build_transaction(self.get_tx_params(is_for_contract_tx=True))
        )

        signed = self.sign_transaction(tx_dict=transaction)

        if signed:
            return self.send_tx(signed)
        return

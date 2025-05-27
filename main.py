import time
import random
from loguru import logger
from fake_useragent import UserAgent
from itertools import cycle
from runner import Runner
from src.utils.helpers import read_json, read_txt
from src.models.network import Binance

PRIVATE_KEYS = read_txt("data/private_keys.txt")
PROXIES = read_txt("data/proxies.txt")
CONTRACT_DATA = read_json("contracts/XterioWhitelist.json")
PROXY_CYCLE = cycle(PROXIES)


def main():
    wallets_amt = len(PRIVATE_KEYS)
    proxies_amt = len(PROXIES)

    logger.debug(f"Loaded wallets: {wallets_amt}, proxies: {proxies_amt}")

    failed_wallets = []

    for account_name, private_key in enumerate(PRIVATE_KEYS, start=1):
        try:
            runner = Runner(
                account_name,
                private_key,
                Binance,
                UserAgent().chrome,
                next(PROXY_CYCLE),
            )

            contract = runner.get_contract(
                contract_addr=CONTRACT_DATA["address"], abi=CONTRACT_DATA["abi"]
            )

            amount, merkle_proofs = runner.get_claim_data()
            res = runner.claim(contract, amount, merkle_proofs)

            if not res:
                failed_wallets.append(runner.private_key)

        except Exception as e:
            logger.warning(f"{account_name} | Error: {str(e)}")
        finally:
            time.sleep(random.randint(5, 10))

    failed_wallets_amt = len(failed_wallets)

    if failed_wallets_amt > 0:
        with open("failed_wallets.txt", "w") as f:
            for wallet in failed_wallets:
                f.write(wallet + "\n")

    logger.success(
        f"Run complete! Success: {wallets_amt - failed_wallets_amt}/{wallets_amt}, Failed: {failed_wallets_amt}/{wallets_amt}"
    )

    return


if __name__ == "__main__":
    main()

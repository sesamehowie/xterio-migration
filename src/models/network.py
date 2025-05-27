from dataclasses import dataclass


@dataclass
class Network:
    name: str
    chain_id: int
    rpc_list: list[str]
    scanner: str
    eip1559: bool
    native_token: str


Binance = Network(
    "Binance Smart Chain",
    56,
    [
        "https://bsc.blockrazor.xyz",
        "https://bsc-pokt.nodies.app",
        "https://bsc.drpc.org",
    ],
    "https://bscscan.com",
    True,
    "BNB",
)

Ethereum = Network(
    "Ethereum Mainnet",
    1,
    [
        "https://eth.drpc.org",
        "https://eth-pokt.nodies.app",
        "https://eth.meowrpc.com",
        "https://eth.llamarpc.com",
    ],
    "https://etherscan.io",
    True,
    "ETH",
)

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

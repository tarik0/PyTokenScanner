from eth_typing import HexStr
from web3 import Web3
from web3_multicall import Multicall

DEAD_ADDR = "0x000000000000000000000000000000000000dEaD"
NULL_ADDR = "0x0000000000000000000000000000000000000000"


def read_file(path: str):
    """ Read a file. """
    with open(path, "r") as f:
        return f.read()


def get_token_info(w3: Web3, token_addr: HexStr):
    """ Print the basic token information. """
    # Ready multicall.
    multicall = Multicall(w3.eth)

    # Ready contract.
    token_abi = read_file("./abi/IERC20.json")
    token_contract = w3.eth.contract(address=token_addr, abi=token_abi)

    # Multicall.
    result = multicall.aggregate([
        token_contract.functions.name(),
        token_contract.functions.symbol(),
        token_contract.functions.decimals(),
        token_contract.functions.totalSupply(),
        token_contract.functions.balanceOf(DEAD_ADDR),
        token_contract.functions.balanceOf(NULL_ADDR)
    ])

    # Print.
    decimal = result.results[2].results[0]
    symbol = result.results[1].results[0]
    print("┳ TOKEN INFO")
    print(f"┣ Name        : {result.results[0].results[0]}")
    print(f"┣ Symbol      : {symbol}")
    print(f"┣ Decimals    : {decimal}")
    print("┣ Total Supply: {:,} {}".format(result.results[3].results[0] / (10 ** decimal), symbol))
    print("┣ Total Burnt : {:,} {}".format((result.results[4].results[0] + result.results[5].results[0]) / (10 ** decimal), symbol))


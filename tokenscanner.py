import panoramix.decompiler
import web3.constants
from eth_typing import HexStr
from panoramix.decompiler import decompile_address, decompile_bytecode

from sys import argv
from re import compile, fullmatch
from dotenv import load_dotenv
from os import environ, _exit

from panoramix.loader import Loader
from panoramix.vm import VM
from web3 import Web3
from web3.exceptions import TransactionNotFound

from basic import get_token_info, read_file
from evm import check_storage_usage, is_using_add_liquidity_eth, is_func_payable
from fourbyte import get_function_names
from hardhat import set_hardhat_config, start_node, stop_node


def is_transaction_valid(tx_hash) -> bool:
    """ Checks if string is a valid TX hash. """
    pattern = compile(r"^0x[a-fA-F\d]{64}")
    return bool(fullmatch(pattern, tx_hash))


def main():
    """ Entry point. """
    # Check the args.
    if len(argv) < 2 or not is_transaction_valid(argv[1]):
        print("Usage : scanner.py [token deploy transaction hash]")
        print("Ex.   : scanner.py 0xfe898b7b3d151929ae8e96745340e4ced6af6695b994403d178584202c6dc44f")
        return

    # Load env.
    load_dotenv()

    # Connect the provider.
    w3 = Web3(Web3.HTTPProvider(environ["RPC_ENDPOINT"]))
    if not w3.isConnected():
        print(f"Unable to connect to the RPC: {environ['RPC_ENDPOINT']}")

    # Get deploy receipt.
    deploy_hash: HexStr = HexStr(argv[1])
    deploy_tx, deploy_receipt = None, None
    try:
        deploy_receipt = w3.eth.get_transaction_receipt(deploy_hash)
        deploy_tx = w3.eth.get_transaction(deploy_hash)
    except TransactionNotFound as e:
        print(f"Unable to get the deploy transaction! ({str(e)})")

    # Get target token address.
    token_addr = deploy_receipt.contractAddress

    # Get basic info.
    get_token_info(w3, token_addr)

    # Get token code.
    code = w3.eth.get_code(token_addr)
    code = code.hex()

    # Decompile the contract.
    loader = Loader()
    loader.load_binary(code)
    loader.run(VM(loader, just_fdests=True))

    # Get function names.
    functions = get_function_names(loader.func_list)

    # Get trading functions.
    trading_funcs = []
    for sig in list(functions.keys())[:-1]:
        name = functions[sig]

        # Check the name.
        if "open" in name or "launch" in name or "start" in name or "enable" in name:
            # Check storage usage.
            if check_storage_usage(loader, sig):
                trading_funcs.append((sig, name))

    # Get blacklist functions.
    blacklist_funcs = []
    for sig in list(functions.keys()):
        name = functions[sig]
        name = name.lower()

        # Check the name.
        if "bot" in name or "black" in name or "ban" in name or "list" in name.lower():
            # Check storage usage.
            if check_storage_usage(loader, sig):
                blacklist_funcs.append((sig, functions[sig]))

    # Print blacklist functions.
    print("")
    print("┳ BLACKLIST FUNCTIONS")
    if len(blacklist_funcs) > 0:
        for functions in blacklist_funcs:
            print(f"┣ {functions[0]}: {functions[1]}")
    else:
        print("┣ No function detected!")

    # Print trading functions.
    print("")
    print("┳ TRADING FUNCTIONS")
    if len(trading_funcs) > 0:
        for functions in trading_funcs:
            print(f"┣ {functions[0]}: {functions[1]}")
    else:
        print("┣ No function detected!")
        return

    # Get chain id and block number.
    block_number = deploy_receipt["blockNumber"] - 1

    print("")
    print("┳ DYNAMIC TESTING")

    # Set the hardhat config.
    set_hardhat_config(block_number + 1)

    # Start the hardhat.
    accounts, node_thread, node_process = start_node()

    # Create new forked provider.
    provider = Web3.HTTPProvider(f"http://127.0.0.1:{environ['DEBUG_HH_PORT']}/")
    forked_w3 = Web3(provider)
    if not forked_w3.isConnected():
        print("┣ Unable to connect to the forked network!")
        return

    # Add balance to the owner.
    provider.make_request(method="hardhat_setBalance", params=[
        deploy_tx["from"],
        Web3.toHex(int(1e20))  # 100 Eth.
    ])

    # Impersonate the owner.
    provider.make_request(method="hardhat_impersonateAccount", params=[
        deploy_tx["from"],
    ])

    # Set code.
    provider.make_request(method="hardhat_setCode", params=[
        token_addr,
        (w3.eth.get_code(token_addr)).hex()
    ])

    # Create forked contract.
    token_abi = read_file("./abi/IERC20.json")
    forked_contract = forked_w3.eth.contract(address=token_addr, abi=token_abi)

    # Create forked uniswap contract.
    uni_abi = read_file("./abi/IUniswapV2Router02.json")
    uni_contract = forked_w3.eth.contract(address=str(environ["UNISWAP_ADDRESS"]), abi=uni_abi)

    # Approve router with all accounts.
    all_accounts = forked_w3.eth.accounts
    all_accounts.append(deploy_tx["from"])
    for account in all_accounts:
        approve_hash = forked_contract.functions.approve(str(environ["UNISWAP_ADDRESS"]),
                                                         int(web3.constants.MAX_INT, 16)) \
            .transact({"from": account})
        forked_w3.eth.wait_for_transaction_receipt(approve_hash)

    # Check owner balance.
    owner_balance = forked_contract.functions.balanceOf(deploy_tx["from"]).call()
    if owner_balance == 0:
        print("┣ No tokens minted to the owner while deploying!")
        return

    amount_ETH_Min = int(1e19)  # 10 ETH as liquidity.
    amount_token_desired = int(owner_balance / 2)  # %50 of the owner balance as liquidity.
    openTrading_value = 0

    # Add liquidity if there are no openTrading or there is no auto liquidity.
    if len(trading_funcs) == 0 or not is_using_add_liquidity_eth(loader, trading_funcs[0][0]):
        # Add liquidity from the router.
        print("┣ Liquidity is added via Uniswap router!")
        liq_hash = uni_contract.functions.addLiquidityETH(
            token_addr,
            amount_token_desired,
            0,
            0,
            deploy_tx["from"],
            int(web3.constants.MAX_INT, 16)
        ).transact({"from": deploy_tx["from"], "value": amount_ETH_Min})
        forked_w3.eth.wait_for_transaction_receipt(liq_hash)

    # Enable trading if there is openTrading function.
    if len(trading_funcs) > 0:
        # Check if dead blocks are dynamic.
        if "," in trading_funcs[0][1]:
            print("┣ Dead blocks might be dynamic!")
            return

        # Check if using addLiquidityETH on openTrading.
        auto_liquidity = is_using_add_liquidity_eth(loader, trading_funcs[0][0])
        if auto_liquidity:
            print("┣ Liquidity is added via openTrading function!")
            # Check if openTrading is payable.
            is_payable = is_func_payable(loader, trading_funcs[0][0])
            if is_payable:
                # If it's payable set msg.value to 10 eth.
                openTrading_value = amount_ETH_Min
            else:
                # If it's not payable set contract balance to 10 eth.
                provider.make_request(method="hardhat_setBalance", params=[
                    token_addr,
                    Web3.toHex(int(1e20))  # 100 Eth.
                ])

            # Send tokens.
            send_hash = forked_contract.functions.transfer(token_addr, amount_token_desired).transact(
                {"from": deploy_tx["from"]})
            forked_w3.eth.wait_for_transaction_receipt(send_hash)

        # Disable auto mining.
        provider.make_request(method="evm_setAutomine", params=[
            False
        ])

        # Enable trading.
        openTrading_hash = forked_w3.eth.send_transaction({
            "to": token_addr,
            "from": deploy_tx["from"],
            "data": bytes(bytearray.fromhex(trading_funcs[0][0][2:])),
            "value": openTrading_value
        })

    # Stop impersonating.
    provider.make_request(method="hardhat_stopImpersonatingAccount", params=[
        deploy_tx["from"],
    ])

    # Get the open trading block number.
    openTrading_number = forked_w3.eth.get_block_number()

    # Enable auto mining.
    provider.make_request(method="evm_setAutomine", params=[
        True
    ])

    # Find dead blocks.
    for account in forked_w3.eth.accounts:
        # Get amounts out. (0.01 ETH)
        amount_in = int(0.01 * 1e18)
        amounts_out = uni_contract.functions.getAmountsOut(amount_in, [environ["WETH_ADDRESS"], token_addr]).call()[1]

        # Try to buy & sell.
        try:
            swap_hash = uni_contract.functions.swapExactETHForTokensSupportingFeeOnTransferTokens(
                0,
                [Web3.toChecksumAddress(environ["WETH_ADDRESS"]), Web3.toChecksumAddress(token_addr)],
                Web3.toChecksumAddress(account),
                int(web3.constants.MAX_INT, 16)
            ).transact({
                "from": account,
                "value": amount_in
            })
            forked_w3.eth.wait_for_transaction_receipt(swap_hash)
        except:
            # Increase the block.
            provider.make_request(method="hardhat_mine", params=[
                "0x1"
            ])
            continue

        # Calculate buy fee.
        balance_buy = forked_contract.functions.balanceOf(account).call()
        fee_percent = int((amounts_out - balance_buy) / amounts_out * 100)

        print("┣ Buy Dead Blocks:", forked_w3.eth.get_block_number() - openTrading_number)
        print(f"┣ Buy Fee Percent: %{fee_percent}", )
        break

    stop_node(node_thread, node_process)
    _exit(0)
    return


if __name__ == '__main__':
    main()

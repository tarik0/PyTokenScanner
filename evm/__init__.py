import trace

from panoramix.loader import Loader
from panoramix.vm import VM


def check_storage_usage(loader: Loader, func_sig) -> dict:
    """ Checks if the function uses storage """
    func_start = loader.func_dests[f"unknown_{func_sig}(?????)"]
    _trace = VM(loader, just_fdests=True).run(func_start)
    return "'store'" in str(_trace)


def is_func_payable(loader: Loader, func_sig) -> bool:
    """ Check if a function is payable. """
    func_start = loader.func_dests[f"unknown_{func_sig}(?????)"]
    return not (
            loader.lines[func_start + 1][1] == "callvalue" and
            loader.lines[func_start + 2][1] == "dup" and
            loader.lines[func_start + 3][1] == "iszero"
    )


def is_using_add_liquidity_eth(loader: Loader, func_sig) -> int:
    """ Finds the functions that uses addLiquidityETH"""
    # 0xf305d719 -> addLiquidityETH
    func_start = loader.func_dests[f"unknown_{func_sig}(?????)"]
    _trace = VM(loader, just_fdests=True).run(func_start)
    return "'call'" in str(_trace)

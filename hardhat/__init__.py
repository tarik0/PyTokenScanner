from os import environ
from subprocess import Popen, PIPE
from threading import Thread

CONFIG_TEMPLATE = """/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: "0.8.9",
  networks: {
  hardhat: {
    forking: {
      url: "RPC_URL",
      blockNumber: BLOCK_NUMBER
    }
   }
 }
};
"""

STOP_NODE = False


def debug_print_pipe(pipe):
    """ Print the pipe in different thread. """
    global STOP_NODE
    while not STOP_NODE:
        if environ["DEBUG_HH_VERBOSE"] != "FALSE":
            print(pipe.readline())


def set_hardhat_config(block_number):
    """ Set the RPC and the block number on the config. """
    config = CONFIG_TEMPLATE.replace("RPC_URL", environ["RPC_ENDPOINT"])
    config = config.replace("BLOCK_NUMBER", str(block_number))

    # Save the config.
    with open("./hardhat/hardhat.config.js", "w+") as f:
        f.write(config)


def start_node():
    """ Start the hardhat node. """
    # Start the process.
    process = Popen(["npx", "hardhat", "node"], cwd="./hardhat/", stdout=PIPE)

    # The auto generated account keys.
    account_keys = []

    # Get the all inputs.
    while len(account_keys) != 20:
        # Get the stout.
        line = process.stdout.readline()

        # Decode the bytes.
        line = str(line, "utf8")

        # Check if it's the account key.
        if line.startswith("Private Key: "):
            account_keys.append(line.split("Key: ")[1].strip())

    # Start debug print lines.
    global STOP_NODE
    STOP_NODE = False
    d_thread = Thread(target=debug_print_pipe, args=(process.stdout,))
    d_thread.start()

    return account_keys, d_thread, process


def stop_node(d_thread, process):
    """ Stop the node. """
    global STOP_NODE
    STOP_NODE = True
    process.terminate()
    d_thread.join()

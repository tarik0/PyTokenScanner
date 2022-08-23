# PyTokenScanner - Token Scanner.
A Python tool to learn the basic trading information about an EVM ERC20 token.

## Features
Here are some of the features in the latest version.

1. Basic Information Gathering. (Name, Symbol etc.)
2. 4Byte Signature Database Support.
3. Blacklist Function Finder.
4. Trading Function Finder.
5. Dynamic Trading Test with Hardhat Support.
6. Buy Dead Block Detector.
7. Buy Fee Detector.

## Installation
You need to have both `Python 3` and `Node v18` for the project to run.

```commandline
sudo apt update && sudo apt upgrade
sudo apt install python3.10

curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install nodejs
```

After that you'll need to install Python requirements.

```commandline
cd PyTokenScanner
pip install -r requirements.txt
```

Then you'll need to install Node JS modules.

```commandline
cd PyTokenScanner/hardhat/
npm install hardhat -g
npm install npx -g
npm install
```

After that the installation is done.

## Configuration
You can configure the required environment variables in the `.env` file.

```commandline
WETH_ADDRESS="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
UNISWAP_ADDRESS="0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
RPC_ENDPOINT="https://eth-mainnet.g.alchemy.com/v2/eZfGimfTzIDjI1fXKlc9nZX6xmsNmzvb"
DEBUG_HH_VERBOSE="FALSE"
DEBUG_HH_PORT="3232"
```

## How To Run
You'll need to find the deployment transaction of the target token you are scanning then give it as a parameter to the scanner.

```commandline
python tokenscanner.py [0xdeploy_tx_hash]
```
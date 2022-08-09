/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: "0.8.9",
  networks: {
  hardhat: {
    forking: {
      url: "https://eth-mainnet.g.alchemy.com/v2/eZfGimfTzIDjI1fXKlc9nZX6xmsNmzvb",
      blockNumber: 15153824
    }
   }
 }
};
import json
from web3 import Web3
from solcx import compile_standard, install_solc
import os
from dotenv import load_dotenv
import yaml
from datetime import datetime


def deployBet(matchId, matchTimestamp):
    load_dotenv()
    # config
    with open("config.yaml", "r") as stream:
        try:
            config = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    chainId = config["chainId"]

    # install the solidity version
    print("Installing...")
    install_solc("0.8.16")

    # Solidity source code
    with open("./contracts/Bet.sol", "r") as file:
        bet_file = file.read()
    
    with open("@chainlink/contracts/abi/v0.4/LinkToken.json", "r") as file:
        linkToken_abi = file.read()

    compiled_sol_bet = compile_standard(
        {
            "language": "Solidity",
            "sources": {"Bet.sol": {"content": bet_file}},
            "settings": {
                "outputSelection": {
                    "*": {
                        "*": ["abi", "metadata", "evm.bytecode", "evm.bytecode.sourceMap"]
                    }
                }
            },
        },
        solc_version="0.8.16",
    )

    with open("compiled_code_bet.json", "w") as file:
        json.dump(compiled_sol_bet, file)

    # get bytecode
    bytecodeBet = compiled_sol_bet["contracts"]["Bet.sol"]["Bet"]["evm"][
        "bytecode"
    ]["object"]


    # get abi
    abiBet = json.loads(
        compiled_sol_bet["contracts"]["Bet.sol"]["Bet"]["metadata"]
    )["output"]["abi"]

    # dev 
    if chainId == 1337 :
        w3 = Web3(Web3.HTTPProvider("http://0.0.0.0:8545"))
        my_address = "0x7E0A8e3647523F0776C8C80D99FCbFFEE92E29A6"
        private_key = "347dc315fd9e3701001c293fcc0d5731adb5c4aedf530c5d4566dab21d16137e"

    # stagging
    elif chainId == 4 : 
        w3 = Web3(Web3.HTTPProvider(os.getenv('RINKEBY_RPC_URL')))
        my_address = os.getenv('PUBLIC_KEY')
        private_key = os.getenv('PRIVATE_KEY')
    elif chainId == 5 : 
        w3 = Web3(Web3.HTTPProvider(os.getenv('GOERLI_RPC_URL')))
        my_address = os.getenv('PUBLIC_KEY')
        private_key = os.getenv('PRIVATE_KEY')

    # Deploying Bet.sol
    Bet = w3.eth.contract(abi=abiBet, bytecode=bytecodeBet)
    nonce = w3.eth.getTransactionCount(my_address)

    jobId = config[chainId]["jobId"]
    oracle = config[chainId]["oracle"]
    fee = config[chainId]["fee"]
    linkTokenAddress = config[chainId]["linkToken"]

    transaction = Bet.constructor(str(matchId), int(matchTimestamp), Web3.toChecksumAddress(oracle), jobId, int(fee), Web3.toChecksumAddress(linkTokenAddress)).buildTransaction(
        {
            "chainId": chainId,
            "gasPrice": w3.eth.gas_price,
            "from": my_address,
            "nonce": nonce,
        }
    )
    signed_txn = w3.eth.account.sign_transaction(transaction, private_key=private_key)
    print("Deploying Contract!")
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    print("Waiting for transaction to finish...")
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    betAdrr = tx_receipt.contractAddress
    print(f"Done! Contract deployed to {tx_receipt.contractAddress}")
    print(f"Etherscan link : https://{config[chainId]['name']}.etherscan.io/address/{tx_receipt.contractAddress}#code")

    
    # fund link
    link_token = w3.eth.contract(address=Web3.toChecksumAddress(config[chainId]["linkToken"]),abi=linkToken_abi)
    nonce = w3.eth.getTransactionCount(my_address)
    tx = link_token.functions.transfer(tx_receipt.contractAddress, 100000000000000000).buildTransaction(
        {
            "chainId": chainId,
            "gasPrice": w3.eth.gas_price,
            "from": my_address,
            "nonce": nonce,
        }) # 0.1 LINK

    # tx_receipt = w3.eth.wait_for_transaction_receipt(tx)

    print("LINK funded contract!")
    token_balance = link_token.functions.balanceOf(tx_receipt.contractAddress).call() # returns int with balance, without decimals
    print("LINK funded : ", token_balance)

    # verify contract on etherscan

    return str(betAdrr)

if __name__ == "__main__":
    matchId = 300
    matchTimestamp = int(datetime.timestamp(datetime.now())) + 60*60 # 1 hour after the deployment
    addr = deployBet(matchId, matchTimestamp)
    print(type(addr))
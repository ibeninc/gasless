from eth_account import Account
from eth_account.messages import encode_structured_data, encode_defunct, encode_typed_data
from web3 import Web3, HTTPProvider
from web3.middleware import geth_poa_middleware
import time


# Configuration
web3 = Web3(HTTPProvider('https://rpc-mumbai.maticvigil.com'))
web3.middleware_onion.inject(geth_poa_middleware, layer=0)


# contract address
contract_address = web3.to_checksum_address('<contract address>')
# contract ABI
abi = []

# Add desired time to represent the deadline, e.g., 1 hour from now
deadline_timestamp = int(time.time()) + (20 * 60)  # Current UNIX time + 20 minutes in seconds


token_contract = web3.eth.contract(address=contract_address, abi=abi)
private_key_sender = <sender key>
sender_address = <sender wallet address>
receiver_address = <reciever wallet address>
amount = web3.to_wei(1, 'ether')  # Amount to send
fee = web3.to_wei(0.01, 'ether')  # Fee to pay the relayer
nonce = token_contract.functions.nonces(sender_address).call()  # Get current nonce for the sender
deadline = deadline_timestamp  # Deadline for the transaction to be mined; ensure this is in seconds and is a future time
private_key_relayer = <relayer private key>  # Private key of the relayer
relayer_address = <relayer wallet address>

# Prepare the structured data for signing
message = {
"types":{
    "EIP712Domain": [
        {"name": "name", "type": "string"},
		{"name": "version", "type": "string"},
		{"name": "chainId", "type": "uint256"},
		{"name": "verifyingContract", "type": "address"}
    ],
    "Permit": [
        {"name": "recipient", "type": "address"},
        {"name": "amount", "type": "uint256"},
        {"name": "fee", "type": "uint256"}
    ],
},
"primaryType": "Permit",
"domain" : {
    "name": "GaslessPay-DAI",
    "version": "1",
    "chainId": 80001,
    "verifyingContract": <smart contract address>,
},
"message" :{
    "sender": sender_address,
    "recipient": receiver_address,
    "amount": amount,
    "fee": fee,
    "nonce": nonce,
    "deadline": deadline,
}
}

# Signing the message
encoded_message = encode_structured_data(message)
signed_message = web3.eth.account.sign_message(encoded_message, private_key=private_key_sender)
# print(signed_message)
v= signed_message.v

r_bytes32 = signed_message.r.to_bytes(32, byteorder='big')
s_bytes32 = signed_message.s.to_bytes(32, byteorder='big')

r = '0x' + r_bytes32.hex()
s = '0x' + s_bytes32.hex()
# Execute the transferGasless function
tx = token_contract.functions.transferGasless(
	sender_address,
    receiver_address,
    amount,
    fee,
    deadline,
    v,
    r,
    s,
).build_transaction({
    'from': relayer_address,
    'nonce': web3.eth.get_transaction_count(relayer_address),
    'gas': 2000000,
    'gasPrice': web3.to_wei('5', 'gwei'),
})

# Sign and send the transaction
signed_tx = web3.eth.account.sign_transaction(tx, private_key_relayer)
tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)  # Ensure correct attribute use for rawTransaction

print(f"Transaction hash: {tx_hash.hex()}")
print(f"Transaction hash: {tx_hash.hex()}")


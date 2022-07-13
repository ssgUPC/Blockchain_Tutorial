#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb  2 11:40:42 2022

@author: souviksengupta
"""

import datetime
import hashlib
import json
from flask import Flask, jsonify, request
import requests
from uuid import uuid4
from urllib.parse import urlparse


# Part 1 - building Blockchain
class Blockchain:

    # initialize the blockchain
    def __init__(self):
        self.chain = []
        self.transactions = [] # always add transactions before initialize the genesis block
        self.create_block(proof=1, prev_hash='0')  # creation of genesis block
        self.nodes = set() #set of decentralize node for adding

    # function for creation of the new block
    def create_block(self, proof, prev_hash):

        block = {'index': len(self.chain) + 1,
                 'timestamp': str(datetime.datetime.now()),
                 'proof': proof,
                 'prev_hash': prev_hash,
                 'transactions': self.transactions}
        
        self.transactions = []
        self.chain.append(block)
        return block

    # get the last block
    def get_previous_block(self):
        return self.chain[-1]

    def proof_of_work(self, prev_proof):
        new_proof = 1
        check_proof = False
        while check_proof is False:
            hash_operation = hashlib.sha256(str(new_proof ** 2 - prev_proof ** 2).encode()).hexdigest()
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1
        return new_proof

    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()

    def is_chain_valid(self, chain):
        prev_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block['prev_hash'] != self.hash(prev_block):
                return False
            prev_proof = prev_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof ** 2 - prev_proof ** 2).encode()).hexdigest()
            if hash_operation[:4] != '0000':
                return False
            prev_block = block
            block_index += 1

        return True
    
    def add_transaction(self, sender, receiver, amount):
        self.transactions.append({'sender': sender, 'receiver' : receiver, 'amount' : amount})
        previous_block = self.get_previous_block()
        return previous_block['index'] + 1
    
    def add_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)
        
    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        for node in network:
            response = requests.get(f'http://{node}/get_chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        
        if longest_chain:
            self.chain = longest_chain
            return True
        return False
        

# Part 2 - Mining our Blockchain
app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False # might be remove, check it

# Creating an address for the node on port 8000
node_address =  str(uuid4()).replace('-','')

# creating a blockchain
blockchain = Blockchain()


# mining a new block
@app.route('/mine_block', methods=['GET'])
def mine_block():
    prev_block = blockchain.get_previous_block()
    prev_proof = prev_block['proof']
    proof = blockchain.proof_of_work(prev_proof)
    prev_hash = blockchain.hash(prev_block)
    blockchain.add_transaction(sender = node_address, receiver = 'Souvik', amount = 10)
    block = blockchain.create_block(proof, prev_hash)
    response = {'meesage': 'Congrats!, you just mined a block!',
                'index': block['index'],
                'timestamp': block['timestamp'],
                'proof': block['proof'],
                'prev_hash': block['prev_hash'],
                'transactions': block['transactions']}
    return jsonify(response), 200


@app.route('/get_chain', methods=['GET'])
def get_chain():
    response = {'chain': blockchain.chain,
                'length': len(blockchain.chain)}
    return jsonify(response), 200


@app.route('/is_valid', methods=['GET'])
def is_valid():
    is_valid = blockchain.is_chain_valid(blockchain.chain)
    if is_valid:
        response = {'message': 'All is good and the blockchain is valid'}
    else:
        response = {'message': 'Folks! something went wrong it is not valid'}
    return jsonify(response), 200

#adding new transaction in the Blockchain
@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    json = request.get_json()
    transaction_keys = ['sender', 'receiver', 'amount']
    if not all (key in json for key in transaction_keys):
        return 'Some key imnformations are missing for transactions!!', 400
    index = blockchain.add_transaction(json['Sender'], json['receiver'], json['amount'])
    response = {'message': f'This transaction will be added to Block {index}'}
    return jsonify(response), 201
        



# Part 3 - Decentralizing our Blockchain

#connecting new nodes
@app.route('/connect_node', methods=['POST'])
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes')
    if nodes is None:
        return "No Node is available", 400
    for node in nodes:
        blockchain.add_node(node)
    response = {'message': 'All the nodes are connected. The Blockchain now contains the following nodes',
                'total_nodes': list(blockchain.nodes)}
    return jsonify(response), 201

# Replacing the chain by the longest chain if needed to be up-to-date
@app.route('/replace_chain', methods=['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced:
        response = {'message': 'The chain was replaced by the longest one and the nodes had different one', 
                    'new_chain': blockchain.chain}
    else:
        response = {'message': 'Folks! all good. The chain is the largest one.',
                    'actual_chain': blockchain.chain}
    return jsonify(response), 200


# Running app
app.run(host='0.0.0.0', port=8000)





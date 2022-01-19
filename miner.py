#! /usr/bin/env python3 ############################################################
##               ,:                                                         ,:    ##
##             ,' |                                                       ,' |    ##
##            /   :                                                      /   :    ##
##         --'   /       :::::::::::   :::::::::::   :::    :::       --'   /     ##
##         \/ />/           :+:            :+:       :+:   :+:        \/ />/      ##
##         / /_\           +:+            +:+       +:+  +:+          / /_\       ##
##      __/   /           +#+            +#+       +#++:++         __/   /        ##
##      )'-. /           +#+            +#+       +#+  +#+         )'-. /         ##
##      ./  :\          #+#        #+# #+#       #+#   #+#         ./  :\         ##
##       /.' '         ###         #####        ###    ###          /.' '         ##
##     '/'                                                        '/'             ##
##     +                                                          +               ##
##    '                                                          '                ##
####################################################################################
##            Copyright © 2022 Tyler J. Kenney. All rights reserved.              ##
####################################################################################
####################################################################################

import sys
import uuid
import flask
import requests
import argparse

from urllib.parse import urlparse
from blockchain import Blockchain

class HTTP:
    OK = 200
    Created = 201
    BadRequest = 400
    NotFound = 404
# End HTTP

class Miner:
    '''
    Miner:
        ID           <str>: Miner's address used in TKC transactions
        chain <Blockchain>: Miner's local copy of the blockchain
        peers        <set>: Set of other active Miners
    '''

    def __init__(self):
        self.peers = set()
        self.ID = str(uuid.uuid4()).replace('-','')
        self.chain = Blockchain.init()

    def new_transaction(self, sender, receiver, amt):
        ## TODO: Should we save pending transactions here, in Miner, instead of
        ##  forwarding them to Blockchain?
        ##
        ##  In this implementation, there's no synchronization of transactions.
        ##  You have to have a specific node address in order to send a
        ##  transaction, and only that node is going to hear about it. During
        ##  consensus, any transactions recorded by nodes without the longest
        ##  chain are lost, which seems like a problem. How are transactions
        ##  recorded and synchronized in real bitcoin?
        ##
        return self.chain.new_transaction(sender,receiver,amt)

    def register_node(self, addr):
        '''
        Register the given address as a peer node.
        Params:
          addr <str>: Address to register (example: http://localhost:123)
        '''
        url = urlparse(addr)
        self.peers.add(url.netloc)

    @staticmethod
    def proof_of_work(last_proof):
        '''
        Search for valid proof given the last proof.

        The current implementation is a brute-force search. Can we
        invert the wegman hash to improve performance here? Are
        bitcoin miners distinguished by cleverness in this search
        algorithm, or merely in the speed at which they can brute-
        force?

        Is zero the best place to start here? Would it be faster if
        we started from the last_proof (and looped back around if
        necessary)?
        '''
        proof = 0
        while not Blockchain.valid_proof(last_proof,proof):
            proof += 1
            if proof % 100000 == 0:
                print(f'guess = {proof}...\r',end='',flush=True)
        return proof

    def mine_block(self):
        '''
        Find proof-of-work and mint new block.
        Returns the successful proof-of-work.
        '''
        new_proof = self.proof_of_work(self.chain.last_block.proof)
        self.new_transaction(self.chain.MINE_ADDR,self.ID,1)
        next_block = self.chain.mine_block(new_proof)
        return new_proof

    def resolve_conflicts(self):
        ''' Sync chains across active nodes '''
        ##
        ## Consensus algorithm: Take the longest valid chain
        ##
        ##  This is currently user-driven; synchronizations only occur when the
        ##  user requests them. Furthermore, this consensus algorithm is going
        ##  to drop transactions that were recorded onto any chains other than
        ##  the longest one. How is this prevented in real bitcoin?
        ##

        changed = False

        print(f'resolve_conflicts(): len(self) = {self.chain.num_blocks}')

        for i,node in enumerate(self.peers):
            # Request full chain from peer node
            response = requests.get(f'http://{node}/chain')

            if response.status_code != HTTP.OK:
                continue # Node failure - ignore corresponding chain

            # Convert from vanilla list to Blockchain
            alt_chain = Blockchain.from_list(response.json()['chain'])

            print(f'resolve_conflicts(): Checking chain #{i} [len={alt_chain.num_blocks()}]')

            # Check for dominant chain
            if len(alt_chain) > len(self.chain) and alt_chain.valid():
                changed = True
                self.chain = alt_chain

        return changed

##
## Globals
##

miner = Miner()
app = flask.Flask('TKBC')

@app.route('/register', methods=['POST'])
def register_node():
    req = flask.request.get_json()

    try:
        node = req['addr']
    except KeyError as e:
        return "Failed to decode node address", HTTP.BadRequest

    miner.register_node(node)
    ack = {
        'message' : f'Node successfully registered.'
    }

    return flask.jsonify(ack), HTTP.Created

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    req = flask.request.get_json()

    try:
        idx = miner.new_transaction(req['sender'],req['receiver'],req['amount'])
    except KeyError as e:
        return "Missing sender/receiver/amount", HTTP.BadRequest

    ack = {
        'message' : f'Transaction will be added to block {idx}'
    }

    return flask.jsonify(ack), HTTP.Created

@app.route('/chain', methods=['GET'])
def full_chain():
    ack = {
        'chain' : miner.chain
    }
    return flask.jsonify(ack), HTTP.OK

@app.route('/mine', methods=['GET'])
def mine():
    next_proof = miner.mine_block()
    ack = {
        'message' : 'New Block Forged',
        'proof' : next_proof
    }

    return flask.jsonify(ack), HTTP.OK

@app.route('/resolve', methods=['GET'])
def resolve():
    replaced = miner.resolve_conflicts()

    msg = 'Chain Replaced' if replaced else 'Chain Retained'

    ack = {
        'message' : msg,
        'chain' : chain.chain
    }

    return flask.jsonify(ack), HTTP.OK

def main():

    ##
    ## Parse Args
    ##

    parser = argparse.ArgumentParser(description='Initiate miner node for TK-Chain')
    parser.add_argument('--port','-p',type=int,metavar='<portnum>',required=True,
                        help='Port number through which the server can be contacted')

    args = parser.parse_args()

    ##
    ## Warmup
    ##
    ##  This is just for fun. It gives our server processes a bit of spin-up
    ##  time and verifies that we have some basic functionality before
    ##  launching the actual server.
    ##

    next_proof=77
    num_proofs = 0
    while (num_proofs < 1):
        next_proof = Miner.proof_of_work(next_proof)
        print(f"Found next proof: {next_proof}")
        num_proofs += 1

    ##
    ## Start the Flask server
    ##

    print('Starting server...')
    app.run(host='0.0.0.0',port=args.port)
    return


if __name__ == "__main__": sys.exit(main())

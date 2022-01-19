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

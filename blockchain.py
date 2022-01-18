####################################################################################
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
import time
import copy
import requests

from urllib.parse import urlparse

def wegman_hash(x):
    ''' Return the wegman-hash of integer x '''
    assert type(x) == int, "Unexpected input type"

    # Split into lo & hi
    lo = (x >> 00) & 0xFFFFFFFF
    hi = (x >> 32) & 0xFFFFFFFF

    # Add random numbers [32-bit modulo add]
    lo = (lo + 0xACEFADE5) & 0xFFFFFFFF
    hi = (hi + 0xBADBABE5) & 0xFFFFFFFF

    # Multiply
    product = lo * hi

    # Shift & Add
    product_masked  = (product >> 00) & 0xFFFFFFFF
    product_shifted = (product >> 31) & 0xFFFFFFFF
    return product_masked + product_shifted

class Transaction(dict):
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

    def __init__(self, sender='', receiver='', amt=0):
        self['sender'] = sender
        self['receiver'] = receiver
        self['amount'] = amt

    @staticmethod
    def from_dict(d):
        assert isinstance(d,dict), "Transaction: passing non-dict to from_dict()?"
        # TODO: Can we return copy.deepcopy(d) here? If so, can we eliminate the copy?
        return Transaction(d['sender'],d['receiver'],d['amount'])

    def __hash__(self):
        values = [val for key,val in self.items()]
        return hash(tuple(values))

class Block(dict):
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

    def __init__(self, transactions=[], proof=0, prev_hash=0, timestamp=time.time()):
        self['transactions'] = tuple(transactions)
        self['proof'] = proof
        self['prev_hash'] = prev_hash
        self['timestamp'] = timestamp

    @staticmethod
    def from_dict(d):
        assert isinstance(d,dict), "Block: passing non-dict to from_dict()?"
        b = Block()
        for key,val in d.items():
            assert key in b.keys(), f"Block::UnexpectedParameter: {key}"
            if key == 'transactions':
                assert isinstance(val,list), "Block: Transactions isn't a list?"
                b[key] = tuple([Transaction.from_dict(x) for x in val])
            else:
                b[key] = val
        #self = copy.deepcopy(d)
        return b

    def __hash__(self):
        values = [val for key,val in self.items()]
        return hash(tuple(values))

class Blockchain:

    def __init__(self, _chain=[]):
        self.active_nodes = set()
        self.current_transactions = []

        if _chain:
            self.chain = _chain
        else:
            self.chain = []
            self.create_block(proof=77) # Genesis block
        return

    @staticmethod
    def from_json(json_chain):
        chain = []
        for json_block in json_chain:
            b = Block.from_dict(json_block)
            chain.append(b)
        return Blockchain(chain)

    @staticmethod
    def valid_proof(proofA, proofB):
        ''' Return true if proofB is a valid proof given prior proof \p proofA '''
        guess = ((proofA & 0xFFFFFFFF) << 16) + proofB
        hashval = wegman_hash(guess)
        return hashval % 10000000 == 777777

    @staticmethod
    def valid_chain(chain):
        if len(chain) == 1:
            return True

        for i in range(1,len(chain)):
            print(f'i = {i}')
            block = chain[i]
            last_block = chain[i-1]
            print(block)

            if block.prev_hash != hash(last_block):
                return False
            if not Blockchain.valid_proof(last_block.proof,block.proof):
                return False

        return True

    def create_block(self, proof):
        '''
        Add new block to the chain.

        Params:
          - proof: proof of work (int)

        Returns:
          - New block
        '''

        # Validate proof
        if self.num_blocks == 0:
            pass # Genesis block
        else:
            if not self.valid_proof(self.last_block.proof,proof):
                raise ValueError('Invalid proof')

        # Get previous hash
        if self.num_blocks == 0:
            prev_hash = 0 # Genesis block
        else:
            prev_hash = hash(self.last_block)

        # Create block
        block = Block(self.current_transactions,proof,prev_hash,time.time())

        self.chain.append(block)
        self.current_transactions = []
        return block

    def new_transaction(self, sender, receiver, amt):
        '''
        Create a new transaction to go into the next block.

        Params:

          - sender:   address (string)
          - receiver: address (string)
          - amt:  int

        Returns:

          - int: index of parent block
        '''

        self.current_transactions.append(Transaction(sender,receiver,amt))
        return self.num_blocks

    def register_node(self, addr):
        ''' Add \p addr to set of active nodes '''
        url = urlparse(addr)
        self.active_nodes.add(url.netloc)

    def resolve_conflicts(self):
        ''' Sync chains across active nodes '''
        ## Consensus algorithm: Take the longest valid chain
        changed = False

        print(f'resolve_conflicts(): len(self.chain) = {len(self.chain)}')

        for i,node in enumerate(self.active_nodes):
            response = requests.get(f'http://{node}/chain')

            if response.status_code != 200: # HTTP::OK
                continue # Node failure - ignore corresponding chain

            node_chain = Blockchain.from_json(response.json()['chain']).chain

            print(f'resolve_conflicts(): Checking chain #{i} [len={len(node_chain)}]')


            # FIXME: Need to re-create Transaction & Block
            # objects that were lost during jsonification

            #print('blockchain.py')
            #print(node_chain)
            #print('\n\n\n\n\n')

            if len(node_chain) > len(self.chain) and self.valid_chain(node_chain):
                changed = True
                self.chain = node_chain

        return changed

    @property
    def MINE_ADDR(self):
        ''' Node address reserved for successful mine '''
        return '0'

    @property
    def last_block(self):
        return self.chain[-1]

    @property
    def num_blocks(self):
        return len(self.chain)

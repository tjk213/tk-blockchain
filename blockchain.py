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

from collections import namedtuple

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

Transaction = namedtuple('Transaction','sender receiver amount')
Block = namedtuple('Block','transactions proof prev_hash timestamp')

class Blockchain:

    def __init__(self):
        self.chain = []
        self.current_transactions = []

        self.create_block(proof=77) # Genesis block
        return

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

    @staticmethod
    def valid_proof(proofA, proofB):
        ''' Return true if proofB is a valid proof given prior proof \p proofA '''
        guess = ((proofA & 0xFFFFFFFF) << 16) + proofB
        hashval = wegman_hash(guess)
        return hashval % 10000000 == 777777

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

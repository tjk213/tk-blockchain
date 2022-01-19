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

##
## TK-Blockchain featuring the WegmanHash
##
## This file contains an implementation of a simple blockchain using the WegmanHash
## as the difficult-to-reverse function in the proof-of-work algorithm. It is not
## at all cryptographically secure, but that's ok because this is only intended for
## educational purposes.
##
## Heavily inspired by Daniel van Flymen's 'Learn Blockchains by Building One'
## guide on HackerNoon:
##
##    https://hackernoon.com/learn-blockchains-by-building-one-117428612f46
##

import sys
import time

def wegman_hash(x):
    '''
    Return the wegman-hash of integer x

    Note: Only the bottom 28 bits of the return value should be relied upon as
          sufficiently random by the caller. We could explicitly zero the
          upper bits here to make this more clear, but most callers will be
          reducing this to a much smaller range so we don't bother with a
          redundant mask.
    '''
    assert type(x) == int, "wegman_hash(): Unexpected input type"
    assert 0 <= x <= 2**64-1, "wegman_hash(): input out-of-range"

    # Split into lo & hi
    lo = (x >> 00) & 0xFFFFFFFF
    hi = (x >> 32) & 0xFFFFFFFF

    # Add random numbers [32-bit modulo add]
    lo = (lo + 0xACEFADE5) & 0xFFFFFFFF
    hi = (hi + 0xBADBABE5) & 0xFFFFFFFF

    # Multiply
    product = lo * hi

    # Shift
    product_masked  = (product >> 00) & 0xFFFFFFFF
    product_shifted = (product >> 31) & 0xFFFFFFFF

    ##
    ## Add
    ##
    ## Note: this isn't restricted to 32-bits in python land, like our original
    ##  C implementation is. The overflow bit should definitely not be
    ##  relied upon as sufficiently random by callers, but that's true for the
    ##  uppermost bits beneath the overflow bit, too. See function notes.
    ##

    return product_masked + product_shifted

class Transaction(dict):
    '''
    Transaction:
        sender   <str>: Address of sender
        receiver <str>: Address of receiver
        amount   <int>: Amount of TKC to transfer

    Implementation Notes:
        - We inherit from dict for automatic conversion to/from JSON

           We could create a similar class with a one-liner using collections.namedtuple,
           but this implementation gives us a from_dict() factory method that we'll use to
           recreate objects after storing & reloading from JSON.
    '''

    # Overide attribute accessors so instance variables can be accessed like
    # class members (t.sender) rather than dictionary keys (t['sender'])
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

    def __init__(self, sender='', receiver='', amt=0):
        super().__init__()
        self['sender'] = sender
        self['receiver'] = receiver
        self['amount'] = amt

    @staticmethod
    def verify(d):
        ''' Verify that dictionary d represents a valid Transaction object '''
        assert isinstance(d,dict), "Transaction: <dict> object expected for verification"

        # Verify no missing keys
        for key in Transaction.keys():
            if key not in d.keys():
                raise ValueError(f'Transaction::MissingKey: {key}')

        # Verify no extra keys
        for key in d.keys():
            if key not in Transaction.keys():
                raise ValueError(f'Transaction::UnexpectedKey: {key}')

        # Verify types
        if not isinstance(d['sender'],str) or \
           not isinstance(d['receiver'],str):
            raise ValueError(f'Transaction::UnexpectedType: Addresses should be strings')
        if not isinstance(d['amount'],int):
            raise ValueError(f'Transaction::UnexpectedType: Amount should be an integer')
        return True

    @staticmethod
    def from_dict(d):
        ''' Construct Transaction from dictionary '''
        assert isinstance(d,dict), "Transaction: passing non-dict to from_dict()?"
        assert Transaction.verify(d), "Transaction: Verification failed"
        # TODO: Can we return copy.deepcopy(d) here? If so, can we eliminate the copy?
        return Transaction(d['sender'],d['receiver'],d['amount'])

    def __hash__(self):
        ''' Pack transaction properties into a tuple and return its hash '''
        assert Transaction.verify(self), "Transaction: Verification failed"
        values = [val for key,val in self.items()]
        return hash(tuple(values))

class Block(dict):
    '''
    Block:
        transactions <list>: Transactions recorded in this block
        proof         <int>: Proof-of-work for this block
        prev_hash     <int>: Hash of previous block in the chain
        timestamp     <int>: Timestamp of this block's creation date
    '''

    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

    def __init__(self, transactions=[], proof=0, prev_hash=0, timestamp=time.time()):
        super().__init__()
        self['transactions'] = tuple(transactions) # Convert to tuple - blocks are immutable
        self['proof'] = proof
        self['prev_hash'] = prev_hash
        self['timestamp'] = timestamp

    @staticmethod
    def verify(d):
        ''' Verify that dictionary d represents a valid Block object '''
        assert isinstance(d,dict), "Block: <dict> object expected for verification"

        # Verify no missing keys
        for key in Block.keys():
            if key not in d.keys():
                raise ValueError(f'Block::MissingKey: {key}')

        # Verify no extra keys
        for key in d.keys():
            if key not in Block.keys():
                raise ValueError(f'Block::UnexpectedKey: {key}')

        # Verify types
        if not isinstance(d['transactions'],list) and \
           not isinstance(d['transactions'],tuple):
            raise ValueError(f'Block::UnexpectedType: Transactions should be sequential container')

        if not isinstance(d['proof'],int):
            raise ValueError(f'Block::UnexpectedType: proof-of-work should be an integer')

        if not isinstance(d['prev_hash'],int):
            raise ValueError(f'Block::UnexpectedType: hash-link should be an integer')

        if not isinstance(d['timestamp'],int):
            raise ValueError(f'Block::UnexpectedType: timestamp should be an integer')

        return True

    @staticmethod
    def from_dict(d):
        assert isinstance(d,dict), "Block: passing non-dict to from_dict()?"
        assert Block.verify(d), "Block: Verification failed"

        ## d['transactions'] could point to any of the following here:
        ##
        ##    -container type: list or tuple
        ##    -elemental type: dict or Transaction
        ##
        ## The Block constructor converts to tuple type, so we don't really
        ## care what the given container type is.
        ##
        ## If the element type is Transaction, then this is wastefully re-
        ## constructing all of our objects, but it won't do any true harm.
        ## If the element type is raw dictionaries, then this converts to
        ## the Transaction type that our blockchain will be expecting.
        ##
        ## Typically, from_dict() is called with data loaded from a json,
        ## so we primarily expect a list of raw dictionaries here.
        transactions = [Transaction.from_dict(x) for x in d['transactions']]
        return Block(transactions,d['proof'],d['prev_hash'],d['timestamp'])

    def __hash__(self):
        ''' Pack Block parameters into a tuple and return its hash '''
        assert Block.verify(self), "Block: Verification failed"
        values = [val for key,val in self.items()]
        return hash(tuple(values))

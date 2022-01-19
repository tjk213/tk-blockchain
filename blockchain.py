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
        for key in Transaction().keys():
            if key not in d.keys():
                raise ValueError(f'Transaction::MissingKey: {key}')

        # Verify no extra keys
        for key in d.keys():
            if key not in Transaction().keys():
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
        for key in Block().keys():
            if key not in d.keys():
                raise ValueError(f'Block::MissingKey: {key}')

        # Verify no extra keys
        for key in d.keys():
            if key not in Block().keys():
                raise ValueError(f'Block::UnexpectedKey: {key}')

        # Verify types
        if not isinstance(d['transactions'],list) and \
           not isinstance(d['transactions'],tuple):
            raise ValueError(f'Block::UnexpectedType: Transactions should be sequential container')

        if not isinstance(d['proof'],int):
            raise ValueError(f'Block::UnexpectedType: proof-of-work should be an integer')

        if not isinstance(d['prev_hash'],int):
            raise ValueError(f'Block::UnexpectedType: hash-link should be an integer')

        if not isinstance(d['timestamp'],float):
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

class Blockchain(list):
    '''
    Blockchain:
        self <list>: List of Blocks representing this chain
        current_transactions <list>: List of pending transactions for next block
    '''

    def __init__(self):
        '''
        *** PRIVATE: Clients should use factory methods ***
        Construct an empty Blockchain.
        '''
        super().__init__()
        self.current_transactions = []

    @staticmethod
    def init(seed=77):
        '''
        Initialize a new Blockchain.

        Params:
          seed <int>: Values used for genesis-block proof
        Returns:
          chain <Blockchain>: Newly created chain
        '''

        chain = Blockchain()
        chain.append(Block(proof=seed,prev_hash=0))
        return chain

    @staticmethod
    def from_list(L):
        ''' Construct a Blockchain from a vanilla list '''
        chain = Blockchain()

        ##
        ## Convert list elements to Blocks
        ##
        ##   Typically, this factory is used for reading data in from a json,
        ##   which means our element types are going to be raw dictionaries.
        ##   Therefore, we use Block's factory method to convert these into
        ##   Block objects. If we're given actual Block objects already, then
        ##   this is wasteful but it will still work. No need to optimize this
        ##   case at this point since it's wholly unexpected.
        ##
        for b in L:
            chain.append(Block.from_dict(b))
        return chain

    @staticmethod
    def valid_proof(proofA, proofB):
        ''' Return true if <proofB> is a valid proof-of-work given prior proof <proofA> '''

        ##
        ## Merge proofA & proofB together into a hashable value
        ##
        ## Cycles
        ## ------
        ## Note that any potential cycle formed by this algorithm sets a fundamental limit.
        ## If the sequence of proofs generated by this algorithm and the given seed proof
        ## (set, in our case, on the genesis block) has a repeating pattern, then we must
        ## presume that someone will notice it, and they will therefore be able to
        ## perform proof-of-work at zero cost.
        ##
        ## If an implementation does have cycles, the length of it could potentially be
        ## analytically calculated. At that point, the safe thing to do would presumably
        ## be to encode a max-chain length, and have the system shut down when it's
        ## reached. Does bitcoin have a proof-link like this? Is it somehow guaranteed to
        ## avoid cycles? Assuming finite data types for proofs, it seems that the cycle
        ## length must be limited? Perhaps they have a guaranteed lower bound, and it's
        ## something sufficiently massive that no one worries about it?
        ##
        ## The implementation here, for instance, can't possibly have a cycle count
        ## longer than ~4 billion blocks (2**32, to be exact) because I'm only using 32
        ## bits of the prior proof in the proof link. Presumably, we hit a repeat way
        ## faster than that for most if not all seed values.
        ##
        ## Note that this limit could clearly be improved by increasing the size of the
        ## bitmask on proofA, or eliminating it altogether. But then we'd have a limit
        ## set by the wegman_hash implementation, which expects nothing greater than a
        ## 64-bit key. I want the cycle limit to be explicit here, so I deliberately
        ## force the bitmask. Four billion blocks should be enough for our purposes.
        ##
        ## The above number-of-possible-proofA-values only gives a loose upper bound on
        ## the max cycle length. To prove that it could be *much* shorter, consider my
        ## initial implementation here:
        ##
        ##    guess = proofA + proofB
        ##
        ## This was a very bad choice. Since this is a commutative op, the cycle length
        ## was just 2. It didn't matter how complicated the hash applied to <guess>
        ## was. The first proof-of-work was solving the equation guess = seed + x
        ## for a value of x that gave us a certain magic value for <guess>. The second
        ## proof-of-work was solving guess = x + y. It is trivial to see that y=seed
        ## gives you the same value for <guess>, which is known to be a good one
        ## (although not necessarily the only good one).
        ##
        ## This is presumably why the HackerNoon guide uses a pure concat(proofA,proofB)
        ## operation. The left-shift in the implementation here creates a similar
        ## effect, although the shift-amount isn't quite high enough to make it a pure
        ## bitwise concatenation.
        ##
        ## I have no idea what the actual cycle length of the current implementation
        ## is, for any given seed value.
        ##
        ##
        ## Termination
        ## -----------
        ## Another potential problem with this sequence is that it could terminate. For
        ## any given proofA, is there guaranteed to exist a proofB? In practice, I
        ## expect cycles to be a much more relevant issue, but I don't know if I can
        ## prove that this doesn't terminate. If it's a good hash function, the lower
        ## bits should be sufficiently random and so we should be guaranteed to get the
        ## magic pattern eventually. But a hash function that accidentally set the LSB
        ## to zero or some strange interaction between the merge() and hash() functions
        ## could potentially produce this problem.
        ##

        guess = ((proofA & 0xFFFFFFFF) << 16) + proofB
        hashval = wegman_hash(guess)
        return hashval % 10000000 == 777777 # modulo 10,000 --> reading bottom ~14 bits of hashval

    def valid(self):
        ''' Return True if this instance represents a valid chain '''

        # Empty chains are invalid
        if self.num_blocks == 0:
            return False

        # All single-block chains are valid
        if self.num_blocks == 1:
            return True

        ##
        ## Validate chain
        ##
        ##  Each link in the chain is two-fold:
        ##    - full hash of prior block is stored in current block
        ##    - proof-of-work is a function of prior proof-of-work
        ##
        ##  Why do we need this double-link?
        ##
        ##    Well, proof-of-work links are clearly not sufficient by themselves because
        ##    they *only* link the proofs, so anyone could read a block, save it's proof,
        ##    update the transactions and the subsequent chain would still pass
        ##    validation.
        ##
        ##    The hash-links solve this problem, but then why do we need the
        ##    proof-of-work link? Well, I think I'm still a bit fuzzy on this but the
        ##    proof everyone's competing to find must be a function of some part of the
        ##    current head, otherwise there'd be no consensus on the problem everyone's
        ##    trying to solve, or you wouldn't have a chain, or both.
        ##
        ##    If valid_proof() was a function of all the transactions in the previous
        ##    block, as well as it's proof, could you then elminate the hash-link? Yes,
        ##    I think you could. This would effectively merge the hash-link within the
        ##    proof-of-work link.
        ##
        for i in range(1,self.num_blocks):
            block = self[i]
            last_block = self[i-1]
            if block.prev_hash != hash(last_block) or \
               not Blockchain.valid_proof(last_block.proof,block.proof):
                return False

        return True

    def mine_block(self, proof):
        '''
        Create new block and add it to the chain.

        Params:
          proof <int>: proof-of-work

        Returns:
          NewBlock <Block>: Generated block
        '''
        # Validate genesis block
        if self.num_blocks == 0:
            raise ValueError('Missing genesis block?')

        # Validate proof
        if not self.valid_proof(self.last_block.proof,proof):
            raise ValueError('Invalid proof-of-work')

        # Create block
        block = Block(self.current_transactions,proof,hash(self.last_block))

        self.append(block)              # Add block to the chain
        self.current_transactions = []  # Reset pending transactions
        return block                    # Return new block

    def new_transaction(self, sender, receiver, amt):
        '''
        Create a new transaction to go into the next block.

        Params:
          sender   <str>: Address of sender
          receiver <str>: Address of receiver
          amt      <int>: Amount of TKC to transfer

        Returns:
          idx <int>: index of to-be-created parent block
        '''

        self.current_transactions.append(Transaction(sender,receiver,amt))
        return self.num_blocks

    @property
    def MINE_ADDR(self):
        ''' Node address reserved for successful mine '''
        return '0'

    @property
    def last_block(self):
        return self[-1]

    @property
    def num_blocks(self):
        return len(self)

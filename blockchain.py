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
        for key in d.keys():
            if key not in Transaction.keys():
                raise ValueError(f'Transaction::UnexpectedKey: {key}')
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

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
        return self.chain.new_transaction(sender,receiver,amt)

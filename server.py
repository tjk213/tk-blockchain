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
import argparse

import blockchain as bc

class HTTP:
    OK = 200
    Created = 201
    BadRequest = 400
    NotFound = 404
# End HTTP

chain = bc.Blockchain()

app = flask.Flask('TKBC')
node_id = str(uuid.uuid4()).replace('-','')

def brute_force_proof(last_proof):
    proof = 0
    while not chain.valid_proof(last_proof,proof):
        proof += 1
        if proof % 100000 == 0:
            print(f'guess = {proof}...\r',end='',flush=True)
    return proof


@app.route('/chain', methods=['GET'])
def full_chain():
    #print('server.py:')
    #print(chain.chain)
    #print('\n\n\n\n\n')

    ack = {
        'chain' : chain.chain
    }
    return flask.jsonify(ack), HTTP.OK

@app.route('/register', methods=['POST'])
def register_node():
    req = flask.request.get_json()

    try:
        node = req['addr']
    except KeyError as e:
        return "Failed to decode node address", HTTP.BadRequest

    chain.register_node(node)
    ack = {
        'message' : f'Node successfully registered.'
    }

    return flask.jsonify(ack), HTTP.Created

@app.route('/resolve', methods=['GET'])
def resolve():
    replaced = chain.resolve_conflicts()

    msg = 'Chain Replaced' if replaced else 'Chain Retained'

    ack = {
        'message' : msg,
        'chain' : chain.chain
    }

    return flask.jsonify(ack), HTTP.OK


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    req = flask.request.get_json()

    try:
        idx = chain.new_transaction(req['sender'],req['receiver'],req['amount'])
    except KeyError as e:
        return "Missing sender/receiver/amount", HTTP.BadRequest

    ack = {
        'message' : f'Transaction will be added to block {idx}'
    }

    return flask.jsonify(ack), HTTP.Created

@app.route('/mine', methods=['GET'])
def mine():
    last_proof = chain.last_block.proof
    next_proof = brute_force_proof(last_proof)

    chain.new_transaction(chain.MINE_ADDR,node_id,1)
    next_block = chain.create_block(next_proof)

    ack = {
        'message' : 'New Block Forged',
        'proof' : next_block.proof
    }

    return flask.jsonify(ack), HTTP.OK

def main():
    parser = argparse.ArgumentParser(description='Initiate server node for TK-Chain')
    parser.add_argument('--port','-p',type=int,metavar='<portnum>',required=True,
                        help='Port number through which the server can be contacted')

    args = parser.parse_args()

    next_proof=77
    num_proofs = 0
    while (num_proofs < 1):
        next_proof = brute_force_proof(next_proof)
        print(f"Found next proof: {next_proof}")
        num_proofs += 1

    print('Starting server...')
    app.run(host='0.0.0.0',port=args.port)
    return


if __name__ == "__main__": sys.exit(main())

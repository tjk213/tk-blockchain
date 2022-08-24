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

import os
import sys
import math
import argparse

import multiprocessing as mp

from blockchain import Blockchain

chain = Blockchain.init()

def proof_of_work(incr):

    assert math.gcd(2**32,incr) == 1, "Invalid increment"
    print(f'{os.getpid()}: Running with increment={incr}...')
    proof = 0
    last_proof = chain.last_block.proof
    print(f'{incr:02d}: len={len(chain)} - last_proof={last_proof}')
    while not Blockchain.valid_proof(last_proof,proof):
        proof = (proof+incr) % 2**32
        if proof == 0:
            raise RuntimeError('No proof exists')

    print(f'{incr:02d}: Found block! len={len(chain)}')
    return proof
    #next_block = chain.mine_block(proof)

increments = [3,5,7,11]

def mine_block():
    #results = p.map(mine_block,[3,5,7,11])

    pool = mp.Pool(len(increments))
    results = [pool.apply_async(proof_of_work,[i]) for i in increments]

    # poll
    print('polling...',flush=True)
    proof = None
    while (True):
        if proof is not None:
            break
        for res in results:
            if res.ready():
                print('Ready!')
                proof = res.get()
                pool.terminate()
                pool.join()
                break

    print(f'LEN = {len(chain)} - POW = {proof}',flush=True)
    return proof


def main():
    parser = argparse.ArgumentParser(description='Spin up nodes & miners and test TKBC',
                               formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog,max_help_position=60))

    parser.add_argument('--num-blocks',type=int,default=2,metavar='<int>',help='Default: 2')

    args = parser.parse_args()
    mp.set_start_method('fork')
    #with mp.Pool(len(increments)) as p:
    for i in range(args.num_blocks):
        print(f'Mining block #{i+1}...',flush=True)
        proof = mine_block()
        chain.mine_block(proof)


if __name__ == '__main__': sys.exit(main())

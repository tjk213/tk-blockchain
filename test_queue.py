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
import time
import argparse

import numpy as np
import multiprocessing as mp

from blockchain import Blockchain

class Miner:
    def __init__(self,queue,incr,num_miners):
        assert math.gcd(2**32,incr) == 1, "Invalid increment"
        self.queue = queue
        self.incr = incr
        self.num_peers = num_miners-1
        self.chain = Blockchain.init()
        return

    def valid_proof(self,proof):
        last_proof = self.chain.last_block.proof
        return Blockchain.valid_proof(last_proof,proof)

    def log(self, msg, **kwargs):
        print(f'{self.incr:02d}: {msg}', flush=True, **kwargs)

    def broadcast(self,proof):
        self.queue.join()
        for _ in range(self.num_peers):
            # Throws queue.Full if queue is full for more than 4 seconds
            self.queue.put(proof,block=True,timeout=4)
        self.queue.join()
        self.log('Broadcast Complete.')

    def run(self,num_blocks):
        assert len(self.chain) == 1,"Pre-mined chain?"
        self.log('Starting...')
        start = 0
        proof = start
        while True:
            # If we reach the target, we're done
            if len(self.chain) == num_blocks:
                self.log('Chain done. exiting...',end='FOO\n')
                break

            # Sync with other miners
            if not self.queue.empty():
                # TODO: handle race condition that throws queue.Empty()
                next_proof = self.queue.get(block=True)
                self.chain.mine_block(next_proof)
                self.log('Chain updated.')
                self.queue.task_done()
                proof = start # reset

            # If we reach the target, we're done
            if len(self.chain) == num_blocks:
                self.log('Chain done. exiting (dos!)...',end='BAR\n')
                break

            # Hash away
            for i in range(10000):
                proof = (proof+self.incr) % 2**32
                if proof == start: # TODO: Can this be a one-liner?
                    raise RuntimeError('No proof exists')

                if self.valid_proof(proof):
                    self.chain.mine_block(proof)
                    self.log(f'Found block! len={len(self.chain)}')
                    self.broadcast(proof) # Broadcast block
                    proof = start # Reset proof
                    break
        return

    def print_chain(self):
        self.log('Final Blockchain:')
        for i,block in enumerate(self.chain):
            print(f'Block #{i}: {block}')
        return

def run_miner(q,incr,num_miners,num_blocks,display):
    miner = Miner(q,incr,num_miners)
    miner.run(num_blocks)
    if display:
        q.join()
        miner.print_chain()
    return

increments = [3,5,7,11]

def main():
    parser = argparse.ArgumentParser(description='Spin up nodes & miners and test TKBC',
                               formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog,max_help_position=60))

    parser.add_argument('--num-blocks',type=int,default=2,metavar='<int>',help='Default: 2')
    parser.add_argument('--num-miners',type=int,default=3,metavar='<int>',help='Default: 3')

    args = parser.parse_args()
    #mp.set_start_method('fork')
    #with mp.Pool(len(increments)) as p:

    print('Initializing environment...')
    miners = []
    q = mp.JoinableQueue()
    print('Initializing miners...')
    for i in range(args.num_miners):
        incr = increments[i]
        m = mp.Process(target=run_miner,daemon=True,
                       args=(q,incr,args.num_miners,args.num_blocks,i==0),name=f'M{incr}')
        m.start()
        miners.append(m)

    print('Running miners...')
    for i,m in enumerate(miners):
        m.join()

    print('done.')
    return

if __name__ == '__main__': sys.exit(main())

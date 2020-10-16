# Using qiskit to implement the Grover search algorithm to find non-frustrated instances of a fully connected Ising model spin glass

In this code I used the grover search algorithm to find special instances of the spin problem where every bond can be satisfied. Then I give the option to visualize those instances. I'm not sure if this is useful at all, but I did it just to get some qiskit/quantum computing practice. 

**I did not write all of this code.** I wrote everything in SGViz.py. The code in SGFrustration is a modified version of the IBM qiskit tutorial on the grover search algorithm. The code in tfim.py was written by someone else and used with permission.

## Getting it running

Runs on python3. Make sure to install (with pip or something) qiskit, PyQt5, and matplotlib. This also uses numpy, scipy, itertools, progressbar, os, sys, threading, and argparse.

Open command line in the direcotry and run 

`python3 SGFrustration.py`

Then enter the number of spins (no fewer than 3, nor greater than 6) and follow the prompts. It'll give you a list of bond configurations that you can visualize. Just input the number in the list that corresponds to that configuration and it'll pop out a visualization. Close the visualization to return to the code and you can visualize another or quit.

The bond configurations are stored as a list of 0s and 1s. 1 corresponds to ferromagnetic (same preferred) bonds, 0 corresponds to anti-ferromagnetic bonds (different prefferred). The farthest left digit is the bond between spins 0 and 1.

Here's an example of running it for a size six spin glass.

<img src="https://github.com/adlantz/QiskitSG/blob/main/ReadMeImages/runningexample.png" alt="RunExample" width="400"/>

The visualization that pops out should look like this:

<img src="https://github.com/adlantz/QiskitSG/blob/main/ReadMeImages/vizexample1.png" alt="vizexample" width="400"/>

The bond list tells you what digit in the bond configurations corresponds to what bond in the spin glass. In this example, the farthest left digit of the bond configuration is 0. Thus the bond between 1 and 0 is anti-ferromagnetic. You can play around by changing the state of the spin glass by entering it into the state box at the bottom and pressing enter. If you put in a state greater than 2^N it'll break.

<img src="https://github.com/adlantz/QiskitSG/blob/main/ReadMeImages/excitedstatexample.png" alt="excitedexample" width="400"/>

The dashed lines represent unsatisfied bonds. 

For a basic overview of the spin glass problem see the section below.

## The Spin Glass Problem

Say you have a group of people, Alice, Bob, and Carol. Each is given a sign that is orange on one side and blue on the other. They are also given a set of relationships between people. For instance the relationships could be

1. Alice and Bob: Same color
2. Alice and Carol: Different color
3. Bob and Carol: Different color

The group then has to display the color that matches these criteria. In this example, Alice and Bob try to display the same color as each other, and different from Carol. So a solution to this problem would be that Alice and Bob display blue and Carol displays orange. 

<img src="https://github.com/adlantz/QiskitSG/blob/main/ReadMeImages/nonfrust.png" alt="NotFrustrated" width="400"/>

However, sometimes they're given relationships which can't be fully satisfied. For instance

1. Alice and Bob: Same color
2. Alice and Carol: Different color
3. Bob and Carol: Same color

In this case Alice and Bob can choose blue, but whatever Carol chooses she can only satisfy one relationship.

<img src="https://github.com/adlantz/QiskitSG/blob/main/ReadMeImages/frust1.png" alt="Frustrated1" width="400"/> <img src="https://github.com/adlantz/QiskitSG/blob/main/ReadMeImages/frust2.png" alt="Frustrated1" width="400"/> 

When not all of the relationships can be satisifed, this is called *frustration*. That's the technical term actually. In frustrated systems, the solution to this problem is the one that satisfies the most relationships, as opposed to every relationship.

This peculiar situation is an instance of the *spin glass problem*. When physicists talk about it they talk about *spins* instead of people. And instead of displaying either orange or blue, the spins can be either "spin up" or "spin down". And the relationships between the people are called *bonds*. The bonds can either be ferromagnetic (same) or antiferromagnetic (different). I believe the term "glass" comes from an analogy to the chemical structure of glass. When a bond is satisfied, it has lower energy than when it is unsatisfied. Thus the spin glass problem consists of finding the lowest possible energy of the whole system.

When mathematicians/computer scientists talk about this problem they turn it all into 1s and -1s, naturally. A person i can be in the state P(i) = 1 or -1. A relationship R(i,j) is also either -1 or 1. Thus, between two people i and j, you try to maximize the quantity R(i,j)\*P(i)\*P(j). Therefore, in general, you're trying to maximize sum ( R(i,j)\*P(i)\*P(j) ) for every person i and j in the group (being careful not to double count relationships).

So why is the spin glass problem important? It turns out that it's really hard to solve as the number of people/spins grows. For N people, there are 2^N different ways the people could display their colors. Computer scientists are interested in hard problems like this because learning efficient ways to solve them can have practical applications to many other difficult problems to solve in the real world. They're also interesting and scientists' masochism lead them to problems that will make them bang their head against the wall.

In this code I am not solving the spin glass problem. I am just using a quantum computing algorithm (simulated using qiskit) called the grover search algorithm to find every instance of the spin glass problem of a particular size that has no frustration. I'm not sure if this is useful at all, but I did it just to get some qiskit/quantum computing practice. Also by fully connected I mean every spin has bond with every other spin.

# Using qiskit to implement the Grover search algorithm to find non-frustrated instances of a fully connected Ising model spin glass


## The Spin Glass Problem

Say you have a group of people, Alice, Bob, adn Carol. Each give a sign that is orange on one side and blue on the other. They are also given a set of relationships between people. For instance the relationships could be

1. Alice and Bob: Same color
2. Alice and Carol: Different color
3. Bob and Carol: Different color

The group then has to display the color that matches these criteria. In this example, Alice nad Bob try to display the same color as each other, and different from Carol. So a solution to this problem would be that Alice and Bob display blue and Carol displays orange. 

<img src="https://github.com/adlantz/QiskitSG/blob/main/ReadMeImages/nonfrust.png" alt="NotFrustrated" width="400"/>

However, sometimes they're given relationships which can't be full satified. For instance


1. Alice and Bob: Same color
2. Alice and Carol: Different color
3. Bob and Carol: Same color

In this case Alice and Bob can choose blue, but whatver Carol chooses she can only satisfy one relationship.

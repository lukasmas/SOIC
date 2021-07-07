# libraries
import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt

graph = {0: [1, 2, 3], 1: [0, 2], 2: [0, 1, 4], 3: [0, 4], 4: [3, 2]}

from_to = []
for g in graph:
    # print(g)
    for v in graph[g]:
        if [g, v] not in from_to and [v, g] not in from_to:
            from_to.append([g, v])

print(from_to)

splited_from = []
splited_to = []

for ft in from_to:
    splited_from.append(ft[0])
    splited_to.append(ft[1])

print(splited_from)
print(splited_to)

# Build a dataframe with your connections
# df = pd.DataFrame({'from': [0, 0, 0, 1, 2, 3], 'to': [1, 2, 3, 2, 4, 4]})
df = pd.DataFrame({'from': splited_from, 'to': splited_to})

# Build your graph
G = nx.from_pandas_edgelist(df, 'from', 'to')

# Graph with Custom nodes:
nx.draw(G, with_labels=True, cmap=plt.cm.Blues)
plt.show()


# yaml
#
#
# graph
#
# 100 x par nadwaca, odbiorca
#
# dodaj node
# usun
#
# nowe wiadmosci

# https://ieeexplore.ieee.org/document/7784246
# https://ieeexplore.ieee.org/document/4469422

#email za tydzien
# spotkanie 20.07 17:30


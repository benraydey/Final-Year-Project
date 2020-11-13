#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 19 16:40:07 2020

@author: benadey
"""


import numpy as np
from timeit import default_timer as timer

n_samples = 10000000


list1 = []
list2 = [None] * n_samples

list4 = np.empty(n_samples)
list4[:] = np.NaN

list5 = np.zeros(n_samples)

t0 = timer()
for i in range(n_samples):
    list1.append(5.123415)
t1 = timer()-t0
t0 = timer()

for i in range(n_samples):
    list2[i] = 5.123415
t2 = timer()-t0
t0 = timer()

for i in range(n_samples):
    list4[i] = 5.123415
t4 = timer()-t0
t0 = timer()

for i in range(n_samples):
    list5[i] = 5.123415
t5 = timer() - t0

print(f"list1:{t1:<6.2} s")
print(f"list2:{t2:<6.2} s")

print(f"list4:{t4:<6.2} s")
print(f"list5:{t5:<6.2} s")

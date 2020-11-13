from timeit import default_timer as timer
import numpy as np

n = 10000000

x = [3] * n

print(x[0:10])

t0 = timer()
y = (np.array(x) - 2).tolist()          # TODO: WINNER
t1 = timer() - t0
print(f'{y[0:10]} t = {t1*1000:6.2f} ms')


t0 = timer()
y = list(np.array(x) - 2)
t1 = timer() - t0
print(f'{y[0:10]} t = {t1*1000:6.2f} ms')

y = [None]*n
t0 = timer()
for i in range(n):
    y[i]=x[i] - 2
t1 = timer() - t0
print(f'{y[0:10]} t = {t1*1000:6.2f} ms')
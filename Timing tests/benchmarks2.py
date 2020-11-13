from timeit import default_timer as timer

a = 3
n = 1000000

t0 = timer()
for i in range(1,n):
    if i !=3:
        pass
t_not_equals = timer() - t0
t0 = timer()

for i in range(1,n):
    if i > 1:
        pass

t_greater_than = timer() - t0

print(f't_not_equals: {t_not_equals*1000:6.2f} ms\nt_greater_than: {t_greater_than*1000:6.2f} ms')

# conclusion: the same.
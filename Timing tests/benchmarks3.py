
import numpy as np
from statistics import mean
from timeit import default_timer as timer

# in conclusion, numpy is faster in every way


n = 100000
a = (np.arange(0,n,1)).tolist()

t0 = timer()
mean_a1 = mean(a)
t1 = timer() - t0
print(t1*1000)

t0 = timer()
mean_a1 = np.mean(a)
t1 = timer() - t0
print(t1*1000)





# n = 100000
# a = [1]*n
# b = [3]*n

# a_np = np.array(a)
# b_np = np.array(b)

# t0 = timer()
# c = [None]*len(a)
# for i in range(len(a)):
#     c[i] = a[i] - b[i]
# t1 = timer() - t0

# a = [1]*n
# b = [3]*n

# a_np = np.array(a)
# b_np = np.array(b)

# t0 = timer()
# c = [None]*len(a)
# for i in range(len(a)):
#     c[i] = a[i] - b[i]
# c2 = np.array(c)
# t2 = timer() - t0


# t0=timer()
# c3 = a_np - b_np
# t3=timer()-t0

# print(c[0:10])
# print(f'lists: {t1*1000} ms\n')
# print(c2[0:10])
# print(f'lists: {t2*1000} ms\n')
# print(c3[0:10])
# print(f'lists: {t3*1000} ms\n')





# a = list(range(1,100))

# t0 = timer()
# b = sum(i*i for i in a)
# t1 = timer() - t0

# a = np.array(a)
# t0=timer()
# b_np = sum(a*a)
# t2 = timer() - t0

# print(f'\nlists: {t1*1000:6.2f} ms\n  {b}')
# print(f'numpy: {t2*1000:6.2f} ms\n  {b_np}')

# n = 400000
# x = list(range(n))

# t0 = timer()
# a=[]
# for i in range(n):
#     if i > n-4:
#         break
#     else:
#         a.append(x[i])
# t1 = timer()-t0

# t0=timer()
# for i in range(n):
#     if i > n-4:
#         z = i
#         break
# a=x[0:z]
# t2 = timer()-t0
# print(f'{t1*1000}\n{t2*1000}')
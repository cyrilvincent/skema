import numpy as np
import matplotlib.pyplot as plt
import scipy.optimize as opt

x = np.array([136,650,1835,3447,5863])
y = np.array([0,0.2,0.5,0.7,1])

xbar = np.array([0,272,273,1027,1028,2642,2643,4251,4252,7450])
ybar = np.array([0,0,0.2,0.2,0.5,0.5,0.7,0.7,1,1])

plt.plot(x, y)
plt.plot(xbar, ybar, color="black")


f = lambda x, a, b: a*x**2 + b*x
res = opt.curve_fit(f, xbar, ybar)
print(res[0])

def g(x):
    a = -2.18e-8
    b = 2.95e-4
    x = np.where(x > -b/(2*a), -b/(2*a), x)
    return np.clip(a*x**2 + b*x, 0, 1)

x = np.arange(7000)
y = f(x, res[0][0], res[0][1])
plt.plot(x, y, color="green")
plt.plot(x, g(x), color="red")
plt.show()





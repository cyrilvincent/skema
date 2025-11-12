import numpy as np
import matplotlib.pyplot as plt

time = 30
for accessibilite_exp in [-0.12, -0.10, -0.08, -0.06, -0.04]:
    if (time > 30 and accessibilite_exp < -0.08) or (time == 30 and accessibilite_exp > -0.06) or (time > 45 and accessibilite_exp < -0.06):
        continue
    print(accessibilite_exp)

f = lambda x,a: np.exp(a * x)
x = np.arange(60)

i=1
for a in np.arange(-0.12,-0.03,0.01):
    plt.subplot(3,3,i)
    plt.ylim(0, 1)
    plt.xlim(0, 60)
    plt.title(f"{a:.2f}")
    y = f(x, a)
    plt.plot(x,y)
    i+=1

plt.show()





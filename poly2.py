from math import sqrt
import matplotlib.pyplot as plt
import numpy as np

print("Polynome du 2nd degré")
print("f(x) = ax² + bx + c")

a = input("a (enter pour random): ")
if a != "":
    b = input("b: ")
    c = input("c: ")
else:
    a = np.random.randint(-5, 15)
    if a == 0:
        a = "10"
    elif a >= 10:
        d = np.random.randint(2, 6)
        a = f"{a - 9}/{d}"
    else:
        a = str(a)
    print(f"a: {a}")
    b = np.random.randint(-5, 20)
    if b > 15:
        b = f"sqrt({np.random.randint(2, 11)})"
    elif b > 10:
        d = np.random.randint(2, 6)
        b = f"{b - 10}/{d}"
    else:
        b = str(b)
    print(f"b: {b}")
    c = np.random.randint(-5, 15)
    if c >= 10:
        d = np.random.randint(2, 6)
        c = f"{c - 10}/{d}"
    else:
        c = str(c)
    print(f"c: {c}")
print(f"f(x) = {a}x² + {b}x + {c}")

a = eval(a)
b = eval(b)
c = eval(c)

alpha = -b / (2 * a)
print(f"α = -b/2a = -{b}/(2({a})) = {-b} / {2*a} = {alpha:.2f}")
delta = b ** 2 - 4 * a * c
beta = delta / (4 * a)
print(f"β = (b²-4ac)/4a = ({b}²-4({a})({b}))/4({a}) = ({b ** 2}-({4 * a * c}))/{4 * a}) = {delta:.2f}/{4 * a} = {beta:.2f}")
print(f"Forme canonique = a(x - α)² + β = {a}(x - {alpha:.2f})² + {beta:.2f}")
print()

falpha = a * alpha ** 2 + b * alpha + c
print("Tableau de variation")
if a < 0:
    print("a < 0")
else:
    print("a > 0")
print(f"f(α) = {a}{alpha:.2f}² + {b}{alpha:.2f} + {c} = {a * alpha ** 2:.2f} + {b * alpha:.2f} + {c} = {falpha:.2f}")
print(f"x   |-∞       α    +∞")
if a > 0:
    print(f"f(x)|   ↘   f(α)  ↗")
else:
    print(f"f(x)|   ↗   f(α)  ↘")
print()

print(f"Resolution de f(x) = ax² + bx + c = 0")
print(f"Δ = b² - 4ac = {b ** 2}-({4 * a * c})) = {delta:.2f}")
if delta < 0:
    print(f"Δ < 0 : Aucune solution")
    print()
    print("Tableau des signes")
    print(f"x   |-∞    +∞")
    if a > 0:
        print(f"f(x)|    +")
    else:
        print(f"f(x)|    -")
elif delta == 0:
    print(f"Δ = 0 : x0 = α = {alpha:.2f}")
    print(f"Factorisation = a(x - x0)² = {a}(x - {alpha:.2f})²")
    print()
    print("Tableau des signes")
    print(f"x   |-∞  x0  +∞")
    if a > 0:
        print(f"f(x)| +  0  +")
    else:
        print(f"f(x)| -  0  -")
else:
    print(f"Δ > 0 : x1 = (-b + √Δ) / 2a et x1 = (-b - √Δ) / 2a")
    x1 = (-b + delta ** 0.5) / (2 * a)
    x2 = (-b - delta ** 0.5) / (2 * a)
    print(f"x1 = (-{b} + √{delta}) / 2{a} = ({-b} + {sqrt(delta): .2f}) / {2 * a} = {x1:.2f}")
    print(f"x2 = (-{b} - √{delta}) / 2{a} = ({-b} - {sqrt(delta): .2f}) / {2 * a} = {x2:.2f}")
    print(f"Factorisation = a(x - x1)(x - x2) = {a}(x - {x1:.2f})(x - {x2:.2f})")
    print()
    print("Tableau des signes")
    print(f"x   |-∞  x1     x2  +∞")
    if a > 0:
        print(f"f(x)|  +  0  -  0  +")
    else:
        print(f"f(x)|  -  0  +  0  -")

# x = np.arange(-5, 5, 0.1)
# y = a * x ** 2 + b * x + c
# plt.axhline(0, color='black', linewidth=1)
# plt.axvline(0, color='black', linewidth=1)
# plt.plot(x, y)
# plt.show()


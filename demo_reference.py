# By Value
a = 1
b = a
a += 1
print(a, b)

# By reference
a = [1, 2]
b = a
a.append(3)
print(a, b)

# Clone
a = [1, 2]
b = list(a)
a.append(3)
print(a, b)
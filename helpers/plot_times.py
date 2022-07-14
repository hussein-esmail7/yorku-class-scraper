import matplotlib.pyplot as plt
import numpy as np

title = "Time per 'tr'"
xLabel = "Row"
yLabel = "Time (s)"

# in_file = input("File location: ")
in_file = "/Users/hussein/Downloads/scraper/time_all.txt"
y_coords = [float(i.replace("\n", "").strip()) for i in open(in_file).readlines()]

# x = np.array(range(1, len(y_coords)-1))
y = np.array(y_coords)
# plt.yticks(np.arange(y.min(), y.max(), 0.05))
# plt.plot(x, y)
plt.plot(y)
# plt.grid(axis='y', linestyle='-')
plt.show()


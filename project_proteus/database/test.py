from matplotlib import pyplot as plt

from database import DataBase


db_spot = DataBase("/Users/fabio/Desktop/project-proteus/databases/test")
db_futures = DataBase("/Users/fabio/Desktop/project-proteus/databases/test2")

plt.plot(db_spot["5m", "close"])
plt.plot(db_futures["5m", "close"])

plt.show()
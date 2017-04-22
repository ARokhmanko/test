'''
Created on 15 апр. 2017 г.

@author: ARokhmanko
'''
import random
from conda._vendor.toolz.dicttoolz import get_in
from dask.array.ufunc import minimum
from bokeh.themes import default


def get_int(msg, minimum, default):
    while True:
        try:
            line = input(msg)
            if not line and default is not None:
                return default
            i = int(line)
            if i < minimum:
                print ("должно быть >= ", minimum)
            else:
                return i
        except ValueError as err:
            print(err)
 
#print ("Вы ввели = ", get_int("введите число", 5, 3))
rows = get_int("строк ", 1, None)
columns = get_int("столбцов ", 1, None)
minimum = get_int("минимальное значение ", -10000, 0)

default = 1000
if default < minimum:
    default = 2*minimum
maximum = get_int("максимум ", minimum, default)


row = 0 
while row < rows:
    line = ""
    column = 0
    while column < columns:
        i = random.randint(minimum, maximum)
        s = str(i)
        while len(s)< 10:
            s = " " + s
        line += s
        column += 1
    print (line)
    row += 1

            

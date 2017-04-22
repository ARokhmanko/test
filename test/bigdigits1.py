'''
Created on 15 апр. 2017 г.

@author: ARokhmanko
'''
import sys
from builtins import str



def get_int(msg):
    try:
        i = int(input(msg))
        return i
    except ValueError as err:
        print(err)

 
print ("hello, world! ")
one =["     **",
      "    * *",
      "   *  *",
      "      *",
      "      *",
      "      *",
      "      *"
      ]

two =[" ******",
      " *    *",
      "      *",
      "     * ",
      "    *  ",
      "   *   ",
      "  *****"
      ]
three=[" ******",
       "     * ",
       "    *  ",
       "   *   ",
       "    *  ",
       "     * ",
       " ******"
       ]
four=[ "   *   ",
       "  *   *",
       " *    *",
       " ******",
       "      *",
       "      *",
       "      *"
       ]
five=[ "****** ",
       "*      ",
       "*      ",
       " ***** ",
       "      *",
       "      *",
       "****** "
       ]
six=[ " ******",
       "*      ",
       "*      ",
       "****** ",
       "*     *",
       "*     *",
       " ***** "
       ]
seven=["*******",
       "    *  ",
       "  *    ",
       " *     ",
       "*      ",
       "*      ",
       "*      "
       ]
eight=[" ***** ",
       "*     *",
       "*     *",
       " ***** ",
       "*     *",
       "*     *",
       " ***** "
       ]
nine=[ " ***** ",
       "*     *",
       "*     *",
       " ******",
       "      *",
       "      *",
       " ***** "
       ]
zero=[ " ***** ",
       "*     *",
       "*     *",
       "*     *",
       "*     *",
       "*     *",
       " ***** "
       ]
Digits = [zero, one, two, three, four,five, six, seven, eight, nine]

#if __name__ == "__main__":
#    while (1):
#        time.sleep(1)
#        ttt()
def replace(st, simbol):
    j = 0
    sst=""
    for s in st:
        if  s == '*':
            sst += simbol
        else:
            sst += s
        j +=1     
    return sst

try:
    print (sys.argv[0])
    digits = sys.argv[1]
    row = 0 
    while row < 7:
        line = ""
        column = 0
        
        #print (replace("0*898*", "-"))
        
        while column < len (digits):
            number = int (digits[column])
            digit = Digits [number]
            #print (digits[column])
            #line += replace (digit[row], digits[column]) + "  "
            line += digit[row] + "  "
            column += 1
        print (line)
        row += 1
except IndexError:
    print ("usage: bigdigits.py <number>")
except ValueError as err:
    print (err, "in", digits)
        
    
#print(str(a.lstrip())==b.lstrip())   


    

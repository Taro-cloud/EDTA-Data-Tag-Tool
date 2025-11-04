import sys
import os
from pathlib import Path
import json
import threading




def printArgv():
    #print('getcwd:      ', os.getcwd())## 実行パスではなくおかしい。
    #print('__file__:    ', __file__)#**.pyまで入る
    #print(sys.argv[0] )
    print("--"+str(sys.argv) )
    print("--"+str(sys.argv[1])+",22" )
    print("--"+str(sys.argv[1])+",33" )
    
#if __name__ == "__main__":
printArgv()

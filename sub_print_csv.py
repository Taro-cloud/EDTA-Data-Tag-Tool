# -*- coding: utf-8 -*-

"""
(c)2025 T. Hayakawa
dataTagEditorのsubrocess用*.pyのサンプル
同じディレクトリのすべてのcsvファイルの指定列を、stdoutへ1ファイル1行で表示する(数値のみ）。
dataTagEitroがこれをstdoutから受け取って、ファイル名,dataの行の表をつくる。

ファイル名には、実験条件の"*Pa,*W"が含まれているとして、これをパターンマッチで取り出して、
dataの前につけて行にする。
"""

import glob
import os,sys,re
sys.stdout.reconfigure(encoding="utf-8")

## ファイルのデーター範囲
use_col=1 #0..
start_r=2 #0..
end_r=30 #end_r行は出力に含まれない。end_r-1まで

def isFloat(s):
    """
    文字列->floatの変換ができるかを、boolで返す。
    """
    try:
        float(s)
    except ValueError:
        return False
    else:
        return True

def getParam(filename) -> tuple:
    """
    ファイル名の"*Pa,*W"が含まれているとして、これをパターンマッチで取り出して返す。
    """
    ma1=re.search(r"(\d+)\s*[pP]a",filename)
    ma2=re.search(r"(\d+)\s*[wW]",filename)

    p1 =ma1.group(1) if ma1!=None else ""
    p2 =ma2.group(1) if ma2!=None else ""

    return p1,p2

def printAllFiles(fullpath,relpath,fileExt,start_r,end_r,use_col):
    files=glob.glob(fullpath+r"\*."+fileExt)
    #print(fullpath)
    #print("files "+str(files) )
        
    slineList=[]
    fileList=[]
    para1=[]
    para2=[]

    if len(files)<1: 
        return

    for file in files:

        ret= readCsv(file,start_r,end_r,use_col)
        #print(ret)
        slineList.append(ret)
        fileList.append(os.path.basename(file))
        p1,p2= getParam(os.path.basename(file))
        para1.append(p1)
        para2.append(p2)
    ##

    headerText="file, pa, W,"
    for  ii in range(len(slineList[0])) : #header output
        headerText+= str(ii) +"," #col headerはindex値。
    print(headerText)
    
    for ii in range(len(fileList)): #dataline output
        ff=fileList[ii]
        tline= ff +"," +para1[ii] +","+ para2 [ii] + ","
        
        for rr in slineList[ii]:
            tline += str(rr) +","
        print(tline )   ## ==> output

def readCsv(fullpath,start_r,end_r,use_col):
    """
    csvの指定列をすべてstdoutへ1ファイル1行で表示するサンプル。
    """

    f=open(fullpath,"r")
    datalines=f.readlines()
    f.close()
    dVal=[]

    if len(datalines)==0:
        return []    
    
    end_r = end_r if end_r<= len(datalines) else len(datalines)

    for ii in range(start_r,end_r):
        
        cols=datalines[ii].split(",")
        if(len(cols)>=use_col) and isFloat(cols[use_col]):
            dVal.append( cols[use_col].rstrip() )
    #print(datalines)
    #print("-----")
    return dVal

if __name__ == "__main__":
    #run_sub_print.batで実行する
    printAllFiles(sys.argv[1],sys.argv[2], "csv",start_r,end_r,use_col)

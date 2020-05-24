#!/usr/bin/python3
#############################################################################
# Project:  XYM
# File:     common.py
# Athor:    Henson
# Descrp:   base function for common use
#############################################################################
# Version: 0.1
# Initial version
#############################################################################

import os, sys, argparse
import time, re


# Arg head
# <desc>: description to display in help messgae
# <usa>: usage to display in help messgae
# [kw]: use key_value to specify option and help message corelated
def argHead(desc, usa, **kw):
    # return name space {{{
    parser = argparse.ArgumentParser(description=desc, usage=usa)    
    for k,w in kw.items():
        eval("parser.add_argument('-{0}', '--{1}', help='{2}')".format(k[0], k, w))
    params = parser.parse_args()

    r = {}
    for k in kw.keys():
        exec("r['{0}'] =  params.{0}".format(k))
    return r
    # }}}


# Display log information for output log and test log
# <out>: specify output object, out could be every type of python class
# [level]: specify error level as below
# 0: Info 
# 1: Warn 
# 2: Error 
# 3: Fatal Error 
# 4: Debug         could choose tun-off by testmode
# default: None
# [testmode]: turn on/off message which level is debug
##############################################################
# potential bug: it may be a bug if variables have same value
def log(out, level=None, testmode=True):
    # {{{
    if type(out) == str:
        msg = out
    else:
        pb = [k  for k,v in globals().items() if v is out]
        try:
            msg = "{0} -> {1}".format(pb[0] if len(pb)==1 else "(ptential bug) "+pb[0], out)
        except IndexError:
            msg = out
    if not level is None:
        pre = ["INFO", "WARN", "ERROR", "FATAL ERROR", "DEBUG", "EIXT"][level]
        if pre == "EIXT":
            print("{0}: {1}".format(pre, msg))
            exit()            
        elif not testmode or pre!="DEBUG":
            print("{0}: {1}".format(pre, msg))
    else:
        print(msg)
    #}}}
        
        
# Read file
# <dir>:  specify directory to read
# [line]: read from line[0] to line[1]
# [nu]:   return line number
def readFile(dir, line=None, nu=None):
    # return string{{{
    if os.path.exists(dir):
        num = 0
        content = ""
        with open(dir, "r", encoding="utf-8") as f:
            for l in f:
                num += 1
                if line:
                    if line[0] <= num <= line[1]:
                        content += l + "\n"
                    elif num > line[1]:
                        break
                else:
                    content += l + "\n"
        return num if nu else content
    else:
        print("READ FILE ERROR: File {0} not exists".format(dir))
        exit()
    # }}}

# Write file
# <dir>: specify directory to write
# <txt>: specify content to write out
# [add]: add to EOF if True, else will be clear and write
# [force]: file will be overwrite if file exists and force=True
def writeFile(dir, txt, add=False, force=False):
    # {{{
    if add:
        f = open(dir, "a+")
    elif os.path.exists(dir):
        if force:
            print("Warning: file {0} exists, will be overwirte.".format(dir))
        else:
            print("Error: file {0} exists, will quit.".format(dir))
            exit()
        f = open(dir, "w")
    else:
        f = open(dir, "w")
    f.write(txt)
    log("Write out to file {0}".format(dir), 0)
    f.close()
    #}}}

# Trace line, return line number that string first appears
# <s>: specify string to trace
# <txt>: text will detect
def traceLine(s, txt):
    # return line number {{{
    nu = 1
    for i in txt.split("\n"):
        if s in i:
            return nu
        nu += 1
    return -1
    # }}}

# Common parse: parse text according to variable
# <conf_file>: a text contain key_value paramter as input file
# [kw]: specify symbol and related means, can be added later, default as show below:
# sp =  use to split key and value
# an // annotation to text
# st "  will ragard as a string between st even if contains space, must be used in pairs
# co ,  split muti-value with co
# ed \n end of a line
def cparse(conf_file, **kw):
    # return parse dic {{{
    sp = kw.get("sp", "=")
    an = kw.get("an", "//")
    st = kw.get("st", '"')
    co = kw.get("co", ",")
    ed = kw.get("ed", "\n")
    signString = "@"
    signEnd = "$"
    
    f = readFile(conf_file)
    f = re.sub("{0}.*".format(an), "", f)
    strLis = re.findall("{0}.*?{0}".format(st), f)
    strLis.reverse()
    stPtn = re.compile("{0}.*?{0}".format(st), re.S)
    f = stPtn.sub(signString, f)
    if st in f:
        log("SyntaxError: invalid syntax in file %s Line %s" %(conf_file, traceLine(st, f))) 
        exit()
    f = re.sub(ed, signEnd, f)
    f = re.sub("\s", "", f)
    # parse FSM
    tmpk, tmpv, flist = "", [], []
    last = state = "idle"
    for w in f:
        # logic
        if w in [signEnd, signString, sp, co]:
            pass
        elif state == "key":
            tmpk += w
        elif state == "value":
            tmpk += w
            
        # stateate transfer
        if w == signEnd:
            state = "key"
            if last == "value":
                if tmpv != []:
                    tmpv.append(tmpk)
                    flist.append(tmpv)
                else:
                    flist.append(tmpk) 
            tmpv = []
            tmpk = ""
        elif w == sp:
            state = "value"
            flist.append(tmpk)
            tmpk = ""
        elif w == co:
            state = "value"
            tmpv.append(tmpk)
            tmpk = ""
        elif w == signString:
            tmpk = strLis.pop()
        last = state
    
    dic = {}
    for j in range(1,len(flist),2):
        dic[flist[j-1]] = flist[j]
    return dic
    # }}}

# Table parse, parse strings table
# return form: [[(item, value), ()], [] ] if no content will not append to list
# <tab>: talbe file to read
# <heading>: table heading, as reference to start table
def tparse(tab, heading=0):
    # return parse dic {{{
    tabList = readFile(tab).split("\n")
    # k for key, idx for index
    key = re.findall("\S+", tabList[heading])
    #print(tabList[heading])
    #print(key)
    idx = []
    for i in key:
        j = tabList[heading].find(i)
        # Use range to detect if cross, so +1
        idx.append([j, j+len(i)+1])
    # parse
    result = []
    for i in range(heading+1, len(tabList)):
        line = tabList[i]
        row = re.findall("\S+", line)
        for item in row:
            tidx = tabList[i].find(item)
            lidx = tabList[i].find(item)
            ridx = lidx+len(item)
            tabList[i]= tabList[i][:lidx] + " "*len(item) + tabList[i][ridx:]

            found = []
            for id in idx:
                if set(range(tidx, tidx+len(item)+1)).intersection(set(range(id[0], id[1]))):
                    found.append(id) 
            #print(item, found)
            if found != []:
                temp = key[idx.index(found[0])]
                #print(temp, item)
                result.append([temp, item])
    r = []
    tmp = [1]
    rst = True
    for i in result:
        if not rst:
            tmp.append(last)
        if i[0] == key[0]:
            rst = True
            if len(tmp) != 1:
                r.append(tmp)
                tmp = []
            tmp = [(i[0],i[1])]
        else:
            rst = False
        last = (i[0], i[1])
    return r
    # }}}

# Get time now
# [mode]: select time to get. 0 -> runtime, 1 -> cur time
START_TIME = time.time()
def get_time(mode=0):
# return time {{{
    if mode == 0:
        return (lambda sec:"{0}s".format(int(sec)) \
        if sec < 60 else "{0}m {1:>2}s" \
        .format(int(sec)/60, int(sec)%60))(time.time()- START_TIME)
    elif mode == 1:
        return time.asctime( time.localtime(time.time()) )
#}}}

# Convert:  split: 111111 --> 11_1111 & convert radix
# [numString]: input number, type is string
# [inputRadix]:  input radix, b, o, d, h
# [outputRadix]: output radix, b, o, d, h
# [split]: return value as 11_1111
def convert(numString, inputRadix=None, outputRadix=None, split=False):
# {{{
    if "x" in numString:
        return numString
    if inputRadix is outputRadix:
        if split:
            for i in range(len(numString) - 4, 0, -4):
                numString = numString[:i] + "_" + numString[i:]
        return numString
    else:
        outputRadix = "x" if outputRadix == "h" else outputRadix
        decimal = int(numString, {"b": 2, "o": 8, "d": 10, "h": 16}[inputRadix])
        numString = str("{:" + outputRadix + "}").format(decimal)
        return convert(numString, None, None, split)
#}}}

# Execute command in shell
# <cmd>: command, need to execute in shell
# [log]: default is none , will record execute log to it
def exe_sh(cmd, log=None):
    # {{{
    if log is None:
        os.system(cmd)
    else:
        writeFile(log, cmd, True)
        os.system("echo {0} | tee -a {1}".format(cmd, log))
#}}}

if __name__ == "__main__":
    print(get_time(1))


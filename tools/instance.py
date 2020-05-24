#!/usr/bin/python
import os, sys, re
sys.path.append(r"D:\pyLab\source\common")
from common import *

usage = """
Descriptio: For RTL module instance, only use with verilog file
python moudle_instance.py rtlcode.v
"""
INSTANCE_AFFIX = "_inst0"
SPACE1 = 4*" "
SPACE2 = 8*" "
FILL = True

# Local function {{{
def isFind(i, line):
    return line.find(i) > -1
# }}}

# instance wire according to result dict
# <result>: result dict, from instance
# [replaceParams]: repalce parameter variable
# [top]: repalce all type to wire
def insWire(result, top=False, replaceParams=True):
    # return wir {{{
    wir = ""
    # Repalce paramter if paramter isn't null \
    if replaceParams:
        if not result["params"] == []:
            k,v = [],[]
            [k.append(i[0]) for i in result["params"]]
            [v.append(i[1]) for i in result["params"]]
            for i in range(len(result["io"])):
                if result["io"][i][2].find(":")>-1 and sum(j in result["io"][i][2] for j in k):
                    index = [j in result["io"][i][2] for j in k].index(True)
                    exp = result["io"][i][2].replace(k[index], v[index]).split(":") 
                    result["io"][i][2] = "{0}:{1}".format(eval(exp[0]), eval(exp[1]))
    
    maxLen = max(len(i[2]) for i in result["io"])
    for p in result["io"]:
        typ = "wire" if top else "reg " if p[1] == "input" else "wire"
        if p[1] == "pre":
            wir += p[0]+"\n"
        elif p[2] == "1":
            wir += ("{1} %s   {0};\n" %(maxLen*" ")).format(p[0], typ)   
        else:
            wir += ("{2} [{0:^%d}] {1};\n" %(maxLen)).format(p[2], p[0], typ)
    return wir
    # }}}



# isntance moudle
# <result>: result dict, from instance
# <fixLen>: specify length of every word in instance text
def insModule(result, fixLen=None):
    # return ins {{{ 
    # Instance
    # result: {"module", "param", "io":[[port, direction, bw]], "type"}
    # to ensure the order of IO with ifdef conditon, '`ifdef' is assignment as ["`ifdef xxx", "pre", ""]
    ins = "{0} ".format(result["module"])
    # Paramters
    if result["params"] == []:
        ins += " {1}{0} (\n".format(INSTANCE_AFFIX, result["module"])
    else:
        ins += "#(\n"
        for kv in result["params"]:
            ins += "{2}.{0}({1}),\n".format(kv[0], kv[1],SPACE2) 
        ins = ins[:-2] + ")\n"
        ins += "{2}{1}{0} (\n".format(INSTANCE_AFFIX, result["module"], SPACE1)
    # IO ports
    maxLen = max(len(i[0]) for i in result["io"]) if fixLen is None else fixLen
    for p in result["io"]:
        p = p[0]
        if p.find("`") > -1:
            ins += ("{1}{0:%d}\n" %(maxLen+2)).format(p, SPACE2[:-4])
        else:
            ins += ("{1}.{0:%d}({0:^%d}),\n" %(maxLen+2, maxLen+10)).format(p, SPACE2)
    return ins[:-2] + ");"
    # }}}


# instance according to file
# <file>: rtl file, only support v2k now
# [top]: top mode, will specify IO as wire if True, otherwise input will specify as reg
# [isWrite]: write out to module_instance.out
def instance(file, top=False, isWrite=False):
    # return wir, ins, result {{{
    # result: {"module", "param", "io":[[port, direction, bw]], "type"}
    result = {"io":[], "params":[]}
    
    modulePtn = re.compile("module.*?;", re.S)
    commentPtn = re.compile("//.*")
    commentPtn2 = re.compile("/\*.*?\*/", re.S)
    
    # Raw input file
    f = readFile(file)
    f = commentPtn.sub("", f)
    f = commentPtn2.sub("", f)
    # Extract module xxx ()
    head = modulePtn.findall(f)
    # mismatch
    if len(head) == 0:
        log("Bug flag", 2)
        exit()
    else:
        if isFind("input", head[0]) or isFind("output", head[0]):
            result["type"] = "v2k"
        else:
            # Transfer v95 to v2k
            result["type"] = "v95"
            f =  commentPtn.sub("", f)
            f =  commentPtn2.sub("", f)
            ioLis = re.findall("input.*?;|output.*?;|inout.*?;", f)
            transPtn = re.compile("\(.*\);", re.S)
            head[0] = transPtn.sub("("+"\n".join(ioLis).replace(";", ",")[:-1]+");", head[0])

    # Parse
    space = [" ", "\n"]
    sign = [",", "#", "(", ")", "=", ";", "[", "]", ":", "-", "+"]
    txt = commentPtn.sub("", head[0])
    txt = commentPtn2.sub("", txt)
    txt = txt.replace("\t", " ")
    tmp = ""
    smash = []
    for i in txt:
        if i in space:
            if not tmp == "":
                smash.append(tmp)
            tmp = ""
        elif i in sign:
            if not tmp == "":
                smash.append(tmp)
            tmp = ""
            smash.append(i)
        else:
            tmp += i
    # Parse FSM     
    st = "idle"
    kw = []
    lastw = ""
    tmp = ""
    assignment = False 
    for w in smash:
        # Assignment
        if st == "module":
            result[st] = w
            st = "idle"
        elif st == "params":
            if assignment:
                if w == "parameter":
                    pass
                else:
                    kw.append(w)
                    assignment = False
            elif w in ["parameter", "=", ","]:
                assignment = True
                if w == ",":
                    result["params"].append(kw)
                    kw = []
            elif w == "(" and lastw == ")":
                result["params"].append(kw)
                kw = []
                st = "idle"
   
        # result: {"module", "param", "io":[[port, direction, bw]], "type"}
        # to ensure the order of IO with ifdef conditon, '`ifdef' is assignment as ["`ifdef xxx", "pre", ""]
        elif st == "io":
            if assignment:
                if w.find("`") > -1:
                    pass
                elif not w in  ["reg", "wire", "[", "input", "output"]:
                    tlis = (tmp + " " + w).split(" ")
                    bw = "".join(tlis[1:-1]) if ":" in tlis else "1"
                    direction =  result["io"][-1][1] if tlis[0] == "" else tlis[0] 
                    result["io"].append([tlis[-1], direction, bw])
                    assignment = False
                    tmp = ""
                elif w == "[":
                    assignment = False
            elif w in ["input", "output", "]", ","]:
                assignment = True
            else:
                tmp += " "+w

        elif st == "pre":
            if lastw == "`endif" or lastw == "`else":
                result["io"].append([lastw, "pre", ""])
            else:
                result["io"].append([lastw+" "+w, "pre", ""])
            st = "idle"            

        lastw = w
        # State convert
        if w == "module":
            st = "module"
        elif w == "#":
            st = "params"
        elif w in ["input", "output"]:
            assignment = True
            tmp = w
            st = "io"
        elif w.find("`") > -1:
            # locked in state params to parse macro
            #if st != "params":
            #    st = "pre"
            if w in ["`ifdef", "`else", "`define"]:
                st = "pre"
    
    isWire = 1
    replaceParams = 1
    if isWire:
        wir = insWire(result, top, replaceParams)
        if isWrite:
            writeFile("module_instance.out", wir)
    isInstance = 1
    if isInstance:
        ins = insModule(result)
        if isWrite:
            writeFile("module_instance.out", ins, True)
    return wir, ins, result
    # }}}


# Package top module, this function can parse all sub-module, instance and package them in one top module rtl file
# <top>: top module name and file name
# <subList>: sub-module rtl file list, contain absolute directory
# [isModuleHead]: contian module_endmodule and port defination
# [isWrite]: write out to module_instance.out 
def pkgTop(top, subList, isModuleHead=True, isWrite=False):
    # {{{
    # lis {{module1}, {module2}}
    lis = [instance(i, 0)[2] for i in subList]
    io = []
    ins = ""
    maxLen = max(max(len(i[0]) for i in m["io"]) for m in lis)
    # instance
    for m in lis:
        io.extend(m["io"])
        ins += "\n\n// {0} instance\n".format(m["module"])
        ins += insModule(m, maxLen)
    # wire
    port = []
    wire = []
    for w in io:
        if w[0] in [i[0] for i in wire]:
            pass
        elif w[0] in [i[0] for i in port]:
            idx = [i[0] for i in port].index(w[0])
            if w[1] != port[idx][1]:
                port[idx][1] = "wire"
                wire.append(port[idx])
                del(port[idx])
        else:
            port.append(w)
    # generate text
        header = "/home/henson/rtl_momdule/rtl_header"        
        txt = readFile(header).format(top, "Script Auto Generate", "Top for %s"%top)
    if isModuleHead:
        txt += "\n\nmodule {0} (\n".format(top.rstrip(".v"))
        txt += "\n".join("{0:7}{1:8}{2},".format(i[1], "" if i[2]=="1" else "["+i[2]+"]", i[0]) for i in port)[:-1].replace("pre    []      ", "")
        txt += ");\n\n"
    
    txt += "\n".join("{0:7}{1:8}{2},".format(i[1], "" if i[2]=="1" else "["+i[2]+"]", i[0]) for i in wire)[:-1]
    txt += ins
    txt += "\n\nendmodule"
    if isWrite:
        writeFile("module_instance.out", txt)
    # }}}



if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(usage)
        exit()
    
    instance(sys.argv[1], 0, 1)
    
    #f = [i.strip() for i in sys.argv[1].split(",")]
    #pkgTop("top_test.v", f, 1, 1)

        


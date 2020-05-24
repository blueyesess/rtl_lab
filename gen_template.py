#!/usr/bin/python
#========================================================================
# Project : CHD
# File    : gen_template.py
# Language: Python
# Author  : henson
# Date    : 2019-10-14
#========================================================================
# Descrip : Generate generic text template 
#========================================================================

import os, sys, datetime
sys.path.append("/home/henson/script")
from common import *
from instance import instance

class Template():
    def __init__(self):
        # Initialize {{{
        # Initial template
        self.header = "//"+"="*72 + "\n// Project : \n// File    : \n// Language: Verilog HDL\n// Author  : {0}\n// Date    : {1}\n//".format(os.getenv("USER"), datetime.date.today()) + "="*72+"\n// Descrip :\n//"+"="*72        
        self.space = " "*4

        # File block
        # For rtl template
        self.dumpWave = "/home/henson/rtl_momdule/dump_fsdb.v"
        self.simClk = "/home/henson/rtl_momdule/sim_clock.v"
        self.simRst = "/home/henson/rtl_momdule/rst.v"
        self.timescale = "/home/henson/rtl_momdule/timescale"
        self.header = "/home/henson/rtl_momdule/rtl_header"

        # File name define
        # for drive tab
        self.driveTab = "drive.tab"
        self.dcFile = "dc_initial.tcl"
        self.easyDcTemp = "/home/henson/rtl_momdule/easy_dc.tcl"
        self.proDcTemp = "/home/henson/rtl_momdule/pro_dc.tcl"
        # }}}

    # Generate RTL template
    # <mode>: design & tb
    # [cfg]: config cfg, if not specify, will generate a poor template
    # [isWrite]: wirte out template if True
    # Params list:
    # for common: NAME PROJ DESC 
    # for tb: INS  DUMP CLK  RST  INI 
    def genRtlTemp(self, mode, cfg="", isWrite=False):
        # return text {{{
        if cfg == "":
            txt = self.header
        else:
            paraDic = cparse(cfg)
            # Header
            txt = readFile(self.header).format(paraDic["PROJ"], os.getenv("USER"), paraDic["DESC"][1:-1])
        # design mode
        if mode == "design":
            txt += "\n\nmodule {0} \n\nendmodule".format(paraDic["NAME"][:paraDic["NAME"].find(".")]) 
        # tb mode
        elif mode == "tb":
            txt += "\n" + readFile(self.timescale)
            top = paraDic["NAME"][:paraDic["NAME"].find(".")]
            txt += "\n\nmodule {0};\n".format(top)             
            
            # Params elaborat, could add new paras below
            # instance module
            if paraDic["INS"] != "":
                print(paraDic["INS"])
                wir, ins, q = instance(paraDic["INS"], False, False)
                txt += "// instance module\n" + wir + "\n" + ins + "\n\n"
            # sim clock generator
            if  paraDic["CLK"] != "":
                txt += "// sim clock generator\n"
                clk =  paraDic["CLK"]
                if type(clk) == str:
                   clk = [clk] 
                for i in clk:
                     c, t = i.replace('"', "").split(" ")
                     tmp = readFile(self.simClk).replace("clk", c).replace("20", str(eval("%s/2.0"%t)))
                     txt += tmp + "\n"                    
            # reset generate
            if  paraDic["RST"] != "":
                txt += "// reset generate\n" 
                rst =  paraDic["RST"]
                if type(rst) == str:
                    rst = [rst]
                for i in rst:
                    r, t = i.replace('"', "").split(" ")
                    tmp = readFile(self.simRst).replace("rst", r).replace("20", t)
                    txt +=  tmp + "\n"
            # initial reg value
            if  paraDic["INI"] != "":
                txt += " // initial reg value\ninitial begin\n"
                ini =  paraDic["INI"]
                regLis = [i.replace("reg", "").replace(" ", "") for i in wir.split("\n") if i.find("reg")==0]
                for i in regLis:
                    if "]" in i:
                        tmp = i.split("]")
                        s = tmp[1][:-1]
                        bw = eval(tmp[0].replace("[", "").replace(":", "-")+"+1")
                        txt += self.space + "{0} = {1}'d{2};\n".format(s, bw, ini)
                    else:
                        txt += self.space + "{0} = 1'd{1};\n".format(i[:-1], ini)
                txt += "end\n\n"
            # dump wave
            if paraDic["DUMP"] != "":
                wav = readFile(self.dumpWave).replace("test.fsdb",paraDic["DUMP"]).replace("xxx", top)
                txt += "// dump wave\n" + wav + "\n"

            txt += "endmodule"
            if isWrite:
                writeFile(paraDic["NAME"], txt)
                log("Write out rtl file!", 0)
            return txt
        else:
            log("unknow mode specify, will quit", 2)
            exit()
            # }}}


    # Generate driver table for input port
    # <file>: specify rtl file to added
    # <dur>: total sim time will write out
    # <step>: time step 
    # output table as:
    # sig\time    0    10    20    30
    # axxxx(1)   32    23          
    # bxx(8)         1     0      1
    def genDriveTab(self, file, dur, step, isWrite=False):
        # return text {{{
        # tabDic: {signal: bitwidth}
        tabDic = {}
        wir, ins = instance(file, False, False)
        regLis = [i.replace("reg", "").replace(" ", "") for i in wir.split("\n") if i.find("reg")==0]
        for i in regLis:
            if "]" in i:
                tmp = i.split("]")
                s = tmp[1][:-1]
                bw = eval(tmp[0].replace("[", "").replace(":", "-")+"+1")
                tabDic[s] = bw
            else:
                tabDic[i] = "1"
        # gen talbe file
        maxLen = max(max(len(k)+len(str(v)) for k,v in tabDic.items()), len("sig/time"))
        txt = "\n"
        # heading
        txt += ("{0:<%s}" %maxLen).format("sig/time") + self.space +\
                self.space.join(str(s) for s in range(0,dur,step)) + "\n"
        # sign
        for s,b in tabDic.items():
            txt += ("{0:<%s}" %maxLen).format("%s(%s)"%(s[:-1],b)) + self.space +\
                self.space.join(" "*len(str(s)) for s in range(0,dur,step)) + "\n"
        
        if isWrite:
            writeFile(self.driveTab, txt)
            log("Write out drive table file.", 0)
        return txt
        # }}}
         
    # Generate dc tcl file with default library
    # <rtl>: specify which rtl file to read
    # [isWrite]: switch to write file
    # [tpt]: dc template to use
    def genDcTemp(self, rtl, isWrite=False, tpt="easy"):
        # {{{
        if tpt == "easy":
            tpt = self.easyDcTemp
        elif tpt == "pro":
            tpt = self.proDcTemp
        else:
            log("No specified template in genDcTemp", 2)
            exit()
        temp = readFile(tpt).replace("test.v", rtl)
        if isWrite:
            writeFile(self.dcFile, temp, 0, 1)
            log("Write out dc template file.", 0)
        #}}}


if __name__ == "__main__":
    # Parse argv {{{
    arg = argHead("This scritp would generate text template.", 
        "mode: rtl, syn, tab",
        mode="specify a mode to generate template. rtl -> config, syn -> verilog, tab -> drive table",
        file="specify a file to read.",
        dct="specify dc template to use. easy or pro"
        )
    mode = arg["mode"]
    file = arg["file"]
    dct = arg["dct"]

    if mode is None or file is None:
        log("Type -h for help")
        exit()
    t = Template()
    if mode == "rtl":
        t.genRtlTemp("tb", file, True)
    elif mode == "syn":
        if dct is None:
            t.genDcTemp(file, True)
        else:
            t.genDcTemp(file, True, dct)
            
    elif mode == "tab":
        t.genDriveTab(file, 150, 10, True)
    else:
        log("Invalid mode specifyed. type -h for help", 3)
    # }}}


    





#!/usr/bin/python
import sys
sys.path.append("/home/henson/script/rtl_lab")
sys.path.append("/home/henson/script")
from common import *
from gen_template import Template

class rtl_lab():
    def __init__(self):

        # tools commad
        self.simCmd = "vcs"
        self.synCmd = "dc_shell"
        
        # script
        self.makefile = "/home/henson/script/Makefile"

        # 
        self.genTemp = Template()

    # Generate RTL template
    # <mode>: design & tb
    # [file]: config file, if not specify, will generate a poor template
    def genRTLTemplate(self, mode, file=""):
        self.genTemp.genRtlTemp(mode, file, True)

    # Compile & sim

            
if __name__ == "__main__":
    r = rtl_lab()
    r.genTemplate( "tb", "lab.conf")


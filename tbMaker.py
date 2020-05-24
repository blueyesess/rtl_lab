#!/usr/bin/python3
#############################################################################
# Project:  XYM
# File:     tbMaker.py
# Athor:    Henson
# Descrp:   test bench generator 
#############################################################################
# Version: 0.1
# Initial version, genetor tb file in gui operation
#############################################################################

import io, gzip, os, re, math, sys
import tkinter as tk
from tkinter import filedialog
from tkinter.messagebox import showinfo
from tkinter import ttk
sys.path.append("/home/pi/Code/rtl_lab/common")
sys.path.append("/home/pi/Code/rtl_lab/tools")
from instance import instance
from common import readFile
from common import log
from common import convert

class TestBenchMaker:

    def __init__(self):
        # {{{    
        # Configurable parameter
        self.TITLE = "TestBenchMaker"
        self.WIDTH = 600
        self.HEIGHT = 700
        self.instance = "_ISTANCE"
        self.space = "  "

        # Inner flag 
        self.lastSignal = ""
        self.lastFlag = None
        self.lastEdit = None
        self._lasTtextList = []
        self._last2Signal = ["", ""]

        self.parseDic = {"input":[], "output":[]}   # {"input":[{"port":xxx, "bit":xxx, "isSet":xx}, {}], "output":[], "module":xxx, "top":xxx}
        self.dataDic = {}                           # {"signal":[{"time":xxx, "value":xxx}, {}]}

        self._tag = 0                   # 0: single, 1: custom, 2: case
        self._caseList = []             # caseList = [{name:xx, time:xx, text:xx}]
        self._testcaseText = []         # text for testcase after ensure in preview4case
        self._indexFlag = 0             # Flag for counting numbers of delete item
        self._offset = 0                # Flag for recording global offset
        self._isSet = []                # Flag for is set
        self._singleRecord = {}         # Flag for single set recording {port:{tag:xx, value:xx, ini:xx}}

        # record test bench code information
        # tbDic["single"]: a dict for single bit signal assignment, {"clk": xxx, "rst": xxx}
        # tbDic["case"]: string for test case text
        # tbDic["custom"]: string for custom input list
        # tbDic["ini"]: a list for initial value assignment, {port: value}
        self._tbDic = {"single": {}, "case": [], "custom": [], "ini": []}
        # }}}

    # Initial root gui
    def initialGUI(self):
        # Change tag when click tag button
        def changeTag(tag):
            # {{{
            frame3.pack_forget()                        # Clear current state
            frame4.pack_forget()
            frame5.pack_forget()
            if tag == 0:                                # Pack destination frame
                frame3.pack(fill=tk.X)                  # 0 for input frame
            elif tag == 1:                              # 1 for output frame
                frame4.pack(fill=tk.X)
            elif tag == 2:                              # 2 for other frame
                frame5.pack(fill=tk.X)
            # }}}

        # Change select mode in different tag
        def changeType(tag):                            # Clear current state
            # {{{
            singleSet.pack_forget()
            caseSet.pack_forget()
            customSet.pack_forget()
            self._tag = tag
            if tag == 0:                                # Change selctmode accroding to current frame
                singleSet.pack(side=tk.TOP, fill=tk.BOTH, expand=tk.YES, pady=5, padx=10)
                self.inputView["selectmode"] = tk.BROWSE
            elif tag == 1:
                customSet.pack(side=tk.TOP, fill=tk.BOTH, expand=tk.YES, pady=5, padx=10)
                self.inputView["selectmode"] = tk.BROWSE
            elif tag == 2:
                caseSet.pack(side=tk.TOP, fill=tk.BOTH, expand=tk.YES, pady=5, padx=10)
                self.inputView["selectmode"] = tk.EXTENDED
            # }}}
            
        # Get select items and record setting value
        def getSel(event=None):
            # {{{
            index = self.inputView.selection()
            desRadix = ["b", "o", "d", "h"][radixValue.get()]
            if len(index):
                index = int(convert(index[0][1:], "h", "d")) - 1
                self.lastSignal = self.parseDic["input"][index]["port"]
                bit = self.parseDic["input"][index]["bit"]
                char = "0" if defaultValue.get() == "0" else "1"
                value.set(str(bit) + "'{}".format(desRadix) + re.sub("[\dABCDEFabcdef]", defaultValue.get(), convert(bit * char, "b", desRadix)))
                self.updateData()
                self._last2Signal = [self._last2Signal[1], self.lastSignal]

                # Divide different function for every tag
                # tag == 0
                if self._tag == 0:
                    if clock.get() == toggle.get():
                        pass
                    elif clock.get() == "":
                        self._singleRecord[self._last2Signal[0]] = {"tag": "toggle", "value": toggle.get(), "ini": initalValue.get()}
                    elif toggle.get() == "":
                        self._singleRecord[self._last2Signal[0]] = {"tag": "clock", "value": clock.get(), "ini": initalValue.get()}

                    toggle.set("")
                    clock.set("")
                    initalValue.set("1'b0")
                    if not self._singleRecord.get(self.lastSignal, "") == "":
                        if self._singleRecord[self.lastSignal]["tag"] == "toggle":
                            toggle.set(self._singleRecord[self.lastSignal]["value"])
                        elif self._singleRecord[self.lastSignal]["tag"] == "clock":
                            clock.set(self._singleRecord[self.lastSignal]["value"])
                        initalValue.set(self._singleRecord[self.lastSignal]["ini"])

                # tag == 1
                elif self._tag == 1:
                    if self._customViewFlag.get(self.lastSignal, False) == False:
                        self._customViewFlag[self.lastSignal] = []
                    [self.customView.delete(i) for i in self.customView.get_children()]
                    self._offset = self._indexFlag
                    if self.dataDic.get(self.lastSignal, False) == False:
                        pass
                    else:
                        [customAdd(i["time"], i["value"], False) for i in self.dataDic[self.lastSignal]]
            else:
                value.set("1'b" + str(defaultValue.get()))
            # }}}

        # Change radix
        def changeRadix(*event):
            # {{{
            tmpSplit = value.get().split("'")
            curRadix = tmpSplit[-1][0]
            desRadix = ["b", "o", "d", "h"][radixValue.get()]
            bit = tmpSplit[0]
            curValue = "".join(tmpSplit[-1][1:].split("_"))
            if all(i.isdigit() or i in list("ABCDEFabcdef") for i in curValue):
                tmp = str(bit) + "'{}".format(desRadix) + convert(curValue, curRadix, desRadix)
                value.set(tmp)
            else:
                radixValue.set(["b", "o", "d", "h"].index(curRadix))
                showinfo(title="Error", message="Can't convert none digit char to other radix.")
            # }}}

        # Adjust value
        # <control>: up/down:"+/-"
        # <value>  : string
        # [step]   : default is 1
        def adjustValue(control, inputValue, step=1):
            # {{{
            value = inputValue.get()
            if value.find("'") > -1:
                tmpSplit = value.split("'")
                radix = tmpSplit[-1][0]
                bit = int(tmpSplit[0])
                value = "".join(tmpSplit[-1][1:].split("_"))
                s = sum((int(convert(value, radix, "d", False)), 1 * step if control == "+" else -1 * step))
                if s < 0:
                    conv = convert(bit * "1", "b", radix)
                else:
                    conv = convert(convert(str(s), "d", "b", False)[-1 * bit:], "b", radix)
                inputValue.set(str(bit) + "'{}".format(radix) + conv)
            else:
                inputValue.set(sum((int(value), 1 * step if control == "+" else -1 * step)))
            # }}}

        # Custom add button
        def customAdd(simTime, value, new=True):
            # {{{
            if self.lastSignal != "":
                signal = self.lastSignal
                if not self.dataDic.get(signal, False):
                    self.dataDic[signal] = []
                if new:
                    self.dataDic[signal].append({"time": simTime, "value": value})
                self.customView.insert("", tk.END, value=[signal, simTime, value])
                self._indexFlag += 1
            else:
                showinfo(title="Error", message="Please choose a signal first.")
            # }}}

        # Custom edit button
        def customEdit(simTime, value):
            # {{{
            index = self.customView.selection()
            signal = self.lastSignal
            if len(index) == 1:
                [self.customView.set(index, column=i, value=[signal, simTime, value][i]) for i in range(3)]
                offset = self._offset
                index = int(convert(index[0][1:], "h", "d")) - 1
                del self.dataDic[signal][index - offset - 1]
                self.dataDic[signal].insert(index, {"time": simTime, "value": value})
            else:
                showinfo(title="Error", message="Please choose a database to edit.")
            # }}}

        # Custom delete
        def customDelete():
            # {{{
            index = self.customView.selection()
            signal = self.lastSignal
            if len(index) == 1:
                self.customView.delete(index)
                index = int(convert(index[0][1:], "h", "d"))
                self._customViewFlag[signal].append(index)
                offset = self._offset
                for i in self._customViewFlag[signal]:
                    if index > i:
                        offset += 1
                del self.dataDic[signal][index - offset - 1]
            else:
                showinfo(title="Error", message="Please choose a database to delete.")
            # }}}

        # Submit and update
        def submit(tag, item):
        # {{{
            if tag == "case":
                self._tbDic["case"].append(item)
            elif tag == "custom":
                self._tbDic["custom"].append(item)
            elif tag == "single":
                self._tbDic["single"]["clk"] = item[0]
                self._tbDic["single"]["rst"] = item[1]
            for i in range(len(self.parseDic["input"])):
                if self.parseDic["input"][i]["port"] in self._isSet:
                    self.parseDic["input"][i]["isSet"] = "Yes"
            self._isSet.clear()
            self.updateData()
        # }}}

        # Submit for caseList
        def submit4caseList():
            # {{{
            itemLength = len(self._caseList)
            index = [self._caseView.item("I{:0>3}".format(convert(str(i), "d", "h")))["values"][0] for i in (1, itemLength + 1)]
            for i in range(len(self._caseList)):
                self._caseList[i]["time"] = index[i]
            textList = ["{}#{} \n".format(self.space, i["time"]) + i["text"] for i in self._caseList]
            self._testcaseText = []
            caseView = self.editor(caseSet, 20, "initial begin\n" + "\n".join(textList) + "end", None, lambda: submit("case", caseView.get(0.0, tk.END)), self._isSet.clear)
            # }}}

        # Submit for custom
        def submit4custom():
            # {{{
            codeList = []
            for port in [d["port"] for d in self.parseDic.get("input", [])]:
                if self.dataDic.get(port, False) != False:
                    self._isSet.append(port)
                    codeList.append("\n{}// {}".format(self.space, port))
                    for item in self.dataDic[port]:
                        codeList.append("{0}#{1}\n{0}{2} = {3};".format(self.space, item["time"], port, item["value"]))
            customView = self.editor(customItem3, 10, "initial begin\n" + "\n".join(codeList) + "\nend", None, lambda: submit("custom", customView.get(0.0, tk.END)), self._isSet.clear)
            # }}}

        # Submit for single
        def submit4single():
            # {{{
            getSel()
            clkList = []
            rstList = []
            for k, v in self._singleRecord.items():
                self._isSet.append(k)
                if v["tag"] == "clock":
                    clkList.append("# {}".format(k))
                    clkList.extend([
                        "always begin",
                        "{0}{1} = #{2} ~{1}".format(self.space, k, v["value"]),
                        "end"
                    ])
                elif v["tag"] == "toggle":
                    if "," in v["value"]:
                        f, s = v["value"].split(",")
                        rstList.append("{0}#{1} {2} = ~{2}".format(self.space, f, k))
                        rstList.append("{0}#{1} {2} = ~{2}".format(self.space, s, k))
                    else:
                        rstList.append("{0}#{1} {2} = ~{2}".format(self.space, v["value"], k))
                self._tbDic["ini"].append({k: v["ini"]})

            previewText = "\n".join(clkList + [
                "initial begin",
                "\n".join(["{}{} = {};".format(self.space, list(i.keys())[0], list(i.values())[0]) for i in self._tbDic["ini"]]),
                "\n".join(rstList),
                "end"
            ])

            singleView = self.editor(singleSub1, 10, previewText, None,
                                     lambda: submit("single", [clkList,rstList]), self._isSet.clear)
            # }}}

        window = tk.Tk()
        window.title(self.TITLE)

        # Place GUI on the center of screen
        self.ws = window.winfo_screenwidth()
        self.hs = window.winfo_screenheight()
        x = (self.ws / 2) - (self.WIDTH / 2)
        y = (self.hs / 2) - (self.HEIGHT / 2)
        window.geometry('%dx%d+%d+%d' % (self.WIDTH, self.HEIGHT, x, y))

        # File directory
        frame = tk.Frame(window)
        frame.pack(fill=tk.X)
        dir = tk.StringVar()
        tk.Label(frame, text="Select a RTL File:", bg="white").grid(row=0, column=0, padx=5, pady=10)
        tk.Entry(frame, textvariable=dir, width=30, bd=4, bg="white").grid(row=0, column=1, padx=5, pady=10)
        tk.Button(frame, text="Open", command=lambda: dir.set(filedialog.askopenfilename())).grid(row=0, column=2, padx=5, pady=10)

        # Extract RTL
        tk.Button(frame, text="Extract", command=lambda: self.extractRTL(dir.get())).grid(row=0, column=3)
        # tk.Button(frame, text="Extract", command=lambda: self.extractRTL(r"C:/Users/sjkpy/Desktop/SR.v")).grid(row=0,
        #                                                                                                        column=3,
        #                                                                                                        padx=5)

        # Tag: 0 --> input; 1 --> output; 2 --> other
        frame2 = tk.Frame(window)
        frame2.pack(fill=tk.Y, pady=10)
        tag = tk.IntVar()
        tagWidth = 23
        tk.Radiobutton(frame2, text="Input", command=lambda: changeTag(0), variable=tag, width=tagWidth, value=0, bd=1,
                       indicatoron=0).grid(column=0, row=1)
        tk.Radiobutton(frame2, text="Output", command=lambda: changeTag(1), variable=tag, width=tagWidth, value=1, bd=1,
                       indicatoron=0).grid(column=1, row=1)
        tk.Radiobutton(frame2, text="Other", command=lambda: changeTag(2), variable=tag, width=tagWidth, value=2, bd=1,
                       indicatoron=0).grid(column=2, row=1)

        # frame3 --> Input
        # Input info list
        frame3 = tk.Frame(window, height=300, bg="white")
        frame3.pack(side=tk.TOP, fill=tk.X)
        subFrame3 = tk.Frame(frame3, bg="white")
        subFrame3.pack(side=tk.TOP, fill=tk.X)
        tk.Label(subFrame3, text="-" * 100).pack(side=tk.TOP, anchor=tk.W)
        self.inputView = self.view(subFrame3, ["Bit", "Input", "Set"], 10, 7, None)
        self.inputView["selectmode"] = tk.BROWSE
        self.inputView.bind("<ButtonRelease-1>", getSel)
        self.inputView.pack(side=tk.TOP, anchor=tk.NW, fill=tk.X, expand=tk.YES)

        # Input setting frame
        width = 10
        frameInputSet = tk.Frame(frame3, bg="white")
        frameInputSet.pack(side=tk.TOP, fill=tk.BOTH, expand=tk.YES)
        tk.Label(frameInputSet, text="  Input Setting").grid(row=0, column=0, pady=5)
        tk.Label(frameInputSet, text="  Signal Type", width=width).grid(row=1, column=0)
        # Tpye: 0 --> Single; 1 --> Custom; 2 --> Case
        type = tk.IntVar()
        tk.Radiobutton(frameInputSet, text="Single", variable=type, value=0, command=lambda: changeType(0), bd=1,
                       indicatoron=0, width=width).grid(row=1, column=1, padx=10)
        tk.Radiobutton(frameInputSet, text="Custom", variable=type, value=1, command=lambda: changeType(1), bd=1,
                       indicatoron=0, width=width).grid(row=1, column=2, padx=10)
        tk.Radiobutton(frameInputSet, text="Case", variable=type, value=2, command=lambda: changeType(2), bd=1,
                       indicatoron=0, width=width).grid(row=1, column=3, padx=10)

        # single setting
        initalValue = tk.StringVar()
        initalValue.set("1'b0")
        clock = tk.StringVar()
        toggle = tk.StringVar()
        singleSet = tk.Frame(frame3, bg="white")
        singleSet.pack(side=tk.TOP, fill=tk.BOTH, expand=tk.YES, pady=5, padx=10)
        singleSub1 = tk.Frame(singleSet, bg="white")
        singleSub1.pack(side=tk.TOP, fill=tk.BOTH, expand=tk.YES, pady=10, padx=10)
        tk.Label(singleSub1, text="Initial Value").grid(row=0, column=0, pady=5)
        tk.Radiobutton(singleSub1, text="1'b0", variable=initalValue, value="1'b0").grid(row=0, column=1, padx=5)
        tk.Radiobutton(singleSub1, text="1'b1", variable=initalValue, value="1'b1").grid(row=0, column=2, padx=5)
        tk.Label(singleSub1, text="Clock").grid(row=1, column=0, pady=5, padx=10)
        tk.Label(singleSub1, text="Half").grid(row=2, column=0, pady=5, padx=10)
        tk.Entry(singleSub1, textvariable=clock, width=10, bd=2, bg="white").grid(row=2, column=1)
        tk.Label(singleSub1, text="Reset").grid(row=3, column=0, pady=5, padx=10)
        tk.Label(singleSub1, text="Toggle").grid(row=4, column=0, pady=5, padx=10)
        tk.Entry(singleSub1, textvariable=toggle, width=10, bd=2, bg="white").grid(row=4, column=1)
        tk.Button(singleSet, text="Submit", command=submit4single).pack(side=tk.TOP)
        tk.Button(singleSet, text="test", command=self.genCode).pack(side=tk.TOP)

        # Custom setting
        defaultValue = tk.StringVar()
        defaultValue.set("0")
        radixValue = tk.IntVar()
        radixValue.set(0)
        customSet = tk.Frame(frame3, bg="white")
        # customSet.pack(side=tk.TOP, fill=tk.BOTH, expand=tk.YES, pady=5, padx=10)
        # Custom item1
        customItem1 = tk.Frame(customSet, bg="white")
        customItem1.pack(side=tk.TOP, fill=tk.BOTH, expand=tk.YES, pady=5, padx=10)
        # Radix 0 --> b, 1 --> o, 2 --> d, 3 --> h
        tk.Label(customItem1, text="Radix").grid(row=0, column=0, pady=5, padx=1, sticky=tk.W)
        tk.Radiobutton(customItem1, text="Binary", variable=radixValue, value=0, command=changeRadix).grid(row=0,
                                                                                                           column=1,
                                                                                                           sticky=tk.W)
        tk.Radiobutton(customItem1, text="Octal", variable=radixValue, value=1, command=changeRadix).grid(row=0,
                                                                                                          column=2,
                                                                                                          sticky=tk.W)
        tk.Radiobutton(customItem1, text="Decimal", variable=radixValue, value=2, command=changeRadix).grid(row=0,
                                                                                                            column=3,
                                                                                                            sticky=tk.W)
        tk.Radiobutton(customItem1, text="Hexadecimal", variable=radixValue, value=3, command=changeRadix).grid(row=0,
                                                                                                                column=4,
                                                                                                                sticky=tk.W)
        # Custom value
        value = tk.StringVar()
        value.set("1'b0")
        simTime = tk.StringVar()
        simTime.set("0")
        tk.Label(customItem1, text="Default").grid(row=1, column=0, pady=5, padx=1, sticky=tk.W)
        tk.Radiobutton(customItem1, text="default 0", variable=defaultValue, value="0", command=getSel).grid(row=1,
                                                                                                             column=1,
                                                                                                             padx=5,
                                                                                                             sticky=tk.W)
        tk.Radiobutton(customItem1, text="default 1", variable=defaultValue, value="1", command=getSel).grid(row=1,
                                                                                                             column=2,
                                                                                                             padx=5,
                                                                                                             sticky=tk.W)
        tk.Radiobutton(customItem1, text="default z", variable=defaultValue, value="z", command=getSel).grid(row=1,
                                                                                                             column=3,
                                                                                                             padx=5,
                                                                                                             sticky=tk.W)
        tk.Radiobutton(customItem1, text="default x", variable=defaultValue, value="x", command=getSel).grid(row=1,
                                                                                                             column=4,
                                                                                                             padx=5,
                                                                                                             sticky=tk.W)
        # Custom item2
        tk.Label(customSet, text="-" * 90).pack(side=tk.TOP, anchor=tk.W)
        customItem2 = tk.Frame(customSet, bg="white")
        customItem2.pack(side=tk.TOP, fill=tk.BOTH, expand=tk.YES, padx=10)
        tk.Label(customItem2, text="Time").grid(row=2, column=0, pady=5, padx=0)
        tk.Entry(customItem2, textvariable=simTime, width=5, bd=2, bg="white", justify=tk.RIGHT).grid(row=2, column=1,
                                                                                                      padx=5)
        tk.Button(customItem2, text="+", width=1, height=1, bd=1, bg="white",
                  command=lambda: adjustValue("+", simTime)).grid(row=2, column=2, pady=5, padx=0)
        tk.Button(customItem2, text="-", width=1, height=1, bd=1, bg="white",
                  command=lambda: adjustValue("-", simTime)).grid(row=2, column=3, pady=5, padx=0)
        tk.Label(customItem2, text="Time").grid(row=2, column=0, pady=5, padx=0)
        tk.Label(customItem2, text="        ").grid(row=2, column=4, pady=5, padx=0)
        tk.Label(customItem2, text="Value").grid(row=2, column=5, pady=5, padx=0)
        tk.Entry(customItem2, textvariable=value, width=25, bd=2, bg="white", justify=tk.RIGHT).grid(row=2, column=6,
                                                                                                     padx=5)
        tk.Button(customItem2, text="+", width=1, height=1, bd=1, bg="white",
                  command=lambda: adjustValue("+", value)).grid(row=2, column=7, pady=5, padx=0)
        tk.Button(customItem2, text="-", width=1, height=1, bd=1, bg="white",
                  command=lambda: adjustValue("-", value)).grid(row=2, column=8, pady=5, padx=0)
        # Custom item3
        # Custom signal
        customItem3 = tk.Frame(customSet, bg="white")
        customItem3.pack(side=tk.TOP, fill=tk.BOTH, expand=tk.YES, padx=10)
        tk.Label(customItem3, text="").pack(side=tk.TOP, anchor=tk.W)
        # Flag for recording signal index that is deleted
        self._customViewFlag = {}
        self.customView = self.view(customItem3, ["Signal", "Time", "Value"], 120, 5, False)
        self.customView.pack(side=tk.LEFT, anchor=tk.NW)
        tk.Button(customItem3, text="Add", width=6, bd=1, bg="white",
                  command=lambda: customAdd(simTime.get(), value.get())).pack(
            side=tk.TOP, anchor=tk.NE, padx=10, pady=5)
        tk.Button(customItem3, text="Edit", width=6, bd=1, bg="white",
                  command=lambda: customEdit(simTime.get(), value.get())).pack(
            side=tk.TOP, anchor=tk.NE, padx=10, pady=5)
        tk.Button(customItem3, text="Delete", width=6, bd=1, bg="white", command=customDelete).pack(side=tk.TOP,
                                                                                                    anchor=tk.NE,
                                                                                                    padx=10, pady=5)
        tk.Button(customItem3, text="Submit", width=6, bd=1, bg="white", command=submit4custom).pack(side=tk.TOP,
                                                                                                     anchor=tk.NE,
                                                                                                     padx=10, pady=5)

        # case setting
        caseSet = tk.Frame(frame3, bg="white")
        # caseSet.pack(side=tk.TOP, fill=tk.BOTH, expand=tk.YES, pady=5, padx=10)
        # sub case set1
        subCaseSet1 = tk.Frame(caseSet, bg="white")
        subCaseSet1.pack(side=tk.TOP, fill=tk.BOTH, expand=tk.YES)
        tk.Label(subCaseSet1, text=" " * 2).pack(side=tk.LEFT)
        tk.Label(subCaseSet1, text="Colum:").pack(side=tk.LEFT, pady=20)
        maxColum = tk.Label(subCaseSet1, width=1, text=5)
        maxColum.pack(side=tk.LEFT, padx=5)
        tk.Button(subCaseSet1, text="+", width=1, bd=1,
                  command=lambda: maxColum.config(text=maxColum["text"] + 1)).pack(side=tk.LEFT)
        tk.Button(subCaseSet1, text="-", width=1, bd=1,
                  command=lambda: maxColum.config(text=maxColum["text"] - 1)).pack(side=tk.LEFT)

        tk.Label(subCaseSet1, text=" " * 2).pack(side=tk.LEFT)
        tk.Label(subCaseSet1, text="Row:").pack(side=tk.LEFT)
        maxRow = tk.Label(subCaseSet1, width=2, text=15)
        maxRow.pack(side=tk.LEFT, padx=5)
        tk.Button(subCaseSet1, text="+", width=1, bd=1,
                  command=lambda: maxRow.config(text=maxRow["text"] + 5)).pack(side=tk.LEFT)
        tk.Button(subCaseSet1, text="-", width=1, bd=1,
                  command=lambda: maxRow.config(text=maxRow["text"] - 5)).pack(side=tk.LEFT)

        clockStep = tk.StringVar()
        clockStep.set("10")
        tk.Label(subCaseSet1, text=" " * 2).pack(side=tk.LEFT)
        tk.Label(subCaseSet1, text="Clock Step:").pack(side=tk.LEFT)
        clockComBox = ttk.Combobox(subCaseSet1, textvariable=clockStep, justify=tk.RIGHT, width=4)
        clockComBox["values"] = ('1', '10', '100', '1000')
        clockComBox.pack(side=tk.LEFT, padx=5)
        tk.Label(subCaseSet1, text=" " * 2).pack(side=tk.LEFT)
        tk.Button(subCaseSet1, text="Editor", bd=2, width=15,
                  command=lambda: self.caseGenerator(maxColum["text"], maxRow["text"], clockStep)).pack(side=tk.LEFT,
                                                                                                        padx=5)
        tk.Label(caseSet, text="-" * 100).pack(side=tk.TOP)
        subCaseSet2 = tk.Frame(caseSet, bg="white")
        subCaseSet2.pack(side=tk.TOP, fill=tk.BOTH, expand=tk.YES, pady=10)
        self._caseView = self.view(subCaseSet2, ["Time", "Case"], 20, 5)

        tk.Button(subCaseSet2, text="Submit", width=25, bd=1,
                  command=submit4caseList).pack(padx=10, pady=10)

        # frame4 --> Output
        frame4 = tk.Frame(window, height=350, bg="white")

        tk.Label(frame4, text="-"*100).pack(anchor=tk.NW)
        self.outputView = self.view(frame4, ["Bit", "Output", "Set"], 10, 7, None)
        self.outputView["selectmode"] = tk.BROWSE
        self.outputView.bind("<ButtonRelease-1>", getSel)
        self.outputView.pack(side=tk.TOP, anchor=tk.NW, fill=tk.X, expand=tk.YES)

        # frame5 --> Other
        frame5 = tk.Frame(window, height=350, bg="yellow")

        window.mainloop()

    # Pop a simple editor, size is same as master frame size
    # output var need a global type
    def editor(self, master, height=None, insert=None, stringVar=None, funcY=None, funcN=None):

        # Ensure if save edit data or not
        def ensure(opt="n"):
            global outputVar
            if opt == "y":
                self.lastEdit = text.get(0.0, tk.END)
                if not stringVar is None:
                    while self.lastEdit.endswith("\n"):
                        self.lastEdit = self.lastEdit[:-1]
                    stringVar.set(self.lastEdit)
                if not funcY is None:
                    funcY()
            else:
                self.lastEdit = None
                if not funcN is None:
                    funcN()

            [i.destroy() for i in frame.winfo_children()]
            frame.destroy()

        m = master.winfo_geometry()
        masterSize = list(map(int, m[:m.find("+")].split("x")))
        frame = tk.Frame(master, width=masterSize[0], height=masterSize[1])
        frame.place(x=0, y=0)
        text = tk.Text(frame, height=int(masterSize[1] * 0.06) if height is None else height,
                       width=int(masterSize[0] * 0.13))
        if not insert is None:
            text.insert(tk.END, insert)
        text.focus_force()
        yScroll = tk.Scrollbar(frame, orient=tk.VERTICAL, command=text.yview)
        yScroll.pack(side=tk.RIGHT, fill=tk.Y)
        text.config(yscrollcommand=yScroll.set)
        text.pack(side=tk.TOP, fill=tk.BOTH)
        subFrame = tk.Frame(frame)
        subFrame.pack(side=tk.TOP)
        buttonWidth = int(masterSize[0] * 0.13 * 0.2)
        tk.Button(subFrame, text=u"?", width=buttonWidth, bd=1, fg="red", command=ensure).pack(side=tk.RIGHT, padx=2)
        tk.Button(subFrame, text=u"?", width=buttonWidth, bd=1, fg="green", command=lambda: ensure("y")).pack(
            side=tk.RIGHT, padx=2)
        return text

    # View tree
    # master: master will place on
    # rowList: for heading item messange
    # columwidth: specify the cloum width
    # height: specify treeview height
    # click treeview will open edit box, need to manully get database from treeview
    def view(self, master, rowList, columwidth, height, click2edit=True):

        def edit(event):
            nonlocal lastEdit
            select = treeView.selection()
            if select != ():
                if not lastEdit is None:
                    try:
                        [i.destroy() for i in lastEdit.winfo_children()]
                        lastEdit.destroy()
                    except:
                        pass

                rowVar = tk.StringVar()
                column = treeView.identify_column(event.x)
                content = treeView.item(select)["values"][int(column.replace("#", "")) - 1]
                editor = self.editor(treeView, 1, content, rowVar,
                                     lambda: treeView.set(select, column=column, value=rowVar.get()))
                editor.config(width=10)
                x, y = (treeView.bbox(select, column)[:2])
                lastEdit = editor.master
                editor.master.place(x=x, y=y)

        lastEdit = None
        treeView = ttk.Treeview(master, height=height, show="headings", column=rowList)
        treeYScroll = tk.Scrollbar(master, orient=tk.VERTICAL, command=treeView.yview)
        treeXScroll = tk.Scrollbar(master, orient=tk.HORIZONTAL, command=treeView.xview)
        treeXScroll.pack(side=tk.BOTTOM, fill=tk.X)
        treeYScroll.pack(side=tk.LEFT, fill=tk.Y)
        treeView.config(yscrollcommand=treeYScroll.set, xscrollcommand=treeXScroll.set)
        treeView.pack(side=tk.TOP, fill=tk.BOTH)
        [treeView.column(i, width=columwidth, anchor='center') for i in rowList]
        [treeView.heading(i, text=i) for i in rowList]
        if click2edit:
            treeView.bind('<Double-1>', edit)
        return treeView

    # Generator for test case setting
    def caseGenerator(self, maxColums, maxRow, intialClockStep):

        # Add a row below tree view
        def addRow():
            self._rowIndex = self._rowIndex + 1
            conv = convert(str(self._rowIndex), "d", "h", None)
            for i in conv:
                if i.isalpha() and i.isupper() == False:
                    conv = conv.replace(i, i.upper())
            self._rowList.append("I{:0>3}".format(conv))
            step = clockStep.get()
            caseList[0].append(len(self._rowList))
            caseList[1].append(step)
            [i.append("") for i in caseList[2:]]
            treeView.insert("", tk.END, value=[i[-1] for i in caseList])

        # Delete row selected
        def delRow():
            if index == "":
                showinfo(title="Error", message="Please choose a row to delete.", parent=top)
            else:
                treeView.delete(index)
                self._rowList[self._rowList.index(index)] = ""

        # Edit item which displays on tree view by double click
        def edit(event):

            # Ensure if save edit data or not
            def ensure(opt="n"):
                if opt == "y":
                    treeView.set(select, column=column, value=text.get())
                [i.destroy() for i in self.lastFlag.winfo_children()]
                self.lastFlag.destroy()
                self.lastFlag = None

            # Dectect input text and split if need
            def detectText(event):
                input = event.char
                if input == "\r":
                    ensure("y")
                elif column != "#1":
                    curText = text.get().replace("_", "")
                    try:
                        splitText = curText.split("'")
                        bit = splitText[0]
                        radix = splitText[1][0]
                        content = splitText[1][1:] + str(input)
                    except IndexError:
                        pass
                    else:
                        curLen = len(content)
                        bitWidthLimit = math.ceil(int(bit) / {"b": 1, "o": 3, "d": 4, "h": 4}[radix])

                        # Detect input number bit width more than limit
                        if curLen > bitWidthLimit:
                            content = content[:-1]
                            text.delete(0, tk.END)
                            text.insert(tk.END, bit + "'" + radix + content[:-1])
                            text.focus_force()
                        # Detect input content if need to split
                        if split.get() == "YES" and curLen > 4:
                            content = convert(content)
                        text.delete(0, tk.END)
                        text.insert(tk.END, bit + "'" + radix + content[:-1])
                        text.focus_force()

            select = treeView.selection()
            if select != ():
                column = treeView.identify_column(event.x)
                # row = treeView.identify_row(event.y)
                if not self.lastFlag is None:
                    try:
                        [i.destroy() for i in self.lastFlag.winfo_children()]
                        self.lastFlag.destroy()
                    except tk.TclError:
                        pass
                content = treeView.item(select)["values"][int(column.replace("#", "")) - 1]
                if insertBit.get() == "YES" and content == "":
                    content = ("{}'{}".format(bitList[int(column.replace("#", "")) - 3], radix.get()))
                editFrame = self.lastFlag = tk.Frame(top)
                text = tk.Entry(editFrame, width=int(columWidth * 0.10))
                text.pack(side=tk.LEFT)
                text.insert(tk.END, content)
                text.focus_force()
                tk.Button(editFrame, text=u"?", width=1, fg="red", command=ensure).pack(side=tk.RIGHT)
                tk.Button(editFrame, text=u"?", width=1, fg="green", command=lambda: ensure("y")).pack(side=tk.RIGHT)
                x, y = (treeView.bbox(select, column)[:2])
                editFrame.place(x=x + 17, y=y + 10)
                text.bind("<Key>", detectText)

        # Preview testcase content
        def preview():
            while "" in self._rowList:
                self._rowList.remove("")

            simTime = 0
            self._lasTtextList = []
            for row in self._rowList:
                rowText = treeView.item((row,))["values"]
                simTime += int(rowText[1])
                if not min(i == "" for i in rowText[2:]) == 1:
                    self._lasTtextList.append("    #{}".format(simTime))
                    for i in range(len(rowText[2:])):
                        if rowText[2:][i] != "":
                            port = signals[i]
                            value = rowText[2:][i]
                            self._lasTtextList.append("    {} = {};".format(port, value))

            # case information
            if block.get() == "begin_end":
                self._lasTtextList = ["{}begin".format(self.space)] + self._lasTtextList + ["{}end".format(self.space)]
            else:
                self._lasTtextList = ["{}fork".format(self.space)] + self._lasTtextList + ["{}join".format(self.space)]

            self._lasTtextList.insert(0, "{}// {}".format(self.space, caseName.get()))
            self.editor(top, None, "\n".join(self._lasTtextList), None)

        # Submit testcase
        def submit():
            if self.lastEdit is None:
                showinfo(title="Error", message="Please check preview", parent=top)
            else:
                self._caseList.append({"name": caseName.get(), "time": "0", "text": self.lastEdit})
                self.lastEdit = None

                # Update UI case box
                for i in range(len(self.parseDic["input"])):
                    if self.parseDic["input"][i]["port"] in self._isSet:
                        self.parseDic["input"][i]["isSet"] = "Yes"
                self._isSet.clear()
                self.updateData()
                self._caseView.insert("", tk.END, value=[self._caseList[-1]["time"], self._caseList[-1]["name"]])
                top.destroy()

        # Create a float window for canvas
        def flyWindow():
            ##################
            # Float selection for test
            ##################
            def move(event):
                x, y = int(flyWin.winfo_geometry().split("+")[1]), int(flyWin.winfo_geometry().split("+")[2])
                if event.keysym == "Up":
                    flyWin.place(x=x, y=y - 25)
                elif event.keysym == "Down":
                    flyWin.place(x=x, y=y + 25)
                elif event.keysym == "Left":
                    flyWin.place(x=x - columWidth, y=y)
                elif event.keysym == "Right":
                    flyWin.place(x=x + columWidth, y=y)
                column = treeView.identify_column(int(x * 1.5))
                row = treeView.identify_row(int(y * 1.5))

            flyWin = tk.Frame(treeView, width=columWidth, height=25, background="")
            flyWin.pack_propagate(0)
            tk.Canvas(flyWin, background="blue", height=2).pack(side=tk.TOP, fill=tk.X)
            tk.Canvas(flyWin, background="blue", height=2).pack(side=tk.BOTTOM, fill=tk.X)
            tk.Canvas(flyWin, background="blue", width=2).pack(side=tk.LEFT, fill=tk.Y)
            tk.Canvas(flyWin, background="blue", width=2).pack(side=tk.RIGHT, fill=tk.Y)
            flyWin.place(x=0, y=25)
            top.bind("<Key>", move)
            ############################################

        index = self.inputView.selection()
        index = [int(convert(i[1:], "h", "d")) - 1 for i in index]
        if index == ():
            showinfo(title="Error", message="Please select a input.")
            return None
        # caseList: Save test case infomation in list
        #           time s1  s2      --> 2D grid
        #             0    1   2
        #            {[], [], [],}
        # Initial value
        caseList = []
        # Record row item
        self._rowIndex = 0
        self._rowList = []
        bitList = [self.parseDic["input"][i]["bit"] for i in index]
        columWidth = 120
        columNum = min((len(index), maxColums))
        #          sim time          port          scroll item  num
        width = columWidth + columWidth * columNum + 20 + 330 + 35
        height = 450
        top = tk.Toplevel()
        x = (self.ws / 2) - (width / 2)
        y = (self.hs / 2) - (height / 2)
        top.geometry('%dx%d+%d+%d' % (width, height, x, y))
        top.title("TestCaseGenerator")

        # Frame2
        gap = 3
        frame2 = tk.Frame(top, bg="white")
        frame2.pack(side=tk.RIGHT, anchor=tk.NW, padx=20, fill=tk.X)
        tk.Label(frame2, text="_" * 50).pack(side=tk.TOP, fill=tk.X)
        tk.Label(frame2, text="ITEM").pack(side=tk.TOP, fill=tk.X)
        tk.Label(frame2, text="-" * 50).pack(side=tk.TOP, fill=tk.X)

        caseName = tk.StringVar()
        clockStep = tk.StringVar()
        insertBit = tk.StringVar()
        split = tk.StringVar()
        radix = tk.StringVar()
        block = tk.StringVar()
        caseName.set("Test Case")
        clockStep.set(intialClockStep.get())
        insertBit.set("YES")
        split.set("YES")
        radix.set("b")
        block.set('begin_end')

        # sub frame1
        subFram1 = tk.Frame(frame2, bg="white")
        subFram1.pack(side=tk.TOP, fill=tk.X)
        tk.Label(subFram1, text="Case Name:").grid(row=0, column=0, sticky=tk.W, pady=gap)
        caseNameText = tk.Label(subFram1, textvariable=caseName)
        caseNameText.grid(row=0, column=1, pady=gap, columnspan=2)
        caseNameText.bind("<Button-1>", lambda x: self.editor(subFram1, 1, caseName.get(), caseName))

        tk.Label(subFram1, text="Clock Step:").grid(row=1, column=0, sticky=tk.E, pady=gap)
        clockComBox = ttk.Combobox(subFram1, textvariable=clockStep, justify=tk.RIGHT, width=4)
        clockComBox["values"] = ('1', '10', '100', '1000')
        clockComBox.grid(row=1, column=1, padx=20, pady=gap)

        tk.Label(subFram1, text="Bit:").grid(row=1, column=2, sticky=tk.E, pady=gap)
        tk.Button(subFram1, textvariable=insertBit, justify=tk.RIGHT, width=5, bd=1,
                  command=lambda: insertBit.set("NO" if insertBit.get() == "YES" else "YES")).grid(row=1, column=3,
                                                                                                   padx=20, pady=gap)

        tk.Label(subFram1, text="Radix:").grid(row=3, column=0, sticky=tk.E, pady=gap)
        radixComBox = ttk.Combobox(subFram1, textvariable=radix, justify=tk.RIGHT, width=4, state="readonly")
        radixComBox["values"] = ('b', 'o', 'd', 'h')
        radixComBox.grid(row=3, column=1, padx=20, pady=gap)

        tk.Label(subFram1, text="Split:").grid(row=3, column=2, sticky=tk.E, pady=gap)
        tk.Button(subFram1, textvariable=split, justify=tk.RIGHT, width=5, bd=1,
                  command=lambda: split.set("NO" if split.get() == "YES" else "YES")).grid(row=3, column=3, padx=20,
                                                                                           pady=gap)

        tk.Label(subFram1, text="Block:").grid(row=4, column=0, sticky=tk.E, pady=gap)
        tk.Button(subFram1, textvariable=block, justify=tk.RIGHT, width=10, bd=1,
                  command=lambda: block.set("fork_join" if block.get() == "begin_end" else "begin_end")).grid(row=4,
                                                                                                              column=1,
                                                                                                              padx=20,
                                                                                                              pady=gap,
                                                                                                              columnspan=2)
        tk.Label(frame2, text="-" * 50).pack(side=tk.TOP, fill=tk.X, pady=gap)

        # sub frame2
        subFrame2 = tk.Frame(frame2, bg="white")
        subFrame2.pack(side=tk.TOP, fill=tk.X)
        tk.Label(subFrame2, text="Edit:", width=8).grid(row=0, column=0)
        tk.Button(subFrame2, text="Add", width=8, command=addRow, bd=1).grid(row=0, column=1, padx=10)
        tk.Button(subFrame2, text="Delete", width=6, command=delRow, bd=1).grid(row=0, column=2, padx=10)
        tk.Label(frame2, text="-" * 50).pack(side=tk.TOP, fill=tk.X, pady=10)
        tk.Button(frame2, text="Preview", bd=1, command=preview).pack(fill=tk.X, pady=5)
        tk.Button(frame2, text="Submit", bd=1, command=submit).pack(fill=tk.X, pady=5)
        tk.Button(frame2, text="Cancel", bd=1, command=lambda: top.destroy()).pack(fill=tk.X, pady=5)

        # Frame1
        frame1 = tk.Frame(top, bg="white", width=columWidth + columWidth * columNum + 20)
        frame1.pack(side=tk.LEFT, anchor=tk.NW)
        signals = tuple(self.parseDic["input"][i]["port"] for i in index)
        self._isSet = list(signals)
        columns = ("Num", "Time") + signals
        caseList = [[] for i in columns]
        treeView = ttk.Treeview(frame1, height=18, show="headings", columns=columns)
        treeYScroll = tk.Scrollbar(frame1, orient=tk.VERTICAL, command=treeView.yview)
        treeXScroll = tk.Scrollbar(frame1, orient=tk.HORIZONTAL, command=treeView.xview)
        treeXScroll.pack(side=tk.BOTTOM, fill=tk.X)
        treeYScroll.pack(side=tk.LEFT, fill=tk.Y)
        treeView.config(yscrollcommand=treeYScroll.set, xscrollcommand=treeXScroll.set)
        treeView.pack(side=tk.TOP, fill=tk.BOTH, pady=15)
        treeView.column("Num", width=35, anchor='center')
        treeView.column("Time", width=columWidth, anchor='center')
        [treeView.column(i, width=columWidth, anchor='center') for i in signals]
        treeView.heading("Time", text="Time")
        treeView.heading("Num", text="Num")
        [treeView.heading(i, text=i) for i in signals]
        treeView.bind('<Double-1>', edit)
        [addRow() for i in range(maxRow)]

        top.mainloop()

    # Excute RTL extract
    # self.parseDic = {"input":[{"port":xxx, "bit":xxx, "isSet":False}, {}], "output":[], "module":xxx, "top":xxx}
    def extractRTL(self, dir):
        if os.path.exists(dir):
            code = readFile(dir)
            comment = re.compile("/\*.*?\*/\n", re.S)
            code = re.sub(comment, "", code)
            code = re.sub("//.*\n", "", code)

            # self.parseDic = {"input":[{"port":xxx, "bit":xxx}, {}], "output":[], "module":xxx, "top":xxx}
            # Module name
            self.parseDic["input"] = []
            self.parseDic["output"] = []
            
            wir, ins, dic = instance(dir)
            self.parseDic["module"] = dic["module"]
            self.parseDic["top"] = ins
            for i in dic["io"]:
                n, d, b = i
                self.parseDic[d].append({"port":n, "bit":b, "isSet":""})

            log(self.parseDic)

            # Upddate UI
            self._inputNum = len(self.parseDic["input"])
            self._outputNum = len(self.parseDic["output"])
            [self.inputView.insert("", tk.END, value=[d["bit"], d["port"], d["isSet"]]) for d in self.parseDic["input"]]
            [self.outputView.insert("", tk.END, value=[d["bit"], d["port"], d["isSet"]]) for d in self.parseDic["output"]]
            self.updateData()
        else:
            showinfo(title="Error", message="File {} is not exists, please choose the correct path.".format(dir))

    # Generate RTL code
    def genCode(self):
        # print(self._tbDic)
        self._tbDic = {'single': {'clk': ['# we_i', 'always begin', '  we_i = #1 ~we_i', 'end'], 'rst': []}, 'case': ["initial begin\n  #0 \n  // Test Case\n  begin\n    #10\n    rd_i = 1'b1;\n    #40\n    data_i = 32'b22;\n  end\nend\n", "initial begin\n  #0 \n  // Test Case\n  begin\n    #10\n    rd_i = 1'b1;\n    #40\n    data_i = 32'b22;\n  end\nend\n"], 'custom': ["initial begin\n\n  // rst_i\n  #0\n  rst_i = 1'b0;\n  #0\n  rst_i = 1'b0;\n\n  // we_i\nend\n"], 'ini': [{'we_i': "1'b0"}]}
        print(self._tbDic)
        # For ["ini"]
        #for i in self._tbDic["ini"]
        #xb

    # Update database
    def updateData(self):

        inputFlag = 1
        for d in self.parseDic["input"]:
            print(d)
            self.inputView.set("I{:0>3}".format(convert(str(inputFlag), "d", "h")), column="#3", value=d["isSet"])
            inputFlag += 1


        outputFlag = 1
        for d in self.parseDic["output"]:
            self.outputView.set("I{:0>3}".format(convert(str(outputFlag), "d", "h")), column="#3", value=d["isSet"])
            outputFlag += 1


if __name__ == "__main__":
    tbm = TestBenchMaker()
    tbm.initialGUI()
    #tbm.extractRTL("i3c_top.v")

import os, sys, time, json
import tkinter as tk
from tkinter import ttk
from tkinter.messagebox import showinfo
from tkinter.messagebox import askokcancel

sys.path.append(r"D:\pyLab\source\common")
from common import *


class GuiWindow(tk.Frame):
    # Initial
    # <master>: tk root master
    # <path>:   dir to trace
    # <width>:  width of gui
    # <height>: height of gui
    def __init__(self, master, path, width, height):
        # Common parameter
        self.width = width
        self.height = height

        # Parameter
        # Backup dir
        self.versionDir = os.path.join(path, "backup")
        if not os.path.exists(self.versionDir): os.mkdir(self.versionDir)

        # version log file record information about files in the below format (may use binary file or password encode text)
        self.versionLog = os.path.join(path, self.versionDir + r"\version.log")
        self.versionData = os.path.join(path, self.versionDir + r"\version.data")

        # Record treeview insert seq
        self._seq = [path]

        # Record last selection
        self.lastSelect = []

        # Record changed state
        self.recordState = ["Submit", "Record", "Recover"]

        # Record all item in tree view
        # {item:{"name":xxx, "abs":xxx, "state":xxx, "content":xxx, "type":xxx, "cur_version": "xxx",
        #       "history": [0, 1], "comment": ["0", "1"], "line": [(1,20), (30,50)]}}
        self._itemDict = {}

        # Add history, record added path
        self.addedHistoryList = []

        # Recover history, record recover path for writing
        self.recoverHistoryList = []

        # For gui view
        self.genInfoView(master)
        self.genTreeView(master, path)
        self.genButtonView(master)

    # Generate tree view
    # <master>: parent frame
    # <path>  : path to trace file
    def genTreeView(self, master, path):
        # Tool function
        def click(event):
            v = event.widget.selection()
            self.lastSelect = []
            for sv in v:
                path = self._seq[int(sv[1:], 16) - 1]
                self.showInformation(path)
                self.lastSelect.append(path)

        # Trace directory tree
        # <parentPath>: path to trace
        # <root>:       tree view to insert
        def loadTree(parentPath):
            filelist = os.listdir(parentPath)
            for filename in filelist:
                absPath = os.path.join(parentPath, filename)
                # Initial database
                if os.path.isfile(absPath):
                    self._queryDatabase([absPath], {"name": filename, "abs": absPath.replace("\\", "\\\\"), "state": "",
                                                    "content": "", "type": "file", "cur_version": "", "history": [],
                                                    "comment": [], "line": []})
                elif os.path.isdir(absPath):
                    self._queryDatabase([absPath],
                                        {"name": filename, "abs": absPath, "state": "", "content": "", "type": "folder",
                                         "cur_version": "", "history": [], "comment": [], "line": []})
                    loadTree(absPath)

        # Generate tree view struct
        # <root>:   root directory
        # <rootId>: root directory treeview id
        def genTree(root, rootId):
            dir = list(self._itemDict.keys())
            typ = [self._itemDict[i]["type"] for i in dir]
            dirDic = {root:rootId}
            for i in range(len(dir)):
                if dir[i] == root: continue
                [prefix, name] = os.path.split(dir[i])
                id = self.treeView.insert(dirDic[prefix], 'end', text=name)
                self._seq.append(dir[i])
                if typ[i] == "folder": dirDic[dir[i]] = id

        treeFrame = tk.Frame(master, padx=10, pady=10)
        treeFrame.grid(row=0, column=0)
        self.treeView = ttk.Treeview(treeFrame, height=int(self.height / 25), show="tree", columns=["state"])
        self.treeView.column("state", width=56, anchor='w')

        # Generate item Dict
        loadTree(path)
        self._queryDatabase([path], {"name": os.path.split(path)[-1], "abs": path, "state": "", "content": "", "type": "folder",
                                                        "cur_version": "", "history": [], "comment": [], "line": []})
        # Read version file
        self.versionControl("r")
        # Generate tree view struct
        root = self.treeView.insert("", "end", text=os.path.split(path)[-1])
        genTree(path, root)
        # Update state
        [self.showInformation(i, True) for i in self._seq]
        # Scroll bar
        treeYScroll = tk.Scrollbar(treeFrame, orient=tk.VERTICAL, command=self.treeView.yview)
        treeXScroll = tk.Scrollbar(treeFrame, orient=tk.HORIZONTAL, command=self.treeView.xview)
        treeXScroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.treeView.pack(side=tk.LEFT, fill=tk.BOTH)
        treeYScroll.pack(side=tk.LEFT, fill=tk.Y)
        self.treeView.config(yscrollcommand=treeYScroll.set, xscrollcommand=treeXScroll.set)
        self.treeView.bind("<<TreeviewSelect>>", click)

    # Generate treeview
    # <master>: parent frame
    def genInfoView(self, master):
        self.infoFrame = tk.Frame(master)
        self.infoFrame.grid(row=0, column=1)
        self.infoVar = tk.StringVar()
        txt = tk.Label(self.infoFrame, bg="white", textvariable=self.infoVar, width=int(self.width / 15),
                       height=int(self.height / 20))
        txt.pack()

    # Generate button for gui
    # <master>: parent frame
    def genButtonView(self, master):
        # Add select file to version dict
        def add():
            if self.lastSelect == []:
                showinfo(title="ERROR", message="Please select one item at least.")
            else:
                read = tk.StringVar()
                self.editor(self.infoFrame, None, None, read)
                buttonFrame.wait_variable(read)
                if read.get() != "None":
                    for i in self.treeView.selection():
                        # Update state
                        file = self._seq[int(i[1:], 16) - 1]
                        self._queryDatabase([file, "state"], 'Add')
                        # Content
                        abs = self._queryDatabase([file, "abs"])
                        content = readFile(abs) if self._queryDatabase([file, "type"]) == "file" else abs
                        self._queryDatabase([file, "content"], content)

                        if abs in self.addedHistoryList:
                            comment = self._queryDatabase([file, "comment"])
                            comment[-1] = read.get()
                            self._queryDatabase([file, "comment"], comment)
                        else:
                            # History
                            history = self._queryDatabase([file, "history"])
                            history.append(len(history))
                            self._queryDatabase([file, "history"], history)
                            # Comment
                            comment = self._queryDatabase([file, "comment"])
                            comment.append(read.get())
                            self._queryDatabase([file, "comment"], comment)
                            # Version
                            self._queryDatabase([file, "cur_version"], history[-1])
                        self.addedHistoryList.append(file)
                        self.showInformation(file)

        # Submit added item to write down
        def submit():
            if not self.addedHistoryList:
                showinfo(title="ERROR", message="Add file before commiting,")
            else:
                # Update gui state
                for i in self.addedHistoryList:
                    self._queryDatabase([i, "state"], 'Submit')
                    self.showInformation(i, True)
                self.versionControl("w")
                showinfo(title="INFO", message="Submit finished.")
                self.addedHistoryList = []

        # Recover data selected
        def recover():
            # For operation for click button
            def clickButton(opt):
                if opt == "r":
                    # Recover selected file from database
                    idx = select.get()
                    line = self._queryDatabase([filePath, "line"])[int(idx)]
                    # Use replace because windows will insert twice
                    content = readFile(self.versionData, line).replace("\n\n\n\n", "\n")
                    writeFile(filePath, content, False, True)
                    # Update database
                    self._queryDatabase([filePath, "state"], "Recover")
                    self._queryDatabase([filePath, "cur_version"], idx)
                    history = self._queryDatabase([filePath, "history"]).append(idx)
                    self._queryDatabase([filePath, "history"], history)
                    self.versionControl("w")
                    self.showInformation(filePath)

                self.recoverHistoryList = []
                frame.destroy()
                self.genInfoView(master)
                self.genButtonView(master)
                self.showInformation(filePath)

            if self.lastSelect == []:
                showinfo("ERROR", "Select one file before recover.")
                return
            elif not self._queryDatabase([self.lastSelect[-1], "state"]) in self.recordState + ["Lost"]:
                showinfo("ERROR", "The file is not recorded.")
                return

            filePath = self.lastSelect[-1]
            self.recoverHistoryList = [filePath]
            self.infoFrame.destroy()
            buttonFrame.destroy()
            m = master.winfo_geometry()
            masterSize = list(map(int, m[:m.find("+")].split("x")))
            frame = tk.Frame(master, width=masterSize[0], height=masterSize[1])
            frame.place(x=320, y=0)
            # Place suite
            select = tk.IntVar()
            commentVar = tk.StringVar()
            history = self._queryDatabase([filePath, "history"])
            comment = self._queryDatabase([filePath, "comment"])
            tk.Label(frame, text="Current file", anchor=tk.W, width=20).grid(row=0, column=0, padx=10, pady=10)
            tk.Label(frame, text=self.lastSelect[-1], anchor=tk.E, width=20).grid(row=0, column=1, padx=10, pady=10)
            tk.Label(frame, text="Version record", anchor=tk.W, width=20).grid(row=1, column=0, padx=10, pady=10)
            tk.Label(frame, text="->".join(str(i) for i in history), anchor=tk.E, width=20).grid(row=1, column=1, padx=10, pady=10)
            tk.Label(frame, text="Version to recover", anchor=tk.W, width=20).grid(row=2, column=0, padx=10, pady=10)
            tk.Label(frame, text="Comment", anchor=tk.W, width=20).grid(row=3, column=0, padx=10, pady=10)
            tk.Label(frame, textvariable=commentVar, anchor=tk.E, width=20).grid(row=3, column=1, padx=10, pady=10)
            com = ttk.Combobox(frame, textvariable=select, justify=tk.RIGHT, width=20, state="readonly")
            com.grid(row=2, column=1, padx=10, pady=10)
            # Button
            tk.Button(frame, text="Recover", width=15, bd=1, command=lambda: clickButton("r")).grid(row=1, column=2, padx=10, pady=10)
            tk.Button(frame, text="Cancel", width=15, bd=1, command=lambda: clickButton("c")).grid(row=2, column=2, padx=10, pady=10)

            curVersion = int(self._queryDatabase([filePath, "cur_version"]))
            com["value"] =history
            com.current(curVersion)
            commentVar.set(comment[curVersion])
            com.bind("<<ComboboxSelected>>", lambda x: commentVar.set(comment[int(select.get())]))

        # Delete data selected
        def delete():
            if self.lastSelect:
                ensure = askokcancel("WARN", "Do you want to delete select files?")
                if ensure:
                    for i in self.lastSelect:
                        typ = self._queryDatabase([i, "type"])
                        if typ == "file": os.remove(i)
                        elif typ =="folder": os.removedirs(i)
                        else: log("Bug flag", 3)
                    self.versionControl("d")
                    self.lastSelect = []
            else:
                showinfo(title="ERROR", message="Select files to delete,")


        buttonFrame = tk.Frame(master)
        buttonFrame.grid(row=0, column=2)
        tk.Button(buttonFrame, width=14, text="Add", command=add).grid(row=0, column=0, padx=15, pady=5)
        tk.Button(buttonFrame, width=14, text="Submit", command=submit).grid(row=1, column=0, padx=15, pady=5)
        tk.Button(buttonFrame, width=14, text="Recover", command=recover).grid(row=2, column=0, padx=15, pady=5)
        tk.Button(buttonFrame, width=14, text="Delete", command=delete).grid(row=3, column=0, padx=15, pady=5)

    # Update gui, show file information clicked to info view
    # <filePath>:  file path to get information
    # [onlyState]: just update state view
    def showInformation(self, filePath, onlyState=False):
        # Update state
        state = self._queryDatabase([filePath, "state"])
        h = hex(self._seq.index(filePath) + 1)[2:]
        idx = "I" + "0" * (3 - len(h)) + h.upper()
        self.treeView.set(idx, "#1", state)
        if onlyState: return # onlyState mode

        # Information view
        show = "{0:^41}\n".format("-" * 42)
        show += "{0:<10}{1:>30}\n".format("Name", os.path.split(filePath)[-1])
        show += "{0:<10}{1:>30}\n".format("Location", os.path.split(filePath)[:-1][0].replace("\\\\", "\\"))
        show += "{0:^41}\n".format("-" * 42)

        if os.path.isfile(filePath):  # Type
            show += "{0:<10}{1:>30}\n".format("Type", "." + os.path.split(filePath)[-1].split(".")[-1])
            fsize = os.path.getsize(filePath)  # Size
            if fsize > 1024 * 1024:
                show += "{0:<10}{1:>27} MB\n".format("Size", fsize)
            elif fsize > 1024:
                show += "{0:<10}{1:>27} KB\n".format("Size", round(fsize / 1024, 2))
            else:
                show += "{0:<10}{1:>27} B\n".format("Size", round(fsize / 1024 * 1024, 2))
        elif os.path.isdir(filePath):
            show += "{0:<10}{1:>30}\n".format("Type", "folder")
            show += "{0:<10}{1:>30}\n".format("Contain", len(os.listdir(filePath)))

        if state == "Lost":
            show += "{0:^41}\n".format("-" * 42)
            show += "{0:<10}{1:>30}\n".format("Access", "Lost")
            show += "{0:<10}{1:>30}\n".format("Create", "Lost")
            show += "{0:<10}{1:>30}\n".format("Modify", "Lost")
        else:
            atime = os.path.getatime(filePath)  # Access time
            ctime = os.path.getctime(filePath)  # Create time
            mtime = os.path.getmtime(filePath)  # Modify time
            show += "{0:^41}\n".format("-" * 42)
            show += "{0:<10}{1:>30}\n".format("Access", time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(atime)))
            show += "{0:<10}{1:>30}\n".format("Create", time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ctime)))
            show += "{0:<10}{1:>30}\n".format("Modify", time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mtime)))
        show += "{0:^41}\n".format("-" * 42)

        # Version control
        if str(self._queryDatabase([filePath, "cur_version"])) is "":
            cur_version = "Not record"
            comment = "Not record"
            last_version = "Not record"
        else:
            cur_version = int(self._queryDatabase([filePath, "cur_version"]))
            comment = self._queryDatabase([filePath, "comment"])[cur_version]
            last_version = max(self._itemDict[filePath]["history"])
        show += "{0:<15}{1:>25}\n".format("cur_version", cur_version)
        show += "{0:<15}{1:>25}\n".format("last_version", last_version)
        show += "{0:<15}{1:>25}\n".format("comment", comment)
        self.infoVar.set(show)

    # Version control write/read
    # <opt>: w: write; r: read; d: delete
    def versionControl(self, opt):
        if opt == "w":
            # For add
            for i in self.addedHistoryList:
                # Write version data
                content = self._queryDatabase([i, "content"])
                startline = readFile(self.versionData, False, True) if os.path.exists(self.versionData) else 0
                writeFile(self.versionData, content, True)
                endline = readFile(self.versionData, False, True) if os.path.exists(self.versionData) else 0
                lastline = self._queryDatabase([i, "line"])
                lastline.append((startline+1, endline))
                self._queryDatabase([i, "line"], lastline)
                # Write version log
                self._queryDatabase([i, "content"], "") # version data write in another file
                text = json.dumps(self._itemDict)
                writeFile(self.versionLog, text, False, True)
                self._queryDatabase([i, "content"], content)
            # For recover
            for i in self.recoverHistoryList:
                content = self._queryDatabase([i, "content"])
                self._queryDatabase([i, "content"], "") # version data write in another file
                text = json.dumps(self._itemDict)
                writeFile(self.versionLog, text, False, True)
                self._queryDatabase([i, "content"], content)
        elif opt == "r":
            if os.path.exists(self.versionLog):
                f = open(self.versionLog, "r")
                txt = f.read()
                f.close()
                for k,v in json.loads(txt).items():
                    if self._itemDict.get(k, None):
                        self._itemDict[k] = v
                    else:
                        self._itemDict[k] = v
                        self._itemDict[k]["state"] = "Lost"
                # Remark submit as record
                for k, v in self._itemDict.items():
                    if v["state"] in self.recordState:
                        self._queryDatabase([k, "state"], "Record")
        elif opt == "d":
            for i in self.lastSelect:
                self._queryDatabase([i, "state"], "Delete")
                self.showInformation(i, True)
                del(self._itemDict[i])
            text = json.dumps(self._itemDict)
            writeFile(self.versionLog, text, False, True)

        else:
            log("No support option in versionControl", 2)

    # Query database function, r/w operator should in this way
    # <key>: key to access, dic[a][b] -> [a，b]
    # [val]: value to write, default means read, otherwise write
    def _queryDatabase(self, key, val=None):
        idx = str(key).replace(",", "][")
        try:
            if val is None:  # Read
                val = eval("self._itemDict%s" % idx)
                return val
            else:  # Write
                if type(val) is str:
                    exec("self._itemDict{0}=val".format(idx))
                else:
                    exec("self._itemDict{0}={1}".format(idx, val))
        except NameError or IndexError:
            log("Access invalid index.", 2)

    # Pop a simple editor, size is same as master frame size
    # <master>: place view on the master
    # [height]: Text height, it's a entry when value is 1
    # [insert]: text want to insert into Text
    # [read]:   stringVar variable, would be set after click yes button
    # [label]:  head label on Text
    # [funcY]:  function called after click yes button
    # [funcN]:  function called after click no button
    def editor(self, master, height=None, insert=None, read=None, label=None, funcY=None, funcN=None):
        # Ensure if save edit data or not
        def ensure(opt="n"):
            if opt == "y":
                if read: read.set(text.get(0.0, tk.END))
                if funcY: funcY()
            else:
                if read: read.set(None)
                if funcN: funcN()
            t = text.get(0.0, tk.END)
            [i.destroy() for i in frame.winfo_children()]
            frame.destroy()

        m = master.winfo_geometry()
        masterSize = list(map(int, m[:m.find("+")].split("x")))
        frame = tk.Frame(master, width=masterSize[0], height=masterSize[1])
        frame.place(x=0, y=0)

        if label:
            tk.Label(frame, text=label).pack()

        text = tk.Text(frame, height=int(masterSize[1] * 0.06) if height is None else height,
                       width=int(masterSize[0] * 0.13), )
        if insert:
            text.insert(tk.END, insert)
        text.focus_force()
        yScroll = tk.Scrollbar(frame, orient=tk.VERTICAL, command=text.yview)
        yScroll.pack(side=tk.RIGHT, fill=tk.Y)
        text.config(yscrollcommand=yScroll.set)
        text.pack(side=tk.TOP, fill=tk.BOTH)
        subFrame = tk.Frame(frame)
        subFrame.pack(side=tk.TOP)
        buttonWidth = int(masterSize[0] * 0.13 * 0.2)
        tk.Button(subFrame, text="Cancel", width=buttonWidth, bd=1, command=ensure).pack(side=tk.RIGHT, padx=10)
        tk.Button(subFrame, text="Ok", width=buttonWidth, bd=1, command=lambda: ensure("y")).pack(side=tk.RIGHT,
                                                                                                  padx=10)


if __name__ == "__main__":
    win = tk.Tk()
    win.title('PyLab')
    WIDTH = 810
    HEIGHT = 400

    # Place GUI on the center of screen
    ws = win.winfo_screenwidth()
    hs = win.winfo_screenheight()
    x = (ws / 2) - (WIDTH / 2)
    y = (hs / 2) - (HEIGHT / 2)
    win.geometry('%dx%d+%d+%d' % (WIDTH, HEIGHT, x, y))
    path = r'D:\pyLab'
    ui = GuiWindow(win, path, WIDTH, HEIGHT)
    win.mainloop()
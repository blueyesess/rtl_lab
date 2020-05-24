#!/usr/bin/python3
#############################################################################
# Project:  XYM
# File:     common_class.py
# Athor:    Henson
# Descrp:   base class for common use
#############################################################################
# Version: 0.1
# Initial version
#############################################################################
from common import *
import threading

# Mutiple thread management
# <commands>: [[taskname,function], []]
#            task list, will execute with muti-thread process, 
#            if command is string, will execute as os.system(), 
#          elif command is callable, will execute as function
class MutiMana():
    # {{{
    def __init__(self, commands):

        # Setting params
        self.MAX_THREAD = 2
        self.REFRESH_TIME = 3

        # Create thread
        self.threadList = []
        for i in commands:
            n, c = i
            if type(c) == str:
                cmd = os.system(c)
            elif callable(c):
                cmd = c
            else:
                log("no support type %s" %type(c), 3)
                exit()
            self.threadList.append(self.myThread(n, c))
        manage = self.myThread("timer", lambda :self._timer(self.threadList))
        manage.start()
        manage.join()


    # Custom thread class 
    # <name>: thread name
    # <func>: execute function 
    class myThread (threading.Thread):
        # {{{
        def __init__(self, name, func):
            threading.Thread.__init__(self)
            self.name = name
            self.func = func
     
        def run(self):
            log("starting " + self.name, 0)
            self.func()
    # }}}
    
    # Timer for all threads, management of thread pool and output logs
    # <threads>: colloection of custom thread class
    def _timer(self, threads):
        # {{{
        limit=self.MAX_THREAD
        refresh = self.REFRESH_TIME
        idx = 0
        total = len(threads)
        op_tm = []
        ed_tm = [None for i in range(total)]
        incrIdx = True
        while True:
            curAlive = sum(i.isAlive() for i in threads)
            if incrIdx and curAlive < limit:
                if idx == total:
                    incrIdx = False
                else:
                    threads[idx].start()
                    op_tm.append(time.time())
                    idx += 1
            else:            
                os.system("clear")
                print("##################")
                print('Run Time: {0}'.format(sec2min(time.time()-startTime)))
                print("##################")        
                for i in range(total):
                    if i < idx:
                        if threads[i].isAlive():
                            ed_tm[i] = int(time.time()-op_tm[i])
                        print("Name: {0:<50}  State: {1:<20}  Dur:{2:>10}               Check: {3:<25}". \
                                format(threads[i].name, "running" if threads[i].isAlive() else "end", sec2min(ed_tm[i]),"" if threads[i].isAlive() else check.get(threads[i].name) ))
                    else:
                        print("Name: {0:<50}  State: {1:<20}  Dur: {2:>10}              Check: {2:<25}".format(threads[i].name, "wait", ""))
            if idx == total and max(i.isAlive() for i in threads) == 0:
                print("Complete! quit now.")        
                break
            time.sleep(refresh)
        # }}}
    #}}} 

# Tree view class, use as table
class treeView(): 
    # {{{
    # View tree
    # [master]: master will place on
    # [rowList]: for heading item messange
    # [columwidth]: specify the cloum width
    # [height]: specify treeview height
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
    #}}}

if __name__ == "__main__":
    def test():
        print(1)
    MutiMana([["test1", test], ["test2", test], ["test3", test]])

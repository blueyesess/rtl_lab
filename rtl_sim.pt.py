import os
sim_dir = r"D:\pyLab\source\rtl"
os.chdir(sim_dir)

flist = "filelist"
target_name = "out.o"
wavefile = "wave.vcd"

file = ""
f = open(os.path.join(sim_dir, flist))
for i in f.readlines():
    file += " " + i.replace("\n", "")

opt = "-g2005-sv"
sim_cmd = "iverilog {0} -o {1} {2}".format(opt, target_name, file)
gen_wave = "vvp {0}".format(target_name)
open_wave = "gtkwave {0}".format(wavefile)
os.system(sim_cmd)
os.system(gen_wave)
os.system(open_wave)
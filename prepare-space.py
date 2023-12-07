import os 
import sys
import pickle
import glob


with open("run.space.template") as f:
  run_script = f.read()
with open("space.py.template") as f:
  py_script = f.read()

structure_list = ['S19-domino','S19-pearl','S7c']
steps = 5000
border_width = 70
cutoff = 5
step_list = range(0,500001, steps)
tpn = 1
dump ='{"descriptor":all_descriptors[0], "energy":all_energies[0]}'

for gb in structure_list:
  dmu_list = sorted(glob.glob(os.path.join(gb,"Ag","T_????K_dmu_?????meV")))
  for dmu in dmu_list: 
    pbc = sorted(glob.glob(os.path.join(dmu, "pbc-??ns")))[-1]
    ex_dir = os.path.join(pbc, 'excess') 
    for step in step_list: 
      dir_name = os.path.join(pbc, 'excess', f'descriptor.{step:010d}')
      if not os.path.exists(dir_name):
        os.makedirs(dir_name)
      pypath = os.path.join(dir_name, "SPACE.py")
      if not os.path.exists(pypath):
        with open(pypath, "w") as f:
          f.write(py_script.format(step=step,
                                   border_width=border_width,
                                   cutoff=cutoff,
                                   dump=dump))
        with open(os.path.join(dir_name, 'space_run.sh'), 'w') as f:
          f.write(run_script.format(tpn=tpn,
                                    jobname = f'des.{step:010d}',
                                    pyname = 'SPACE.py'
                                    ))

  

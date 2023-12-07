#!/usr/bin/env python3

import glob
import os
import subprocess

for paramdir in sorted(glob.glob("T_????K_dmu_?????meV")):
  if not os.path.exists(os.path.join(paramdir, "end_run.data.gz")): 
    runscripts = [os.path.join(paramdir, "run.sh")] 
    if runscripts:
      subprocess.run(["chain_submit.py"] + runscripts)

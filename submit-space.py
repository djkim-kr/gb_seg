#!/usr/bin/env python3

import glob
import os
import subprocess

root = ['S19-domino','S19-pearl','S7c']
for gb in root:
  for paramdir in sorted(glob.glob(os.path.join(gb, 'Ag', "T_????K_dmu_?????meV/pbc-20ns/excess"))):
    runscripts = [os.path.join(d, "space_run.sh")
                  for d in sorted(glob.glob(os.path.join(paramdir, "descriptor.??????????")))
                  if not os.path.exists(os.path.join(d, "descriptors.?_??????????.pickle"))]
    if runscripts:
      subprocess.run(["chain_submit.py"] + runscripts)


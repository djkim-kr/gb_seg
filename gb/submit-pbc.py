#!/usr/bin/env python3

import glob
import os
import subprocess

for paramdir in sorted(glob.glob("T_????K_dmu_?????meV")):
    runscripts = [os.path.join(d, "run.sh")
                  for d in (sorted(glob.glob(os.path.join(paramdir, "pbc-??ns")))
                            + sorted(glob.glob(os.path.join(paramdir, "pbc-??ns/excess"))))
                  if (not os.path.exists(os.path.join(d, "end_run.data.gz"))
                      and not os.path.exists(os.path.join(d, "occupation-??.dump.gz")))]
    if runscripts:
        subprocess.run(["chain_submit.py"] + runscripts)

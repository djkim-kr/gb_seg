#!/usr/bin/env python3

import os
import random
import numpy as np

with open("lmp.in.template") as f:
    LMP_IN = f.read()
with open("run.sh.template") as f:
    RUN_SH = f.read()


dmu_l = np.arange(0.5,1.205, 0.005)
T_dmu = {
    300: dmu_l,
}

for T, dmu_list in T_dmu.items():
    for dmu in dmu_list:
        dirname = f"T_{T:04.0f}K_dmu_{1000*dmu:+05.0f}meV"
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        inpath = os.path.join(dirname, "lmp.in")
        if not os.path.exists(inpath):
            seed = random.randint(1, 1e9)
            with open(inpath, "w") as f:
                f.write(LMP_IN.format(T2=2*T,
                                      T=T,
                                      velseed=seed,
                                      dmu=dmu))
            with open(os.path.join(dirname, "run.sh"), "w") as f:
                f.write(RUN_SH.format(name=dirname.replace("/", "-")))

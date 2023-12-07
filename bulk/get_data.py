#!/usr/bin/env python3

from glob import glob
import os

import numpy as np

import sys
sys.path.insert(0, "../..")
from _projectlib import lammps

data = {}
latconst = {}
latconst0 = {}
Ecoh = {}
temperatures = set()
dmus = set()
for dirname in sorted(glob("T_????K_dmu_?????meV")):
    T = int(dirname.split("_")[1][:-1]) # K
    dmu = int(dirname.split("_")[3][:-3]) # meV
    log = lammps.read_log(os.path.join(dirname, "log.lammps.gz"))
    run = log[-2]
    n = len(run["Step"])
    c_Ag = np.average(run["v_cAg"][3*n//4:]) # last fourth
    a = np.average(run["Lx"][3*n//4:]
                   + run["Ly"][3*n//4:]
                   + run["Lz"][3*n//4:]) / (3*20)
    data[T, dmu] = c_Ag
    latconst[T, dmu] = a
    a0 = (log[-1]["Lx"][-1] + log[-1]["Ly"][-1] + log[-1]["Lz"][-1]) / (3*20)
    E = log[-1]["PotEng"][-1] / log[-1]["Atoms"][-1]
    latconst0[T, dmu] = a0
    Ecoh[T, dmu] = E
    temperatures.add(T)
    dmus.add(dmu)

# Write out data.
output = np.empty((len(dmus), len(temperatures)+1))
output_a = np.empty((len(dmus), len(temperatures)+1))
output_a0 = np.empty((len(dmus), len(temperatures)+1))
output_E = np.empty((len(dmus), len(temperatures)+1))

for i, dmu in enumerate(sorted(dmus)):
    output[i, 0] = dmu
    output_a[i, 0] = dmu
    output_a0[i, 0] = dmu
    output_E[i, 0] = dmu
    for j, T in enumerate(sorted(temperatures), 1):
        output[i, j] = data[T, dmu]
        output_a[i, j] = latconst[T, dmu]
        output_a0[i, j] = latconst0[T, dmu]
        output_E[i, j] = Ecoh[T, dmu]

np.savetxt("thermo.dat", output,
           header="Ag concentration\ndmu (meV)    "
                  + "    ".join(f"@ {T} K"
                                for T in sorted(temperatures)))
np.savetxt("latconst.dat", output_a,
           header="lattice constant (A)\ndmu (meV)    "
                  + "    ".join(f"@ {T} K"
                                for T in sorted(temperatures)))
np.savetxt("latconst0.dat", output_a0,
           header="lattice constant minimized 0 K (A)\ndmu (meV)    "
                  + "    ".join(f"@ {T} K"
                                for T in sorted(temperatures)))
np.savetxt("Ecoh.dat", output_E,
           header="cohesive energy (eV/atom)\ndmu (meV)    "
                  + "    ".join(f"@ {T} K"
                                for T in sorted(temperatures)))

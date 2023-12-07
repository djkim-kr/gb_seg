#!/usr/bin/env python3

import os
import random

with open("lmp.in.template") as f:
    LMP_IN = f.read()
with open("lmp.in.excess.template") as f:
    LMP_IN_EXCESS = f.read()
with open("run.sh.pbc.template") as f:
    RUN_SH_PBC = f.read()


# Fill out these settings ##############################################
#
# What temperatures and what values of Δµ?
T_dmu_pbc = {
    300: [-0.46, -0.48, -0.52, -0.54, -0.56, -0.58,
    -0.625, -0.630, -0.635, -0.645, -0.650, -0.655, -0.665, -0.670, -0.675, -0.685, -0.690, -0.695,
          -0.62, -0.64, -0.66, -0.68],
}
host_element = "Cu"
host_element_mass = " 63.546 "
a = {
    # lattice constant of host element as function of temperature
    0: 3.615,
    300: 3.63193003913628,
}
Ecoh = -3.54 # cohesive energy of pure host element.
second_element = "Ag"
second_element_mass = "107.8682"

pot_type = "eam/alloy"
pot_file = "../../../../WilliamsMishinHamilton2006-CuAg.eam.alloy"
pot_file_excess = "../../../../../WilliamsMishinHamilton2006-CuAg.eam.alloy"
# MC parameters
mc_every = "20"  # after this many MD steps, run Monte Carlo
mc_steps = "0.1" # how many MC steps to run; is multiplied by number of atoms

# Size of simulation cell
repeat_x = 3
repeat_z = 15
lx = f"{repeat_x} * sqrt(3*3 + 4*4 + 7*7)/2 * v_a"
lz = f"{repeat_z} * sqrt(3) * v_a"

run_time = 20 # ns

# This will prepare the final averaging calculations. Only activate
# when the simulations are equilibrated.
finish = True 
########################################################################


for T, dmu_list in T_dmu_pbc.items():
    for dmu in dmu_list:
        run_time_pbc = run_time
        for i in range(1, run_time_pbc+1):
            dirname = f"T_{T:04.0f}K_dmu_{1000*dmu:+05.0f}meV/pbc-{i:02.0f}ns"
            if not os.path.exists(dirname):
                os.makedirs(dirname)
            inpath = os.path.join(dirname, "lmp.in")
            if not os.path.exists(inpath):
                bc = "p s p"
                scale_fac = a[T]/a[0]
                read_data = (
                    "read_data ../../ground-state/minimized-2atomtypes.data.gz\n"
                    f"change_box all x scale {scale_fac} y scale {scale_fac} z scale {scale_fac} remap\n"
                    f"replicate {repeat_x} 1 {repeat_z}"
                    if i == 1
                    else f"read_data ../pbc-{i-1:02.0f}ns/end_run.data.gz"
                )
                seed = random.randint(1, 1e9)
                velocity = (
                    f"velocity        all create {2*T} {seed}  loop local"
                    if i == 1
                    else ""
                )
                base_ensemble = f"fix             1 all nvt temp {T} {T} 0.1"
                with open(inpath, "w") as f:
                    f.write(LMP_IN.format(bc=bc,
                                          read_data=read_data,
                                          pot_type=pot_type,
                                          pot_file=pot_file,
                                          host_element=host_element,
                                          host_element_mass=host_element_mass,
                                          second_element=second_element,
                                          second_element_mass=second_element_mass,
                                          T=T,
                                          base_ensemble=base_ensemble,
                                          mc_every=mc_every,
                                          mc_steps=mc_steps,
                                          velocity=velocity,
                                          dmu=dmu))
                with open(os.path.join(dirname, "run.sh"), "w") as f:
                    f.write(RUN_SH_PBC.format(name=dirname.replace("/", "-"),
                                              time="24:00:00",
                                              extra_cmds=""))
            if (i == run_time_pbc) and finish:
                excess_dir = os.path.join(dirname, "excess")
                if not os.path.exists(excess_dir):
                    os.makedirs(excess_dir)
                inpath = os.path.join(excess_dir, "lmp.in")
                if not os.path.exists(inpath):
                    bc = "p s p"
                    base_ensemble = f"fix             1 all nvt temp {T} {T} 0.1"
                    with open(inpath, "w") as f:
                        f.write(LMP_IN_EXCESS.format(bc=bc,
                                                     pot_type=pot_type,
                                                     pot_file=pot_file_excess,
                                                     host_element=host_element,
                                                     host_element_mass=host_element_mass,
                                                     second_element=second_element,
                                                     second_element_mass=second_element_mass,
                                                     base_ensemble=base_ensemble,
                                                     mc_every=mc_every,
                                                     mc_steps=mc_steps,
                                                     T=T,
                                                     dmu=dmu,
                                                     a=a[0],
                                                     Ecoh=Ecoh,
                                                     lx=lx,
                                                     lz=lz))
                    with open(os.path.join(excess_dir, "run.sh"), "w") as f:
                        f.write(RUN_SH_PBC.format(name=excess_dir.replace("/", "-"),
                                                  time="48:00:00",
                                                  extra_cmds=f"""
rm -f occupation-{second_element}.dump.0000000000
mv occupation-{second_element}.dump.0000500000 occupation-{second_element}.dump
gzip occupation-{second_element}.dump minimized.dump.*
rm -f restart.*
"""))

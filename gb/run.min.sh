#!/bin/bash -l
#
#SBATCH --job-name=SOME_NAME
#
#SBATCH -o out.%j
#SBATCH -e err.%j
#
#SBATCH --partition=p.cmfe  # <- if only one node, use "s.cmfe", otherwise "p.cmfe"
#SBATCH --constraint=[swi1|swi2|swi3|swi4|swi5|swi6|swi7|swi8|swi9|swe1|swe2|swe3|swe4|swe5|swe6|swe7]
#
#SBATCH --nodes=1
# "Task" is a process, "CPUs per task" means threads per process
#SBATCH --ntasks-per-node=40  # every node has 40 cores
#SBATCH --cpus-per-task=1
#
#SBATCH --time=03:00:00  # max time is 3 days = 72 h, please use sensible number

module load intel/19.1.0
module load impi/2019.6
module load mkl/2019.5
module load lammps/29Sep21

export OMP_NUM_THREADS="$SLURM_CPUS_PER_TASK"

echo "Start: $(date)"
echo "cwd: $(pwd)"

srun lmp_mpi -in lmp.in

# gzip *.data   # gzip things as needed!

echo "End: $(date)"

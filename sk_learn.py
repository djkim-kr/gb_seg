import sys
import os
import pickle
import glob
import numpy as np 
import gzip
import sklearn.linear_model
import pyiron_atomistics
import matplotlib.pyplot as plt
from itertools import combinations
#sys.path.insert(0, './')
from _projectlib import lammps
from _projectlib.pyiron_dpd import make_ace, space, get_ace_descr


def read_seg_sites(dump_file, border_width=70):
  box = lammps.read_dump(dump_file,
                         lammps.ELEMENTS_IN)
  box.pbc = [True, True, True]
  ymin = box.positions[:,1].min()
  ymax = box.positions[:,1].max()
  del box[(box.positions[:,1] < ymin+border_width)
          |
          (box.positions[:,1] > ymax-border_width)]
  seg_sites = np.nonzero(box.numbers == 2)[0]
  structure = pyiron_atomistics.ase_to_pyiron(box)
  return seg_sites, structure

def write_params(train_list, cutoff, steps):
  step_list = range(0,500001, steps)
  for train in train_list:
    all_descriptors = []
    all_energies = []
    for gb in train:
      dmu_list = sorted(glob.glob(os.path.join(gb,"Ag","T_????K_dmu_?????meV")))
      for dmu in dmu_list: 
        pbc = sorted(glob.glob(os.path.join(dmu, "pbc-??ns")))[-1]
        log = lammps.read_log(os.path.join(pbc, 'excess', 'log.lammps'))
        v_Agb = log[4]["v_Agb"][-1]
        for step in step_list:
          des_pickle = os.path.join(pbc,'excess',f'descriptor.{step:010d}',
                                    f'descriptors.{cutoff}_{step:010d}.pickle')
          if os.path.getsize(des_pickle) != 0:
            with open (des_pickle, 'rb') as f:
              data = pickle.load(f)
            all_descriptors.append(data["descriptor"])
            all_energies.append(data["energy"]* v_Agb)

    sklearn_thingy = sklearn.linear_model.LinearRegression()
    sklearn_thingy.fit(all_descriptors, all_energies)
    
    write_file = f'./space_descriptors/my_params_{train[0]}&{train[1]}&{train[2]}_{steps}.pickle'
    with open(write_file, 'wb') as f:
      pickle.dump({"model": sklearn_thingy, "cutoff": cutoff}, f)

def write_params_individual(train_list, cutoff, steps):
  step_list = range(0,500001, steps)
  for gb in train_list:
    all_descriptors = []
    all_energies = []
    dmu_list = sorted(glob.glob(os.path.join(gb,"Ag","T_????K_dmu_?????meV")))
    for dmu in dmu_list: 
      pbc = sorted(glob.glob(os.path.join(dmu, "pbc-??ns")))[-1]
      log = lammps.read_log(os.path.join(pbc, 'excess', 'log.lammps'))
      v_Agb = log[4]["v_Agb"][-1]
      for step in step_list:
        des_pickle = os.path.join(pbc,'excess',f'descriptor.{step:010d}',
                                  f'descriptors.{cutoff}_{step:010d}.pickle')
        if os.path.getsize(des_pickle) != 0:
          with open (des_pickle, 'rb') as f:
            data = pickle.load(f)
          all_descriptors.append(data["descriptor"])
          all_energies.append(data["energy"]*v_Agb)
    sklearn_thingy = sklearn.linear_model.LinearRegression()
    sklearn_thingy.fit(all_descriptors, all_energies)

    write_file = f'./space_descriptors/my_params_{gb}_{steps}.pickle'
    with open(write_file, 'wb') as f:
      pickle.dump({"model": sklearn_thingy, "cutoff": cutoff}, f)

class Predictor:
  def __init__(self, load_file, cutoff):
    with open(load_file, 'rb') as f:
      data = pickle.load(f)
    self._model = data["model"]
    self._cutoff = data["cutoff"]
    self._ace = make_ace(self._cutoff)
  def get_gb_energy(self, descriptors):
    return self._model.predict([descriptors])[0]

def energy_list(gb, step_list, predictor, cutoff):
  E_original = []
  E_predict = []
  dmu_data = []
  step_data = []
  c_Ag_data = []
  N_Ag_data = []

  dmu_list = sorted(glob.glob(os.path.join(gb,"Ag","T_????K_dmu_?????meV")))
  for dmu in dmu_list:
    pbc = sorted(glob.glob(os.path.join(dmu, "pbc-??ns")))[-1]
    log = lammps.read_log(os.path.join(pbc, 'excess', 'log.lammps'))
    log = log[1:]
    v_Agb = log[3]["v_Agb"][-1]
    dmu_d = int(dmu.split('meV')[0].split('_')[-1].split('-')[-1])
    for step in step_list:
      dump_file = os.path.join(pbc, 'excess',f'minimized.dump.{step:010d}.gz')
      seg_sites, box = read_seg_sites(dump_file)
      if len(seg_sites):
        des_pickle = os.path.join(pbc,'excess',f'descriptor.{step:010d}',
                                  f'descriptors.{cutoff}_{step:010d}.pickle')
        if os.path.getsize(des_pickle) != 0:
          with open (des_pickle, 'rb') as f:
            data = pickle.load(f)
        descriptor = data["descriptor"]
        E_original.append(data["energy"])
        Egb = predictor.get_gb_energy(descriptor)
        E_predict.append(Egb / v_Agb)
        dmu_data.append(dmu_d)
        step_data.append(step)
        c_Ag_data.append(len(seg_sites))
        N_Ag_data.append(len(seg_sites)/ v_Agb)
        
  if not all(len(lst) == len(E_original) for lst in [E_predict, dmu_data, step_data, c_Ag_data, N_Ag_data]):
    raise ValueError('length of all lists should be the same')
  return E_original, E_predict, dmu_data, step_data, c_Ag_data, N_Ag_data

def rms_dict(x_ref, x_pred):
    x_ref = np.array(x_ref)
    x_pred = np.array(x_pred)
    if np.shape(x_pred) != np.shape(x_ref):
        raise ValueError('WARNING: not matching shapes in rms')
    error_2 = (x_ref - x_pred) ** 2
    average = np.sqrt(np.average(error_2))
    std_ = np.sqrt(np.var(error_2))
    return {'rmse': average, 'std': std_}

###################################################################################

TRAIN = False
TEST = True

des_list = ['S37c-pearl','S7-domino','S7c','S19-domino','S49-domino','S49-pearl']
train_list = list(combinations(des_list, 3))
#train_list = [['S7-domino','S37c-pearl'],['S49-domino','S37c-pearl'],['S49-pearl','S37c-pearl']]
if TRAIN:
  write_params(train_list, cutoff=5, steps=5000)


# train_list = ['S37c-pearl','S7-domino','S7-pearl','S7c','S19-domino','S19-pearl','S49-domino','S49-pearl']
test_list = ['S37c-pearl','S7-domino','S7-pearl','S7c','S19-domino','S19-pearl','S49-domino','S49-pearl']
step_list = [500000]
if TEST:
  for gb in test_list:
    for train in train_list:
      steps = 5000
      predictor = Predictor(f'./space_descriptors/my_params_{train[0]}&{train[1]}&{train[2]}_{steps}.pickle', 5)
      E_original, E_predict, dmu_data, step_data, c_Ag_data, N_Ag_data = energy_list(gb, step_list, predictor,5)
      data = np.column_stack((dmu_data, step_data, 
                              np.round(E_original,3), np.round(E_predict,3),
                              c_Ag_data, N_Ag_data))
      output_file = f"./space_descriptors/{train[0]}&{train[1]}&{train[2]}_{gb}_energy.dat"
      np.savetxt(output_file, data, delimiter=' ',
                 header ='dmu step E_original E_predict c_Ag N_Ag(1/A²)', 
                 comments='', fmt='%s')
      print(f'{output_file} is written')

#      rms = rms_dict(E_original, E_predict)
#      rmse = np.round(rms['rmse'],3)
#      std = np.round(rms['std'],3)    




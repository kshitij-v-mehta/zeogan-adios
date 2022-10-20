#!/usr/bin/env python3

import sys
import os
import glob
import numpy as np
import adios2


if (len(sys.argv) != 2):
    print("Need input directory")
    sys.exit(1)

# Open input dir and get file list
in_dir = sys.argv[1]
assert os.path.isdir(in_dir), "{} does not seem to exist".format(in_dir)
_flist = glob.glob("{}/*.grid".format(in_dir))
print("Found {} files in {}".format(len(_flist), in_dir))
flist = [f.split(".grid")[0] for f in _flist]


# ADIOS initializations
adios = adios2.ADIOS()
io = adios.DeclareIO("writer")
en = io.Open("test.bp", adios2.Mode.Write)


# Define variables
_celldata = np.empty((3))
var_cellparams = io.DefineVariable('cell_parameters', _celldata,
        [], [], list(np.shape(_celldata)), adios2.ConstantDims)
var_cellangles = io.DefineVariable('cell_angles', _celldata,
        [], [], list(np.shape(_celldata)), adios2.ConstantDims)
var_gridnum = io.DefineVariable('grid_numbers', _celldata,
        [], [], list(np.shape(_celldata)), adios2.ConstantDims)

_ndarray = np.empty((32,32,32), dtype=np.float32)
var_griddata = io.DefineVariable('griddata', _ndarray,
        [], [], list(np.shape(_ndarray)), adios2.ConstantDims)
var_O = io.DefineVariable('O', _ndarray,
        [], [], list(np.shape(_ndarray)), adios2.ConstantDims)
var_si = io.DefineVariable('si', _ndarray,
        [], [], list(np.shape(_ndarray)), adios2.ConstantDims)


# Read raw data and write to ADIOS fle
for fname in flist:
    gridf = "{}.grid".format(fname)
    griddataf = "{}.griddata".format(fname)
    of = "{}.O".format(fname)
    sif = "{}.si".format(fname)
    
    with open(gridf) as f:
        lines = f.readlines()

    cell_parameters = np.float_(lines[0].split()[1:])
    cell_angles = np.float_(lines[1].split()[1:])
    grid_numbers = np.float_(lines[2].split()[1:])

    griddata = np.fromfile(griddataf, dtype=np.float32)
    Odata = np.fromfile(of, dtype=np.float32)
    sidata = np.fromfile(sif, dtype=np.float32)
    # np.savetxt("{}.txt".format(griddataf), griddata)

    en.BeginStep()
    en.Put(var_cellparams, cell_parameters)
    en.Put(var_cellangles, cell_angles)
    en.Put(var_gridnum, grid_numbers)
    en.Put(var_griddata, griddata)
    en.Put(var_O, Odata)
    en.Put(var_si, sidata)
    en.EndStep()

en.Close()
 
print("Done.")


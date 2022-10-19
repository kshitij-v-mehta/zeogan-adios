#!/usr/bin/env python3

import numpy as np
import adios2


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


# Read raw data and write to ADIOS fle
for fname in ["ACO", "LTA"]:
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
    # np.savetxt("{}.txt".format(griddataf), griddata)

    en.BeginStep()
    en.Put(var_cellparams, cell_parameters)
    en.Put(var_cellangles, cell_angles)
    en.Put(var_gridnum, grid_numbers)
    en.Put(var_griddata, griddata)
    en.EndStep()

en.Close()
 

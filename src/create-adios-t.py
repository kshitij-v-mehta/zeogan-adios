#!/usr/bin/env python3

import sys
import os
import glob
import queue
import sys
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import adios2


rootdir     = "../data/206"
adios_fname = "test.bp"

q = queue.Queue()

def get_flist():
    try:
        flist = []
        gridfnames = glob.glob("{}/*.grid".format(rootdir))
        for fname in gridfnames:
            flist.append(fname.rsplit('/',1)[-1].split(".grid")[0])

        return flist
    
    except Exception as e:
        print(e)
        sys.exit(1)


def read_data(objname):
    try:
        objpath = '{}/{}'.format(rootdir,objname)
        
        gridf     = objpath + ".grid"
        griddataf = objpath + ".griddata"
        of        = objpath + ".O"
        sif       = objpath + ".si"
        
        with open(gridf) as f:
            gridtext = f.readlines()

        griddata = np.fromfile(griddataf, dtype=np.float32)
        Odata    = np.fromfile(of,        dtype=np.float32)
        sidata   = np.fromfile(sif,       dtype=np.float32)

        d = dict()
        d['name']     = objname
        d['gridtext'] = gridtext
        d['griddata'] = griddata
        d['Odata']    = Odata
        d['sidata']   = sidata

        q.put(d)

    except Exception as e:
        print(e)
        sys.exit(1)


def create_adios():
    try:
        # ADIOS initializations
        adios = adios2.ADIOS()
        io = adios.DeclareIO("writer")
        io.SetParameter("engine", "BP5")
        en = io.Open("{}/{}".format(rootdir,adios_fname), adios2.Mode.Write)
        
        # Define variables
        var_name = io.DefineVariable('name')
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
    

        # Iterate over the queue
        stepcount = 0
        for i in range(len(flist)):
            d = q.get()
            
            cell_parameters = np.float_(d['gridtext'][0].split()[1:])
            cell_angles     = np.float_(d['gridtext'][1].split()[1:])
            grid_numbers    = np.float_(d['gridtext'][2].split()[1:])

            # Create new step and write data
            en.BeginStep()
            en.Put(var_name,       d['name'])
            en.Put(var_cellparams, cell_parameters)
            en.Put(var_cellangles, cell_angles)
            en.Put(var_gridnum,    grid_numbers)
            en.Put(var_griddata,   d['griddata'])
            en.Put(var_O,          d['Odata'])
            en.Put(var_si,         d['sidata'])
            en.EndStep()
            
            q.task_done()
            stepcount = stepcount + 1
            print("Step {}".format(stepcount), flush=True)

        en.Close()
    
    except Exception as e:
        print(e)
        sys.exit(1)



# -------------------------------------------------------------------------- #
# Get list of data items in the directory
flist = get_flist()
print("Received {} files".format(len(flist)))

with ThreadPoolExecutor(max_workers=None) as executor:
    # Launch worker to create ADIOS file
    executor.submit(create_adios)
    
    # Launch I/O workers
    executor.map(read_data, flist)

print("All data added to queue. Waiting for adios writer to complete")
q.join()

print("Done")


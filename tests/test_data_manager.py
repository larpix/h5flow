import pytest
import h5py
import os
from mpi4py import MPI

from h5flow.data import H5FlowDataManager

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

@pytest.fixture
def testfile(mpi_tmp_path):
    return os.path.join(mpi_tmp_path, 'test.h5')

@pytest.fixture
def datamanager(testfile):
    dm = H5FlowDataManager(testfile)
    return dm

def test_init(testfile, datamanager):
    # check that filepath was intialized correctly
    assert datamanager.filepath == testfile
    # check that file opens ok
    assert datamanager.fh

@pytest.fixture
def empty_testdset(datamanager):
    name = 'test/test'
    dm = datamanager
    dm.create_dset('test/test', int)
    return name

def test_create_dset(datamanager, empty_testdset):
    dm = datamanager
    # check that dataset opens and has correct type
    assert dm.get_dset(empty_testdset).dtype == int
    # check that dataset is still empty
    assert len(dm.get_dset(empty_testdset)) == 0

@pytest.fixture
def empty_testattr(datamanager, empty_testdset):
    dm = datamanager
    dm.set_attrs('test', test=123)
    return 'test'

def test_setattr(datamanager, empty_testattr):
    dm = datamanager
    # check that dataset was given correct attribute data
    assert dm.get_attrs(empty_testattr)['test'] == 123

@pytest.fixture
def empty_testref(datamanager, empty_testdset):
    dm = datamanager
    dm.create_ref(empty_testdset, empty_testdset)
    return empty_testdset, empty_testdset

def test_create_ref(datamanager, empty_testref):
    dm = datamanager
    # check that ref dataset opens and has correct type
    assert dm.get_ref(*empty_testref).dtype == h5py.regionref_dtype
    # check that ref dataset is still empty
    assert len(dm.get_ref(*empty_testref)) == 0

@pytest.fixture
def full_testdset(datamanager, empty_testdset):
    dm = datamanager
    sl = dm.reserve_data(empty_testdset, 100)
    dm.write_data(empty_testdset, sl, rank)
    return empty_testdset, sl

def test_write_dset(datamanager, full_testdset):
    dm = datamanager
    # check that we have access to the *full* dataset after writing
    assert len(dm.get_dset(full_testdset[0])) == size*100
    # check that processes wrote to correct region
    assert all(dm.get_dset(full_testdset[0])[full_testdset[1]] == rank)

@pytest.fixture
def full_testref(datamanager, full_testdset, empty_testref):
    dm = datamanager
    n = full_testdset[1].stop - full_testdset[1].start
    sl = dm.reserve_ref(*empty_testref, n)
    dm.write_ref(*empty_testref, sl, [full_testdset[1] for _ in range(sl.start, sl.stop)])
    return empty_testref, sl

def test_write_ref(datamanager, full_testdset, full_testref):
    dm = datamanager
    # check that we have access to the *full* ref dataset after writing
    assert len(dm.get_ref(*full_testref[0])) == size*100
    # check that child attribute is accessible and correct
    assert dm.fh[dm.get_ref(*full_testref[0]).attrs['child']] == dm.get_dset(full_testdset[0])
    ref = dm.get_ref(*full_testref[0])[full_testref[1]]
    # check that first of process' refs point to the correct chunk of the dataset
    assert all(dm.get_dset(full_testdset[0])[ref[0]] == dm.get_dset(full_testdset[0])[full_testdset[1]])



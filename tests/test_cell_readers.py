import os
import tempfile
import shutil
import pytest
import logging
from cellpy import log
from . import fdv

log.setup_logging(default_level=logging.DEBUG)


@pytest.fixture
def cellpy_data_instance():
    from cellpy import cellreader
    return cellreader.CellpyData()


@pytest.fixture
def dataset():
    from cellpy import cellreader
    a = cellreader.CellpyData()
    a.from_raw(fdv.res_file_path)
    a.set_mass(1.0)
    a.make_summary(find_ocv=False, find_ir=True,
                   find_end_voltage=True)
    a.save(fdv.cellpy_file_path)

    b = cellreader.CellpyData()
    b.load(fdv.cellpy_file_path)
    return b


def test_create_cellpyfile(cellpy_data_instance):
    # create a cellpy file from the res-file (used for testing)
    cellpy_data_instance.from_raw(fdv.res_file_path)
    cellpy_data_instance.set_mass(1.0)
    cellpy_data_instance.make_summary(find_ocv=False, find_ir=True, find_end_voltage=True)
    print(f"trying to save the cellpy file to {fdv.cellpy_file_path}")
    cellpy_data_instance.save(fdv.cellpy_file_path)


def test_search_for_files():
    import os
    from cellpy import filefinder
    run_files, cellpy_file = filefinder.search_for_files(fdv.run_name,
                                                         raw_file_dir=fdv.raw_data_dir,
                                                         cellpy_file_dir=fdv.output_dir)
    assert fdv.res_file_path in run_files
    assert os.path.basename(cellpy_file) == fdv.cellpy_file_name


def test_set_res_datadir_wrong(cellpy_data_instance):
    _ = r"X:\A_dir\That\Does\Not\Exist\random_random9103414"
    cellpy_data_instance.set_cellpy_datadir(_)
    assert _ != cellpy_data_instance.cellpy_datadir


def test_set_res_datadir_none(cellpy_data_instance):
    cellpy_data_instance.set_cellpy_datadir()
    assert cellpy_data_instance.cellpy_datadir is None


def test_set_res_datadir(cellpy_data_instance):
    cellpy_data_instance.set_cellpy_datadir(fdv.data_dir)
    assert fdv.data_dir == cellpy_data_instance.cellpy_datadir


def test_fid(cellpy_data_instance):
    cellpy_data_instance.loadcell(fdv.res_file_path)
    my_test = cellpy_data_instance.dataset
    assert len(my_test.raw_data_files) == 1
    fid_object = my_test.raw_data_files[0]
    print(fid_object)
    print(fid_object.get_raw())
    print(fid_object.get_name())
    print(fid_object.get_size())
    print(fid_object.get_last())


def test_only_fid():
    from cellpy.readers.cellreader import FileID
    my_fid_one = FileID()
    my_file = fdv.cellpy_file_path
    my_fid_one.populate(my_file)
    my_fid_two = FileID(my_file)
    assert my_fid_one.get_raw()[0] == my_fid_two.get_raw()[0]
    assert my_fid_one.get_size() == my_fid_two.get_size()


def test_load_res(cellpy_data_instance):
    cellpy_data_instance.loadcell(fdv.res_file_path)
    run_number = 0
    data_point = 2283
    step_time = 1500.05
    sum_discharge_time = 362198.12
    my_test = cellpy_data_instance.datasets[run_number]
    assert my_test.dfsummary.loc[1, "Data_Point"] == data_point
    assert step_time == pytest.approx(my_test.dfdata.loc[4, "Step_Time"], 0.1)
    assert sum_discharge_time == pytest.approx(my_test.dfsummary.loc[:, "Discharge_Time"].sum(), 0.1)
    assert my_test.test_no == run_number

    # cellpy_data_instance.make_summary(find_ir=True)
    # cellpy_data_instance.make_step_table()
    # cellpy_data_instance.save(test_cellpy_file_full)


def test_make_summary(cellpy_data_instance):
    cellpy_data_instance.from_raw(fdv.res_file_path)
    cellpy_data_instance.set_mass(1.0)
    cellpy_data_instance.make_summary()
    s1 = cellpy_data_instance.datasets[0].dfsummary
    s2 = cellpy_data_instance.get_dataset().dfsummary
    s3 = cellpy_data_instance.get_summary()
    assert s1.columns.tolist() == s2.columns.tolist()
    assert s2.columns.tolist() == s3.columns.tolist()
    assert s2.iloc[:, 3].size == 17
    assert s2.iloc[5, 3] == s1.iloc[5, 3]





def test_summary_from_cellpyfile(cellpy_data_instance):
    cellpy_data_instance.load(fdv.cellpy_file_path)
    s1 = cellpy_data_instance.get_summary()
    mass = cellpy_data_instance.get_mass()
    cellpy_data_instance.set_mass(mass)
    cellpy_data_instance.make_summary(find_ocv=False, find_ir=True, find_end_voltage=True)
    s2 = cellpy_data_instance.get_summary()
    assert s1.columns.tolist() == s2.columns.tolist()
    assert s2.iloc[:, 3].size == 17
    assert s2.iloc[5, 3] == s1.iloc[5, 3]


def test_load_cellpyfile(cellpy_data_instance):
    cellpy_data_instance.load(fdv.cellpy_file_path)
    run_number = 0
    data_point = 2283
    step_time = 1500.05
    sum_test_time = 9301719.457
    my_test = cellpy_data_instance.datasets[run_number]
    unique_cycles = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]
    unique_cycles_read = my_test.step_table.loc[:, "cycle"].unique()
    assert any(map(lambda v: v in unique_cycles_read, unique_cycles))
    assert my_test.dfsummary.loc[1, "Data_Point"] == data_point
    assert step_time == pytest.approx(my_test.dfdata.loc[4, "Step_Time"], 0.1)
    assert sum_test_time == pytest.approx(my_test.dfsummary.loc[:, "Test_Time"].sum(), 0.1)
    assert my_test.test_no == run_number


def test_get_current_voltage(dataset):
    v = dataset.get_voltage(cycle=5)
    assert len(v) == 498
    c = dataset.get_current(cycle=5)
    assert len(c) == 498


def test_get_capacity(dataset):
    cc, vcc = dataset.get_ccap(cycle=5)
    assert len(cc) == len(vcc)
    assert len(cc) == 214
    dc, vdc = dataset.get_dcap(cycle=5)
    assert len(dc) == len(vdc)
    assert len(dc) == 224
    c, v = dataset.get_cap(cycle=5)
    assert len(c) == len(v)


@pytest.mark.parametrize("test_input,expected", [
    ((1.0, 1.0), 1.0),
    ((1.0, 0.1), 0.1),
    ((0.1, 1.0), 10.0),
    pytest.mark.xfail(((1.0, 0.001), 1.0)),
])
def test_get_converter_to_specific(dataset, test_input, expected):
    c = dataset.get_converter_to_specific(mass=1.0, to_unit=test_input[0], from_unit=test_input[1])
    assert c == expected


def test_save_cellpyfile_with_extension(cellpy_data_instance):
    cellpy_data_instance.loadcell(fdv.res_file_path)
    cellpy_data_instance.make_summary(find_ir=True)
    cellpy_data_instance.make_step_table()
    tmp_file = next(tempfile._get_candidate_names())+".h5"
    cellpy_data_instance.save(tmp_file)
    assert os.path.isfile(tmp_file)
    os.remove(tmp_file)
    assert not os.path.isfile(tmp_file)


def test_save_cellpyfile_auto_extension(cellpy_data_instance):
    cellpy_data_instance.loadcell(fdv.res_file_path)
    cellpy_data_instance.make_summary(find_ir=True)
    cellpy_data_instance.make_step_table()
    tmp_file = next(tempfile._get_candidate_names())
    cellpy_data_instance.save(tmp_file)
    assert os.path.isfile(tmp_file+".h5")
    os.remove(tmp_file+".h5")
    assert not os.path.isfile(tmp_file+".h5")


def test_save_cvs(cellpy_data_instance):
    cellpy_data_instance.loadcell(fdv.res_file_path)
    cellpy_data_instance.make_summary(find_ir=True)
    cellpy_data_instance.make_step_table()
    temp_dir = tempfile.mkdtemp()
    cellpy_data_instance.to_csv(datadir=temp_dir)
    shutil.rmtree(temp_dir)
    # cellpy_data_instance.save(tmp_file)
    # assert os.path.isfile(tmp_file)
    # os.remove(tmp_file)
    # assert not os.path.isfile(tmp_file)


def test_str_cellpy_data_object(dataset):
    assert str(dataset.dataset).find("silicon") >= 0
    assert str(dataset.dataset).find("rosenborg") < 0

import numpy as np
import pandas as pd
import pytest

import olorenchemengine as oce
from olorenchemengine.internal import download_public_file

__author__ = "Oloren AI"
__copyright__ = "Oloren AI"


def remote(func):
    def wrapper(*args, **kwargs):
        with oce.Remote("http://api.oloren.ai:5000") as remote:
            func(*args, **kwargs)

    return wrapper


@pytest.fixture
def example_data1():
    file_path = download_public_file("sample-csvs/sample_data1.csv")
    df = pd.read_csv(file_path)
    return df


# RuntimeError: Not compiled with CUDA support


def test_TorchGeometric(example_data1):
    data = oce.RandomSplit(split_proportions=[0.8, 0.0, 0.2]).split(example_data1)
    train, valid, test = data[0], data[1], data[2]
    s = "{'BC_class_name': 'BaseTorchGeometricModel', 'args': [{'BC_class_name': 'GINModel', 'args': [], 'kwargs': {'batch_size': 100, 'conv_radius': 3, 'conv_type': 'gin+', 'dataset': 'molpcba', 'dropout': 0.5, 'hidden': 100, 'layers': 3, 'lr': 0.001, 'optim': 'adam', 'task_type': 'classification', 'virtual_node': False}}], 'kwargs': {'auto_lr_find': True, 'batch_size': 16, 'epochs': 5, 'log': True, 'lr': 0.0001, 'pos_weight': 'balanced', 'preinitialized': False, 'representation': {'BC_class_name': 'TorchGeometricGraph', 'args': [], 'kwargs': {'atom_featurizer': {'BC_class_name': 'OGBAtomFeaturizer', 'args': [], 'kwargs': {}}, 'bond_featurizer': {'BC_class_name': 'OGBBondFeaturizer', 'args': [], 'kwargs': {}}}}}}"
    s = (
        s.replace("'", '"')
        .replace("True", "true")
        .replace("False", "false")
        .replace("None", "null")
    )
    model = oce.create_BC(s)

    model.fit(train["Smiles"], train["pChEMBL Value"])
    preds = model.predict(test["Smiles"])


# TypeError: unsupported operand type(s) for +: 'Mol2Vec' and 'DescriptastorusDescriptor'


def test_ConcatMol2Vec():
    oce.DescriptastorusDescriptor("morgan3counts") + oce.Mol2Vec()
    oce.Mol2Vec() + oce.DescriptastorusDescriptor("morgan3counts")

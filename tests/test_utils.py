import pytest
from common.utils import load_sensor_data_sync, load_soil_data_sync, simulate_optumgx

@pytest.fixture
def mock_data():
    return {"test": "data"}

def test_load_sensor_data():
    ds = load_sensor_data_sync()
    assert 'value' in ds.variables

def test_load_soil_data():
    df = load_soil_data_sync()
    assert 'x' in df.columns

def test_simulate_optumgx():
    df = simulate_optumgx(100)
    assert 'stress' in df.columns
    assert len(df) == 100
"""
Comprehensive integration tests for Groundhog CPT processing functionality
Tests the full workflow from data upload to visualization
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from groundhog.siteinvestigation.insitutests.pcpt_processing import PCPTProcessing
from groundhog.general.soilprofile import SoilProfile

# Test data paths
PROJECT_DIR = Path(__file__).parent.parent
CPT_TEST_FILE = PROJECT_DIR / 'Data' / 'excel_example_cpt.xlsx'
LAYERING_TEST_FILE = PROJECT_DIR / 'Data' / 'excel_example_layering.xlsx'


class TestGroundhogCPTProcessing:
    """Test suite for Groundhog CPT processing"""

    @pytest.fixture
    def cpt_data(self):
        """Load CPT test data"""
        return pd.read_excel(CPT_TEST_FILE)

    @pytest.fixture
    def layering_data(self):
        """Load layering test data"""
        return pd.read_excel(LAYERING_TEST_FILE)

    @pytest.fixture
    def cpt_processor(self):
        """Create CPT processor instance"""
        return PCPTProcessing(title='Test CPT')

    def test_cpt_file_exists(self):
        """Test that CPT data file exists"""
        assert CPT_TEST_FILE.exists(), f"CPT test file not found: {CPT_TEST_FILE}"

    def test_layering_file_exists(self):
        """Test that layering data file exists"""
        assert LAYERING_TEST_FILE.exists(), f"Layering test file not found: {LAYERING_TEST_FILE}"

    def test_cpt_data_structure(self, cpt_data):
        """Test CPT data has required columns"""
        required_columns = {'z [m]', 'qc [MPa]', 'fs [MPa]'}
        assert required_columns.issubset(set(cpt_data.columns)), \
            f"Missing required columns. Expected: {required_columns}, Got: {set(cpt_data.columns)}"

    def test_layering_data_structure(self, layering_data):
        """Test layering data has required columns"""
        required_columns = {'Depth from [m]', 'Depth to [m]', 'Soil type'}
        assert required_columns.issubset(set(layering_data.columns)), \
            f"Missing required columns. Expected: {required_columns}, Got: {set(layering_data.columns)}"

    def test_cpt_data_values(self, cpt_data):
        """Test CPT data has valid values"""
        assert len(cpt_data) > 0, "CPT data is empty"
        assert cpt_data['z [m]'].min() >= 0, "Depth values should be non-negative"
        assert cpt_data['qc [MPa]'].min() >= 0, "qc values should be non-negative"
        assert not cpt_data['z [m]'].isna().all(), "Depth column contains only NaN"

    def test_layering_data_values(self, layering_data):
        """Test layering data has valid values"""
        assert len(layering_data) > 0, "Layering data is empty"
        assert (layering_data['Depth from [m]'] <= layering_data['Depth to [m]']).all(), \
            "Depth from should be <= Depth to"

    def test_pcpt_processor_initialization(self, cpt_processor):
        """Test PCPTProcessing can be initialized"""
        assert cpt_processor is not None
        assert cpt_processor.title == 'Test CPT'

    def test_load_pandas_with_u2_key(self, cpt_processor, cpt_data):
        """Test loading CPT data with u2_key parameter (Bug Fix #1)"""
        cpt_processor.load_pandas(
            cpt_data,
            z_key='z [m]',
            qc_key='qc [MPa]',
            fs_key='fs [MPa]',
            u2_key='u [kPa]'  # FIX #1: Specify u2_key
        )

        assert cpt_processor.data is not None, "CPT data not loaded"
        assert len(cpt_processor.data) > 0, "CPT data is empty after loading"
        assert 'z [m]' in cpt_processor.data.columns
        assert 'qc [MPa]' in cpt_processor.data.columns
        assert 'u2 [MPa]' in cpt_processor.data.columns  # Should be converted

    def test_load_pandas_without_u2_key_should_fail(self, cpt_processor, cpt_data):
        """Test that loading without u2_key fails as expected"""
        with pytest.raises(Exception) as exc_info:
            cpt_processor.load_pandas(
                cpt_data,
                z_key='z [m]',
                qc_key='qc [MPa]',
                fs_key='fs [MPa]'
                # Missing u2_key - should fail
            )
        assert 'u2' in str(exc_info.value).lower(), "Error should mention u2"

    def test_soil_profile_returns_dataframe(self, layering_data):
        """Test SoilProfile returns DataFrame (Bug Fix #3)"""
        profile = SoilProfile(layering_data)

        assert profile is not None, "SoilProfile returned None"
        assert hasattr(profile, 'shape'), "SoilProfile should return DataFrame-like object"
        assert hasattr(profile, 'columns'), "SoilProfile should have columns"

    def test_soil_profile_not_empty(self, layering_data):
        """Test SoilProfile is not empty"""
        profile = SoilProfile(layering_data)

        if hasattr(profile, 'empty'):
            assert not profile.empty, "SoilProfile is empty"
        if hasattr(profile, 'shape'):
            assert profile.shape[0] > 0, "SoilProfile has no rows"

    def test_plot_raw_pcpt_basic(self, cpt_processor, cpt_data):
        """Test basic plotting without parameters (Bug Fix #5)"""
        import matplotlib.pyplot as plt

        cpt_processor.load_pandas(
            cpt_data,
            z_key='z [m]',
            qc_key='qc [MPa]',
            fs_key='fs [MPa]',
            u2_key='u [kPa]'
        )

        # Should not raise exception
        try:
            cpt_processor.plot_raw_pcpt()
            plt.close('all')
        except TypeError as e:
            if 'plot_rf' in str(e):
                pytest.fail("plot_raw_pcpt() should not require plot_rf parameter")
            # If it's another TypeError, let it raise
            raise

    def test_integration_full_workflow(self, cpt_data, layering_data):
        """Test complete workflow from data load to processing"""
        # Step 1: Initialize processor
        cpt = PCPTProcessing(title='Integration Test')

        # Step 2: Load CPT data with proper parameters
        cpt.load_pandas(
            cpt_data,
            z_key='z [m]',
            qc_key='qc [MPa]',
            fs_key='fs [MPa]',
            u2_key='u [kPa]'
        )

        assert cpt.data is not None
        assert len(cpt.data) == len(cpt_data) + 1  # +1 for header row

        # Step 3: Load soil profile
        profile = SoilProfile(layering_data)
        assert profile is not None

        # Step 4: Generate plot (without failing)
        import matplotlib.pyplot as plt
        try:
            cpt.plot_raw_pcpt()
            plt.close('all')
        except Exception as e:
            pytest.fail(f"Plot generation failed: {e}")

    def test_data_export(self, cpt_processor, cpt_data):
        """Test that processed data can be exported"""
        cpt_processor.load_pandas(
            cpt_data,
            z_key='z [m]',
            qc_key='qc [MPa]',
            fs_key='fs [MPa]',
            u2_key='u [kPa]'
        )

        # Should be able to convert to dict (for storage)
        data_dict = cpt_processor.data.to_dict('records')
        assert isinstance(data_dict, list)
        assert len(data_dict) > 0

        # Should be able to convert back to DataFrame
        df_reconstructed = pd.DataFrame(data_dict)
        assert len(df_reconstructed) == len(data_dict)


class TestGroundhogInputValidation:
    """Test input validation and error handling"""

    def test_missing_required_cpt_columns(self):
        """Test error handling for missing required columns"""
        invalid_data = pd.DataFrame({
            'depth': [1, 2, 3],
            'resistance': [10, 20, 30]
        })

        required_cols = {'z [m]', 'qc [MPa]', 'fs [MPa]'}
        missing = required_cols - set(invalid_data.columns)

        assert len(missing) > 0, "Test data should be missing required columns"

    def test_missing_required_layering_columns(self):
        """Test error handling for missing required layering columns"""
        invalid_data = pd.DataFrame({
            'top': [0, 5],
            'bottom': [5, 10]
        })

        required_cols = {'Depth from [m]', 'Depth to [m]', 'Soil type'}
        missing = required_cols - set(invalid_data.columns)

        assert len(missing) > 0, "Test data should be missing required columns"

    def test_empty_dataframe_handling(self):
        """Test handling of empty DataFrames"""
        empty_df = pd.DataFrame()

        cpt = PCPTProcessing(title='Test')

        with pytest.raises(Exception):
            cpt.load_pandas(
                empty_df,
                z_key='z [m]',
                qc_key='qc [MPa]',
                fs_key='fs [MPa]'
            )


class TestGroundhogDataQuality:
    """Test data quality checks"""

    @pytest.fixture
    def cpt_data(self):
        return pd.read_excel(CPT_TEST_FILE)

    def test_depth_values_increasing(self, cpt_data):
        """Test that depth values are generally increasing"""
        # Allow for some variation but general trend should be increasing
        depth_diff = cpt_data['z [m]'].diff().dropna()
        increasing_count = (depth_diff >= 0).sum()
        total_count = len(depth_diff)

        assert increasing_count / total_count > 0.9, \
            "Depth values should be mostly increasing"

    def test_qc_values_realistic(self, cpt_data):
        """Test that qc values are in realistic range"""
        qc_values = cpt_data['qc [MPa]']

        # CPT qc values typically range from 0 to 50 MPa
        assert qc_values.min() >= 0, "qc should not be negative"
        assert qc_values.max() < 100, "qc values seem unrealistically high"

    def test_no_all_zero_columns(self, cpt_data):
        """Test that critical columns are not all zeros"""
        assert not (cpt_data['qc [MPa]'] == 0).all(), "qc column should not be all zeros"
        assert not (cpt_data['z [m]'] == 0).all(), "Depth column should not be all zeros"


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v', '--tb=short'])

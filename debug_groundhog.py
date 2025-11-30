"""
Debug script for Groundhog CPT processing
This script tests the Groundhog functionality step-by-step to identify issues
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pandas as pd
import matplotlib.pyplot as plt
from groundhog.siteinvestigation.insitutests.pcpt_processing import PCPTProcessing
from groundhog.general.soilprofile import SoilProfile
import traceback

print("="*80)
print("GROUNDHOG DEBUG SCRIPT")
print("="*80)

# Step 1: Load CPT data
print("\n[STEP 1] Loading CPT data...")
try:
    cpt_df = pd.read_excel('Data/excel_example_cpt.xlsx')
    print(f"✓ CPT data loaded successfully")
    print(f"  Shape: {cpt_df.shape}")
    print(f"  Columns: {list(cpt_df.columns)}")
    print(f"\nFirst 5 rows:")
    print(cpt_df.head())
except Exception as e:
    print(f"✗ ERROR loading CPT data: {e}")
    traceback.print_exc()
    exit(1)

# Step 2: Load Layering data
print("\n[STEP 2] Loading Layering data...")
try:
    layering_df = pd.read_excel('Data/excel_example_layering.xlsx')
    print(f"✓ Layering data loaded successfully")
    print(f"  Shape: {layering_df.shape}")
    print(f"  Columns: {list(layering_df.columns)}")
    print(f"\nFirst 5 rows:")
    print(layering_df.head())
except Exception as e:
    print(f"✗ ERROR loading layering data: {e}")
    traceback.print_exc()
    exit(1)

# Step 3: Initialize PCPTProcessing
print("\n[STEP 3] Initializing PCPTProcessing...")
try:
    cpt = PCPTProcessing(title='CPT Process Debug')
    print(f"✓ PCPTProcessing initialized")
    print(f"  Object: {cpt}")
except Exception as e:
    print(f"✗ ERROR initializing PCPTProcessing: {e}")
    traceback.print_exc()
    exit(1)

# Step 4: Load pandas data into PCPTProcessing
print("\n[STEP 4] Loading pandas dataframe into PCPTProcessing...")
try:
    print(f"  Attempting to load with keys:")
    print(f"    z_key='z [m]'")
    print(f"    qc_key='qc [MPa]'")
    print(f"    fs_key='fs [MPa]'")
    print(f"    u2_key='u [kPa]'  <-- FIX: Specify u2_key parameter")

    cpt.load_pandas(cpt_df, z_key='z [m]', qc_key='qc [MPa]', fs_key='fs [MPa]', u2_key='u [kPa]')

    if cpt.data is None:
        print(f"✗ ERROR: cpt.data is None after loading")
        exit(1)
    else:
        print(f"✓ Data loaded into PCPTProcessing")
        print(f"  cpt.data type: {type(cpt.data)}")
        print(f"  cpt.data shape: {cpt.data.shape if hasattr(cpt.data, 'shape') else 'N/A'}")
        print(f"  cpt.data columns: {list(cpt.data.columns) if hasattr(cpt.data, 'columns') else 'N/A'}")
except Exception as e:
    print(f"✗ ERROR loading pandas data: {e}")
    traceback.print_exc()
    exit(1)

# Step 4b: Initialize SoilProfile BEFORE normalization
print("\n[STEP 4b] Initializing SoilProfile (required for normalization)...")
try:
    print(f"  Input dataframe shape: {layering_df.shape}")
    print(f"  Input dataframe columns: {list(layering_df.columns)}")

    profile = SoilProfile(layering_df)

    print(f"✓ SoilProfile initialized")
    print(f"  Profile object type: {type(profile)}")
    print(f"  Profile attributes: {[attr for attr in dir(profile) if not attr.startswith('_')][:15]}")

    # Check if it's actually a DataFrame (SoilProfile might return a DataFrame)
    if hasattr(profile, 'shape'):
        print(f"  Profile is a DataFrame with shape: {profile.shape}")
        print(f"  Profile columns: {list(profile.columns)}")
except Exception as e:
    print(f"✗ ERROR initializing SoilProfile: {e}")
    traceback.print_exc()
    exit(1)

# Step 4c: Map soil profile to CPT data
print("\n[STEP 4c] Mapping soil profile to CPT data...")
try:
    cpt.map_soilprofile(profile)
    print(f"✓ Soil profile mapped to CPT data")
    print(f"  cpt.data columns after mapping: {list(cpt.data.columns)}")
    if 'Soil type' in cpt.data.columns:
        print(f"  Unique soil types: {cpt.data['Soil type'].unique()}")
except Exception as e:
    print(f"✗ ERROR mapping soil profile: {e}")
    traceback.print_exc()
    print("\n  Note: This is expected if the workflow doesn't require mapping")
    print("  Continuing anyway...")

# Step 5: Normalize PCPT data
print("\n[STEP 5] Normalizing PCPT data...")
try:
    cpt.normalise_pcpt()
    print(f"✓ PCPT data normalized")
    print(f"  cpt.data columns after normalization: {list(cpt.data.columns)}")
except Exception as e:
    print(f"✗ ERROR normalizing PCPT: {e}")
    traceback.print_exc()
    print("\n  Note: Normalization requires soil profile data (total stress, etc.)")
    print("  Skipping normalization and continuing...")

# Step 6: Apply correlation
print("\n[STEP 6] Applying relative density correlation...")
try:
    print(f"  Correlation: relativedensity_ncsand_baldi")
    print(f"  Output: Dr [%]")
    print(f"  Soil types: Sand")

    cpt.apply_correlation(
        name="relativedensity_ncsand_baldi",
        outputs={"Dr": "Dr [%]"},
        apply_for_soiltypes=["Sand"]
    )
    print(f"✓ Correlation applied")
    print(f"  cpt.data columns after correlation: {list(cpt.data.columns)}")
except Exception as e:
    print(f"✗ ERROR applying correlation: {e}")
    traceback.print_exc()
    print("\n  Note: This might fail if 'Sand' soil type is not detected in data")
    print("  Continuing anyway...")

# Step 7: Plot raw PCPT
print("\n[STEP 7] Plotting raw PCPT data...")
try:
    fig, ax = plt.subplots(figsize=(10, 8))
    cpt.plot_raw_pcpt(plot_rf=True, zlines=[0, 5, 10])

    if fig is None:
        print(f"✗ ERROR: plot_raw_pcpt returned None")
    else:
        print(f"✓ Plot generated successfully")
        print(f"  Saving to 'debug_pcpt_plot.png'...")
        plt.savefig('debug_pcpt_plot.png', dpi=150, bbox_inches='tight')
        print(f"  ✓ Plot saved")
except Exception as e:
    print(f"✗ ERROR plotting PCPT: {e}")
    traceback.print_exc()

# Step 8: Check available methods
print("\n[STEP 8] Checking available PCPTProcessing methods...")
try:
    methods = [m for m in dir(cpt) if not m.startswith('_')]
    print(f"  Available methods ({len(methods)}):")
    for i, method in enumerate(methods[:20], 1):  # Show first 20
        print(f"    {i}. {method}")
    if len(methods) > 20:
        print(f"    ... and {len(methods) - 20} more")
except Exception as e:
    print(f"✗ ERROR listing methods: {e}")

# Step 9: Summary
print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print(f"✓ CPT data loaded: {cpt_df.shape}")
print(f"✓ Layering data loaded: {layering_df.shape}")
print(f"✓ PCPTProcessing initialized: {cpt.data is not None}")
print(f"✓ SoilProfile initialized: {profile.layering is not None if 'profile' in locals() else False}")
print("\nDebug complete. Check 'debug_pcpt_plot.png' for visualization.")
print("="*80)

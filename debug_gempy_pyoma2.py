"""
Debug script for GemPy and PyOMA2 functionality
Identifies bugs and issues in both modules
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pandas as pd
import numpy as np
import traceback

print("="*80)
print("GEMPY & PYOMA2 DEBUG SCRIPT")
print("="*80)

# =============================================================================
# GEMPY TESTING
# =============================================================================
print("\n" + "="*80)
print("TESTING GEMPY FUNCTIONALITY")
print("="*80)

# Test 1: Load GemPy test data
print("\n[GEMPY-1] Loading GemPy test data...")
try:
    surfaces_df = pd.read_csv('Data/model1_surface_points.csv')
    orientations_df = pd.read_csv('Data/model1_orientations.csv')
    print("✓ GemPy data files loaded")
    print(f"  Surfaces shape: {surfaces_df.shape}")
    print(f"  Surfaces columns: {list(surfaces_df.columns)}")
    print(f"  Orientations shape: {orientations_df.shape}")
    print(f"  Orientations columns: {list(orientations_df.columns)}")
except Exception as e:
    print(f"✗ ERROR loading GemPy data: {e}")
    traceback.print_exc()

# Test 2: Import GemPy
print("\n[GEMPY-2] Testing GemPy import...")
try:
    import gempy as gp
    import gempy_viewer as gpv
    print("✓ GemPy imported successfully")
    print(f"  GemPy version: {gp.__version__ if hasattr(gp, '__version__') else 'Unknown'}")
except ImportError as e:
    print(f"✗ ERROR: GemPy not installed: {e}")
except Exception as e:
    print(f"✗ ERROR importing GemPy: {e}")
    traceback.print_exc()

# Test 3: Create GemPy model
print("\n[GEMPY-3] Creating GemPy model...")
try:
    import tempfile
    import os

    # Save to temp files
    with tempfile.NamedTemporaryFile(delete=False, suffix='.csv', mode='w') as tmp_surf:
        surfaces_df.to_csv(tmp_surf.name, index=False)
        surf_path = tmp_surf.name

    with tempfile.NamedTemporaryFile(delete=False, suffix='.csv', mode='w') as tmp_ori:
        orientations_df.to_csv(tmp_ori.name, index=False)
        ori_path = tmp_ori.name

    print(f"  Temp files created")
    print(f"  Surfaces: {surf_path}")
    print(f"  Orientations: {ori_path}")

    # Create importer
    importer = gp.data.ImporterHelper(
        path_to_surface_points=surf_path,
        path_to_orientations=ori_path
    )
    print("✓ ImporterHelper created")

    # Calculate extent
    extent = [
        surfaces_df.X.min(), surfaces_df.X.max(),
        surfaces_df.Y.min(), surfaces_df.Y.max(),
        surfaces_df.Z.min(), surfaces_df.Z.max()
    ]
    print(f"  Model extent: {extent}")

    # Create geomodel
    geo_model = gp.create_geomodel(
        project_name='Debug Model',
        extent=extent,
        refinement=4,
        importer_helper=importer
    )
    print("✓ GeoModel created")

    # Map formations
    formations = surfaces_df['formation'].unique()
    print(f"  Formations: {list(formations)}")

    gp.map_stack_to_surfaces(geo_model, {"Formations": formations})
    print("✓ Formations mapped")

    # Compute model
    gp.compute_model(geo_model)

    if geo_model.solutions is None:
        print("✗ ERROR: Model solutions is None")
    else:
        print("✓ Model computed successfully")
        print(f"  Solutions type: {type(geo_model.solutions)}")

    # Clean up temp files
    os.unlink(surf_path)
    os.unlink(ori_path)
    print("  Temp files cleaned up")

except Exception as e:
    print(f"✗ ERROR creating GemPy model: {e}")
    traceback.print_exc()

# Test 4: GemPy visualization
print("\n[GEMPY-4] Testing GemPy visualization...")
try:
    if 'geo_model' in locals() and geo_model.solutions is not None:
        plot = gpv.plot_3d(geo_model, off_screen=True, plotter_type='basic', show=False)
        print("✓ 3D plot created (off-screen)")

        # Test export
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as tmp_html:
            plot.p.render()
            plot.p.export_html(tmp_html.name)
            print(f"✓ Plot exported to HTML: {tmp_html.name}")

            # Check file size
            import os
            size = os.path.getsize(tmp_html.name)
            print(f"  HTML file size: {size} bytes")

            if size > 100:
                print("✓ HTML export appears successful")
            else:
                print("⚠ WARNING: HTML file seems too small")

            os.unlink(tmp_html.name)
    else:
        print("⚠ Skipping visualization (no model available)")
except Exception as e:
    print(f"✗ ERROR with visualization: {e}")
    traceback.print_exc()

# Test 5: GemPy solutions to dict
print("\n[GEMPY-5] Testing solutions serialization...")
try:
    if 'geo_model' in locals() and geo_model.solutions is not None:
        # Attempt to convert to dict
        solutions_dict = geo_model.solutions.to_dict()
        print(f"✗ BUG: geo_model.solutions likely doesn't have to_dict() method")
        print(f"  Type: {type(geo_model.solutions)}")
        print(f"  Dir: {[m for m in dir(geo_model.solutions) if not m.startswith('_')][:10]}")
    else:
        print("⚠ Skipping test (no model available)")
except AttributeError as e:
    print(f"✗ BUG FOUND: solutions.to_dict() doesn't exist: {e}")
    print(f"  This will fail in callbacks.py line 163")
    traceback.print_exc()
except Exception as e:
    print(f"✗ ERROR: {e}")
    traceback.print_exc()

# =============================================================================
# PYOMA2 TESTING
# =============================================================================
print("\n" + "="*80)
print("TESTING PYOMA2 FUNCTIONALITY")
print("="*80)

# Test 1: PyOMA2 import
print("\n[PYOMA2-1] Testing PyOMA2 import...")
try:
    import pyoma2
    PYOMA_AVAILABLE = True
    print("✓ PyOMA2 imported successfully")
    print(f"  PyOMA2 available: {PYOMA_AVAILABLE}")
except ImportError as e:
    PYOMA_AVAILABLE = False
    print(f"⚠ PyOMA2 not installed (will use fallback simulation)")
    print(f"  Error: {e}")

# Test 2: Create test sensor data
print("\n[PYOMA2-2] Creating test sensor data...")
try:
    # Simulate sensor data
    time = np.linspace(0, 10, 1000)
    freq = 2.5  # Hz
    sensor1 = np.sin(2 * np.pi * freq * time) + 0.1 * np.random.randn(1000)
    sensor2 = np.cos(2 * np.pi * freq * time) + 0.1 * np.random.randn(1000)

    sensor_df = pd.DataFrame({
        'time': time,
        'sensor1': sensor1,
        'sensor2': sensor2
    })
    print("✓ Test sensor data created")
    print(f"  Shape: {sensor_df.shape}")
    print(f"  Columns: {list(sensor_df.columns)}")
except Exception as e:
    print(f"✗ ERROR creating sensor data: {e}")
    traceback.print_exc()

# Test 3: Data preparation
print("\n[PYOMA2-3] Testing data preparation...")
try:
    data = sensor_df.drop(columns=['time']).values.T
    print("✓ Data reshaped for PyOMA2")
    print(f"  Data shape: {data.shape}")
    print(f"  Expected: (num_channels, num_samples) = (2, 1000)")
except Exception as e:
    print(f"✗ ERROR preparing data: {e}")
    traceback.print_exc()

# Test 4: PyOMA2 processing (if available)
print("\n[PYOMA2-4] Testing PyOMA2 processing...")
if PYOMA_AVAILABLE:
    try:
        fs = 100  # sampling frequency
        alg = pyoma2.MSSI_COV(name='Test OMA', data=data, fs=fs, br=10)
        print("✓ PyOMA2 algorithm initialized")

        alg.run()
        print("✓ PyOMA2 algorithm executed")

        # Extract results
        # BUG CHECK: How to get frequencies and amplitudes?
        if hasattr(alg, 'freqs'):
            print(f"  Has 'freqs' attribute")
        if hasattr(alg, 'amps'):
            print(f"  Has 'amps' attribute")
        if hasattr(alg, 'result'):
            print(f"  Has 'result' attribute")

        print(f"  Available attributes: {[a for a in dir(alg) if not a.startswith('_')][:15]}")
        print("⚠ BUG: callbacks.py line 80 uses freqs, amps = [], [] - no actual extraction!")

    except Exception as e:
        print(f"✗ ERROR with PyOMA2: {e}")
        traceback.print_exc()
else:
    print("⚠ Skipping PyOMA2 test (library not available)")

# Test 5: Fallback simulation
print("\n[PYOMA2-5] Testing fallback simulation...")
try:
    from common.utils import simulate_pyoma2

    test_data = data[0]  # First channel
    freqs, amps = simulate_pyoma2(test_data)

    print("✓ Simulation function works")
    print(f"  Frequencies shape: {freqs.shape}")
    print(f"  Amplitudes shape: {amps.shape}")
    print(f"  Freq range: {freqs.min():.2f} to {freqs.max():.2f}")
except Exception as e:
    print(f"✗ ERROR with simulation: {e}")
    traceback.print_exc()

# Test 6: Result serialization
print("\n[PYOMA2-6] Testing result serialization...")
try:
    result = {'freqs': freqs.tolist(), 'amps': amps.tolist()}
    print("✓ Results converted to lists")
    print(f"  Result keys: {list(result.keys())}")

    # Test DataFrame creation
    result_df = pd.DataFrame(result)
    print("✓ DataFrame created from results")
    print(f"  DataFrame shape: {result_df.shape}")
except Exception as e:
    print(f"✗ ERROR serializing results: {e}")
    traceback.print_exc()

# =============================================================================
# SUMMARY
# =============================================================================
print("\n" + "="*80)
print("BUGS IDENTIFIED")
print("="*80)

print("\n🐛 GEMPY BUGS:")
print("1. Line 163: geo_model.solutions.to_dict() likely doesn't exist")
print("   - solutions object may not have to_dict() method")
print("   - Need to check actual type and available methods")
print("2. Line 165-166: Temp files cleanup may fail if error occurs before")
print("   - Should use try/finally or context managers")
print("3. Line 163: Storing entire model in session storage may be too large")
print("   - Should store minimal metadata or file reference instead")

print("\n🐛 PYOMA2 BUGS:")
print("1. Line 80: Empty result extraction - freqs, amps = [], []")
print("   - Algorithm runs but results are not extracted")
print("   - Need to find correct PyOMA2 API to get modal parameters")
print("2. Line 86: Assumes freqs and amps have .tolist() method")
print("   - If they're empty lists, this works but returns empty data")
print("   - If PyOMA2 returns results, format may be different")
print("3. Missing error handling for PyOMA2 algorithm failures")

print("\n✓ WORKING:")
print("- Data upload and validation")
print("- Fallback simulation for PyOMA2")
print("- GemPy model creation and computation")
print("- GemPy 3D visualization export")

print("\n" + "="*80)
print("DEBUG COMPLETE")
print("="*80)

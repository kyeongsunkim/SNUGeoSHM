# Enhanced standalone example for pyOMA2: Operational Modal Analysis.
# Uses real Palisaden building dataset for demonstration.
# Includes data loading, preprocessing, algorithm runs, and visualizations.
# Requires: pip install pyOMA-2 (may need additional deps like pyvista for 3D plots)
# Run this script to perform analysis and see plots.

import numpy as np
from pyoma2.algorithms import FSDD, SSIcov, pLSCF
from pyoma2.setup import SingleSetup
from pyoma2.support.utils.sample_data import get_sample_data

# Load real dataset (Palisaden building acceleration data)
data = np.load(get_sample_data(filename="Palisaden_dataset.npy", folder="palisaden"), allow_pickle=True)

# Create single setup instance with sampling frequency
Pali_ss = SingleSetup(data, fs=100)  # fs=100 Hz

# Load geometry files for visualization
_geo1 = get_sample_data(filename="Geo1.xlsx", folder="palisaden")  # 2D geometry
_geo2 = get_sample_data(filename="Geo2.xlsx", folder="palisaden")  # 3D geometry

Pali_ss.def_geo1_by_file(_geo1)
Pali_ss.def_geo2_by_file(_geo2)

# Plot geometries for verification
fig, ax = Pali_ss.plot_geo1()  # 2D plot
_ = Pali_ss.plot_geo2(scaleF=2)  # 3D with pyvista
_, _ = Pali_ss.plot_geo2_mpl(scaleF=2)  # 3D with matplotlib

# Plot raw time histories
_, _ = Pali_ss.plot_data()

# Plot channel info (TH, PSD, KDE) for last channel
_, _ = Pali_ss.plot_ch_info(ch_idx=[-1])

# Preprocess data: High-pass filter and decimate
Pali_ss.filter_data(Wn=(0.1), order=8, btype="highpass")  # Remove low-frequency noise
Pali_ss.decimate_data(q=5)  # Downsample by factor of 5
_, _ = Pali_ss.plot_ch_info(ch_idx=[-1])  # Verify preprocessing

# Initialize algorithms
fsdd = FSDD(name="FSDD", nxseg=1024, method_SD="cor")  # Frequency Domain Decomposition
ssicov = SSIcov(name="SSIcov", br=30, ordmax=30, calc_unc=True)  # Stochastic Subspace Identification
plscf = pLSCF(name="polymax", ordmax=30)  # Poly-reference Least Squares Complex Frequency

# Update parameters for FSDD
fsdd.run_params = FSDD.RunParamCls(nxseg=2048, method_SD="per", pov=0.5)  # Segment length, method, overlap

# Add algorithms to setup
Pali_ss.add_algorithms(ssicov, fsdd, plscf)

# Run algorithms by name
Pali_ss.run_by_name("SSIcov")
Pali_ss.run_by_name("FSDD")
Pali_ss.run_by_name("polymax")
# Alternatively: Pali_ss.run_all() to run everything

# Save results as dicts for further use/export
ssi_res = ssicov.result.model_dump()
fsdd_res = dict(fsdd.result)

# Visualize results
_, _ = fsdd.plot_CMIF(freqlim=(1,4))  # Singular values of PSD
_, _ = ssicov.plot_stab(freqlim=(1,4), hide_poles=False)  # Stabilization diagram
_, _ = ssicov.plot_freqvsdamp(freqlim=(1,4))  # Frequency vs damping
_, _ = plscf.plot_stab(freqlim=(1,4), hide_poles=False)  # pLSCF stabilization

# Modal parameter extraction (MPE) for selected frequencies
Pali_ss.mpe("SSIcov", sel_freq=[1.88, 2.42, 2.68], order_in=20)
ssi_res = dict(ssicov.result)  # Update results

Pali_ss.mpe("FSDD", sel_freq=[1.88, 2.42, 2.68], MAClim=0.95)
fsdd_res = dict(fsdd.result)  # Update results

# Additional plot for FSDD fit
_, _ = Pali_ss[fsdd.name].plot_EFDDfit(freqlim=(1,4))

# Mode shape visualizations
_, _ = Pali_ss.plot_mode_geo1(algo_res=fsdd.result, mode_nr=2, view="3D", scaleF=2)  # Plot mode 2 in 2D/3D
_ = Pali_ss.anim_mode_geo2(algo_res=ssicov.result, mode_nr=1, scaleF=3)  # Animate mode 1 in 3D
# Standalone example for GemPy: 3D geological modeling.
# This script demonstrates creating a simple faulted stratigraphic model,
# computing it, and visualizing in 2D/3D. Based on official tutorial.
# Requires: pip install gempy
# Run this script to see plots (may require a display backend like matplotlib).

import numpy as np
import gempy as gp
import gempy_viewer as gpv

# Define data path for remote input files
data_path = 'https://raw.githubusercontent.com/cgre-aachen/gempy_data/master/'

# Create the geological model with extent and refinement
geo_model = gp.create_geomodel(
    project_name='Tutorial_ch1_1_Basics',
    extent=[0, 2000, 0, 2000, 0, 750],  # X, Y, Z bounds
    refinement=6,  # Grid resolution level
    importer_helper=gp.data.ImporterHelper(
        path_to_orientations=data_path + "/data/input_data/getting_started/simple_fault_model_orientations.csv",
        path_to_surface_points=data_path + "/data/input_data/getting_started/simple_fault_model_points.csv",
        hash_surface_points="4cdd54cd510cf345a583610585f2206a2936a05faaae05595b61febfc0191563",
        hash_orientations="7ba1de060fc8df668d411d0207a326bc94a6cdca9f5fe2ed511fd4db6b3f3526"
    )
)

# Map geological surfaces to series (stratigraphic and fault)
gp.map_stack_to_surfaces(
    gempy_model=geo_model,
    mapping_object={
        "Fault_Series": 'Main_Fault',
        "Strat_Series": ('Sandstone_2', 'Siltstone', 'Shale', 'Sandstone_1')
    }
)

# Mark the fault series as a fault
gp.set_is_fault(
    frame=geo_model.structural_frame,
    fault_groups=['Fault_Series']
)

# Compute the model
sol = gp.compute_model(geo_model)

# Visualize 2D section with data points
gpv.plot_2d(
    geo_model,
    show_data=True,
    cell_number="mid",
    direction='y'  # Cross-section direction
)

# Visualize 3D model (basic plotter)
gpv.plot_3d(
    geo_model,
    show_data=False,
    image=False,
    plotter_type='basic'
)

# Add random topography for realism
gp.set_topography_from_random(
    grid=geo_model.grid,
    fractal_dimension=1.2,  # Controls terrain roughness
    d_z=np.array([350, 750]),  # Z-range for topography
    topography_resolution=np.array([50, 50]),  # Resolution of topo grid
)
# Recompute model with topography
gp.compute_model(geo_model)
gpv.plot_2d(geo_model, show_topography=True)
gpv.plot_3d(
    model=geo_model,
    plotter_type='basic',
    show_topography=True,
    show_surfaces=True,
    show_lith=True,  # Show lithology blocks
    image=False
)

# Example: Compute lithology at a specific point
x_i = np.array([[1000, 1000, 100]])  # XYZ coordinates
lith_values_at_coords = gp.compute_model_at(
    gempy_model=geo_model,
    at=x_i
)
print("Lithology at point:", lith_values_at_coords)
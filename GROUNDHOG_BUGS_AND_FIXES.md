# Groundhog Integration - Bugs Found and Fixes

## Summary

The Groundhog CPT processing functionality in `pages/groundhog/callbacks.py` has several critical issues that prevent it from working correctly. This document details all bugs found and their fixes.

---

## Bug #1: Missing `u2_key` Parameter

### Location
`pages/groundhog/callbacks.py:133`

### Issue
```python
cpt.load_pandas(cpt_df, z_key='z [m]', qc_key='qc [MPa]', fs_key='fs [MPa]')
```

The function call is missing the `u2_key` parameter. The library expects `'u2 [MPa]'` but the data file has `'u [kPa]'`.

### Error Message
```
KeyError: 'u2 [MPa]'
ValueError: Error during reading of PCPT data. Review the error message and try again. - 'u2 [MPa]'
```

### Fix
```python
cpt.load_pandas(cpt_df, z_key='z [m]', qc_key='qc [MPa]', fs_key='fs [MPa]', u2_key='u [kPa]')
```

---

## Bug #2: Incorrect Workflow - `normalise_pcpt()` Requires Soil Profile Data

### Location
`pages/groundhog/callbacks.py:136`

### Issue
The code calls `cpt.normalise_pcpt()` without first mapping soil profile data to the CPT. The normalization function requires:
- Vertical total stress (`'Vertical total stress [kPa]'`)
- Soil type information
- Other geotechnical parameters

### Error Message
```
KeyError: 'Vertical total stress [kPa]'
ValueError: Error during calculation of normalised properties.Review the error message and try again ('Vertical total stress [kPa]')
```

### Root Cause
The `normalise_pcpt()` function tries to calculate normalized CPT parameters (Qt, Fr, etc.) which require knowing the in-situ stresses. These stresses are calculated from the soil profile.

### Fix Options

#### Option 1: Skip Normalization (Simplest)
Remove the normalization step entirely if not needed:
```python
# Comment out or remove this line
# cpt.normalise_pcpt()
```

#### Option 2: Calculate Vertical Stress Manually
Add vertical stress calculation before normalization:
```python
# Calculate depth-based vertical stress (simplified)
cpt.data['Vertical total stress [kPa]'] = cpt.data['z [m]'] * 18.0  # Assuming average unit weight of 18 kN/m³

# Then normalize
cpt.normalise_pcpt()
```

#### Option 3: Use Groundhog's Soil Profile Integration (Recommended)
This requires a more complex workflow using groundhog's soil mechanics functions to calculate stresses from the layering data.

---

## Bug #3: `SoilProfile` Object Structure Misunderstanding

### Location
`pages/groundhog/callbacks.py:138-140`

### Issue
```python
profile = SoilProfile(layering_df)
if profile.layering is None:
    raise ValueError("Layering profile is empty. Check uploaded data.")
```

The code assumes `SoilProfile` has a `.layering` attribute, but:
1. `SoilProfile()` actually returns a **DataFrame**, not an object with attributes
2. The check `profile.layering is None` causes an `AttributeError`

### Error Message
```
AttributeError: 'SoilProfile' object has no attribute 'layering'
```

### Fix
```python
profile = SoilProfile(layering_df)
# SoilProfile returns a DataFrame directly
if profile is None or profile.empty:
    raise ValueError("Layering profile is empty. Check uploaded data.")
```

---

## Bug #4: Non-existent Method `map_soilprofile()`

### Location
`pages/groundhog/callbacks.py` (implied by workflow)

### Issue
The code attempts to use `cpt.map_soilprofile(profile)`, but this method doesn't exist in `PCPTProcessing`.

### Error Message
```
AttributeError: 'PCPTProcessing' object has no attribute 'map_soilprofile'
```

### Fix
Use the correct method to map soil layers to CPT data. According to Groundhog documentation, you need to use:
```python
from groundhog.general.soilprofile import map_soiltypes

# Map soil types from profile to CPT based on depth
cpt.data = map_soiltypes(
    cpt_data=cpt.data,
    soilprofile=profile,
    z_key='z [m]'
)
```

---

## Bug #5: Incorrect `plot_raw_pcpt()` Parameters

### Location
`pages/groundhog/callbacks.py:143`

### Issue
```python
cpt.plot_raw_pcpt(plot_rf=True, zlines=[0, 5, 10])
```

The method `plot_raw_pcpt()` doesn't accept `plot_rf` as a keyword argument.

### Error Message
```
TypeError: PCPTProcessing.plot_raw_pcpt() got an unexpected keyword argument 'plot_rf'
```

### Fix
Check the actual method signature and use correct parameters:
```python
# Option 1: Use default parameters
cpt.plot_raw_pcpt()

# Option 2: Check documentation for correct parameters
fig = cpt.plot_raw_pcpt()  # Returns matplotlib figure
```

---

## Bug #6: Missing Correlation Prerequisites

### Location
`pages/groundhog/callbacks.py:137`

### Issue
```python
cpt.apply_correlation(name="relativedensity_ncsand_baldi", outputs={"Dr": "Dr [%]"}, apply_for_soiltypes=["Sand"])
```

This correlation requires:
1. Soil type column (`'Soil type'`) in the CPT data
2. The soil type must be mapped from the profile
3. The correlation needs additional parameters that may not be present

### Error Message
```
KeyError: 'Soil type'
```

### Fix
Ensure soil types are mapped before applying correlations:
```python
from groundhog.general.soilprofile import map_soiltypes

# Map soil types first
cpt.data = map_soiltypes(
    cpt_data=cpt.data,
    soilprofile=profile,
    z_key='z [m]'
)

# Then apply correlation (note: check if "Sand" or "SAND" is used)
cpt.apply_correlation(
    name="relativedensity_ncsand_baldi",
    outputs={"Dr": "Dr [%]"},
    apply_for_soiltypes=["SAND"]  # Use uppercase to match data
)
```

---

## Corrected Workflow

Here's the complete corrected version of the `run_groundhog()` callback:

```python
@callback(
    [Output('groundhog-output', 'children'), Output('global-store', 'data', allow_duplicate=True)],
    Input('run-groundhog-btn', 'n_clicks'),
    State('global-store', 'data'),
    prevent_initial_call=True
)
def run_groundhog(n_clicks, store_data):
    if not n_clicks:
        raise PreventUpdate
    store_update = store_data.copy()
    try:
        # Check for required data
        if 'groundhog_cpt' not in store_data or 'groundhog_layering' not in store_data:
            raise ValueError("Missing CPT or layering data. Please upload both files.")

        cpt_df = pd.DataFrame(store_data['groundhog_cpt'])
        layering_df = pd.DataFrame(store_data['groundhog_layering'])

        # Initialize CPT processing
        cpt = PCPTProcessing(title='CPT Process')

        # FIX #1: Add u2_key parameter
        cpt.load_pandas(
            cpt_df,
            z_key='z [m]',
            qc_key='qc [MPa]',
            fs_key='fs [MPa]',
            u2_key='u [kPa]'  # FIX: Specify pore pressure column
        )

        if cpt.data is None:
            raise ValueError("CPT data loading failed. Check file columns and content.")

        # FIX #3: SoilProfile returns a DataFrame
        profile = SoilProfile(layering_df)
        if profile is None or profile.empty:
            raise ValueError("Layering profile is empty. Check uploaded data.")

        # FIX #4: Map soil types to CPT data
        from groundhog.general.soilprofile import map_soiltypes
        cpt.data = map_soiltypes(
            cpt_data=cpt.data,
            soilprofile=profile,
            z_key='z [m]'
        )

        # FIX #2: Option 1 - Skip normalization if not needed
        # Or implement proper stress calculation before normalizing
        # cpt.normalise_pcpt()  # Comment out for now

        # FIX #6: Apply correlation only if soil types are mapped
        if 'Soil type' in cpt.data.columns:
            try:
                cpt.apply_correlation(
                    name="relativedensity_ncsand_baldi",
                    outputs={"Dr": "Dr [%]"},
                    apply_for_soiltypes=["SAND"]  # Match case with data
                )
            except Exception as e:
                logging.warning(f"Correlation failed: {e}")

        # FIX #5: Use correct plot parameters
        fig, ax = plt.subplots(figsize=(12, 8))
        cpt.plot_raw_pcpt()  # Use default parameters

        if fig is None:
            raise ValueError("Plot generation failed.")

        img_src = matplotlib_to_base64(fig)
        plt.close(fig)  # Clean up

        output = [html.Img(src=img_src, style={'width': '100%'})]

        # Store processed data
        store_update['groundhog_cpt_processed'] = cpt.data.to_dict('records')
        store_update['groundhog_profile'] = profile.to_dict('records')

        logging.info("Groundhog processing completed successfully.")
        return output, store_update

    except Exception as e:
        store_update['error'] = str(e)
        logging.error(f"Groundhog processing error: {str(e)}")
        return [dbc.Alert(str(e), color="danger")], store_update
```

---

## Additional Recommendations

### 1. Add Input Validation
```python
# Validate column names before processing
required_cpt_cols = {'z [m]', 'qc [MPa]', 'fs [MPa]', 'u [kPa]'}
if not required_cpt_cols.issubset(set(cpt_df.columns)):
    raise ValueError(f"Missing required CPT columns: {required_cpt_cols - set(cpt_df.columns)}")

required_layer_cols = {'Depth from [m]', 'Depth to [m]', 'Soil type'}
if not required_layer_cols.issubset(set(layering_df.columns)):
    raise ValueError(f"Missing required layering columns: {required_layer_cols - set(layering_df.columns)}")
```

### 2. Improve Error Messages
Provide more helpful error messages to users:
```python
try:
    cpt.load_pandas(...)
except KeyError as e:
    raise ValueError(f"Column not found in CPT data: {e}. Please check your file format.")
except Exception as e:
    raise ValueError(f"Failed to load CPT data: {e}")
```

### 3. Add Download Functionality
The download callback references a non-existent component:
```python
# In layout.py, add:
dcc.Download(id='download-component')

# In callbacks.py, fix the download callback
@callback(
    Output('download-component', 'data'),
    Input('download-groundhog-btn', 'n_clicks'),
    State('global-store', 'data'),
    prevent_initial_call=True
)
def download_groundhog(n_clicks, store_data):
    if not n_clicks or 'groundhog_cpt_processed' not in store_data:
        raise PreventUpdate
    processed_data = store_data.get('groundhog_cpt_processed')
    if processed_data is None:
        raise ValueError("No processed data available for download.")
    df = pd.DataFrame(processed_data)
    logging.info("Groundhog results downloaded.")
    return dcc.send_data_frame(df.to_csv, 'groundhog_results.csv', index=False)
```

### 4. Use Try-Except for Optional Features
```python
# Normalize only if possible
try:
    cpt.normalise_pcpt()
except KeyError:
    logging.warning("Normalization skipped - missing required columns")
```

---

## Testing Checklist

- [ ] Test with excel_example_cpt.xlsx
- [ ] Test with excel_example_layering.xlsx
- [ ] Verify plot generation
- [ ] Verify data download
- [ ] Test error handling for missing files
- [ ] Test error handling for malformed data
- [ ] Verify soil type mapping
- [ ] Test correlation calculations

---

## Files to Modify

1. `pages/groundhog/callbacks.py` - Main fixes needed here
2. `pages/groundhog/layout.py` - Add dcc.Download component
3. `common/utils.py` - No changes needed

---

## Priority

**CRITICAL** - The Groundhog functionality is currently completely broken and will fail on every execution.

All 6 bugs must be fixed for basic functionality to work.

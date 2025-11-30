# Dash App Architecture - Complete Guide

## 📘 Table of Contents

1. [Core Concepts](#core-concepts)
2. [App Structure](#app-structure)
3. [How Callbacks Work](#how-callbacks-work)
4. [Page Mechanisms](#page-mechanisms)
5. [Data Flow](#data-flow)
6. [Real Examples](#real-examples)

---

## 🎯 Core Concepts

### What is Dash?

Dash is a **reactive web framework** built on top of:
- **Flask** (Python web server)
- **React** (JavaScript UI framework)
- **Plotly** (Visualization library)

**Key Principle:** Write Python, get a reactive web app!

### The Reactive Pattern

```
User Action → Component → Callback → Update Other Components → UI Re-renders
```

**Example:**
```python
User clicks button → Button's n_clicks changes → Callback triggered →
Update graph → Browser re-renders graph
```

---

## 🏗️ App Structure

### File Organization

```
SNUGeoSHM/
├── app.py                    # Main application file
├── pages/                    # Individual page modules
│   ├── groundhog/
│   │   ├── __init__.py      # Register page with Dash
│   │   ├── layout.py        # Define UI components
│   │   └── callbacks.py     # Define interactivity
│   ├── gempy/
│   └── pyoma2/
├── common/                   # Shared utilities
│   ├── navbar.py
│   ├── utils.py
│   └── constants.py
└── Data/                     # Data files
```

### Main Application (app.py)

```python
# Line 21: Create Dash app instance
app = dash.Dash(
    __name__,
    use_pages=True,  # ← Enable multi-page support
    suppress_callback_exceptions=True  # ← Allow cross-page callbacks
)

# Line 55-78: App layout
app.layout = dbc.Container([
    navbar,                              # Navigation bar
    dash.page_container,                 # ← Pages render here
    dcc.Store(id='global-store'),        # ← Shared data storage
    dcc.Download(id='download-component') # ← File downloads
])
```

**Key Components:**

1. **`dash.page_container`**: Placeholder where page content renders
2. **`dcc.Store`**: Browser-side data storage (like a global variable)
3. **`dcc.Download`**: Handles file downloads

---

## ⚙️ How Callbacks Work

### Anatomy of a Callback

```python
@callback(
    # OUTPUTS: What components to update
    [
        Output("component-id", "property"),
        Output("another-id", "property")
    ],
    # INPUTS: What triggers this callback
    Input("button-id", "n_clicks"),
    # STATES: Read values without triggering
    State("input-id", "value"),
    prevent_initial_call=True  # Don't run on page load
)
def my_callback(n_clicks, input_value):
    # Your logic here
    return "new value for component", "new value for another"
```

### The Three Types of Arguments

#### 1. **Output** - What to Update
```python
Output("my-graph", "figure")
#      ↑ component ID   ↑ property to update
```

#### 2. **Input** - What Triggers the Callback
```python
Input("upload-button", "contents")
#     ↑ component ID    ↑ property to watch
```
Callback runs **whenever this property changes**.

#### 3. **State** - Read Without Triggering
```python
State("text-input", "value")
#     ↑ component ID  ↑ property to read
```
Callback reads this value but **doesn't run when it changes**.

### Example: Upload → Process → Display

```python
@callback(
    Output("output-div", "children"),     # What to update
    Input("upload-data", "contents"),      # Trigger: file upload
    State("upload-data", "filename"),      # Read filename (don't trigger)
    prevent_initial_call=True
)
def handle_upload(contents, filename):
    # contents changes when user uploads file
    # filename is just read for information

    if contents is None:
        return "No file uploaded"

    df = process_file(contents, filename)
    return f"Uploaded {filename} with {len(df)} rows"
```

**Flow:**
1. User uploads file
2. `contents` property changes
3. Callback triggered
4. Function runs
5. Returns new value
6. `output-div` children updated
7. Browser re-renders

---

## 📄 Page Mechanisms

### How Multi-Page Works

#### Step 1: Register Page (`pages/groundhog/__init__.py`)

```python
import dash
from dash import html, dcc

# Register this as a page
dash.register_page(__name__, path='/groundhog')

# Import layout and callbacks
from .layout import layout
from . import callbacks  # Side-effect import: registers callbacks
```

**What happens:**
- `dash.register_page()` tells Dash "this is a page"
- `path='/groundhog'` makes it accessible at `/groundhog`
- Layout function returns UI components
- Callbacks module registers interactivity

#### Step 2: Define Layout (`pages/groundhog/layout.py`)

```python
def layout():
    """Returns the UI components for this page"""
    return dbc.Card([
        html.H2("Groundhog CPT Processing"),

        # File upload component
        dcc.Upload(
            id="upload-groundhog-cpt",  # ← Unique ID
            children=dbc.Button("Upload CPT Data")
        ),

        # Display upload status
        html.Div(id="upload-groundhog-cpt-status"),

        # Data table
        dash_table(id="groundhog-cpt-data-table"),

        # Process button
        dbc.Button("Process", id="run-groundhog-btn"),

        # Output area
        html.Div(id="groundhog-output")
    ])
```

**Component IDs:**
- Must be **unique across entire app**
- Used to reference components in callbacks
- Convention: `page-purpose-component`

#### Step 3: Define Callbacks (`pages/groundhog/callbacks.py`)

Let's break down a real callback from the fixed Groundhog page:

```python
@callback(
    # OUTPUTS: What gets updated
    [
        Output("upload-groundhog-cpt-status", "children"),  # Status message
        Output('global-store', 'data', allow_duplicate=True),  # Save to storage
        Output("groundhog-cpt-data-table", "data"),  # Table data
        Output("groundhog-cpt-data-table", "columns"),  # Table columns
        Output("groundhog-cpt-data-viz", "figure"),  # Visualization
    ],
    # INPUT: File upload triggers this
    Input("upload-groundhog-cpt", "contents"),
    # STATES: Additional info we need
    State("upload-groundhog-cpt", "filename"),
    State("global-store", "data"),  # Existing global data
    prevent_initial_call=True
)
def handle_groundhog_cpt_upload(contents, filename, store_data):
    """
    This runs when user uploads a file

    Args:
        contents: Base64 encoded file data (from Input)
        filename: Name of uploaded file (from State)
        store_data: Current global storage dict (from State)

    Returns:
        Tuple of 5 values matching the 5 Outputs above
    """
    try:
        # 1. Process uploaded file
        df = process_uploaded_file(contents, filename)

        # 2. Validate data
        required_cols = {'z [m]', 'qc [MPa]', 'fs [MPa]'}
        if not required_cols.issubset(set(df.columns)):
            raise ValueError(f"Missing columns!")

        # 3. Update global storage
        store_update = store_data.copy()
        store_update['groundhog_cpt'] = df.to_dict('records')

        # 4. Prepare table display
        columns = [{"name": col, "id": col} for col in df.columns]

        # 5. Create visualization
        fig = px.line(df, x="z [m]", y="qc [MPa]", title="CPT Data")

        # 6. Return all outputs IN ORDER
        return (
            dbc.Alert(f"{filename} uploaded.", color="success"),  # Status
            store_update,  # Global storage
            df.to_dict('records'),  # Table data
            columns,  # Table columns
            fig  # Visualization
        )

    except Exception as e:
        # On error, return safe defaults
        return (
            dbc.Alert(str(e), color="danger"),
            store_data,  # Don't modify storage
            [],  # Empty table
            [],
            go.Figure()  # Empty figure
        )
```

**Execution Flow:**

```
1. User selects file
   ↓
2. Browser uploads file
   ↓
3. "upload-groundhog-cpt" contents changes
   ↓
4. Callback triggered
   ↓
5. Function receives: (contents, filename, store_data)
   ↓
6. Process file → create table → make graph
   ↓
7. Return 5 values
   ↓
8. Dash updates 5 components
   ↓
9. Browser re-renders changed components
```

---

## 🔄 Data Flow Patterns

### Pattern 1: Upload → Store → Process

**Common in all pages:**

```python
# Callback 1: Upload file → Store in global-store
@callback(
    Output('global-store', 'data'),
    Input('upload-button', 'contents')
)
def store_data(contents):
    df = process_file(contents)
    return {'my_data': df.to_dict('records')}

# Callback 2: Process button → Read from global-store → Display
@callback(
    Output('output-div', 'children'),
    Input('process-button', 'n_clicks'),
    State('global-store', 'data')
)
def process_data(n_clicks, store_data):
    df = pd.DataFrame(store_data['my_data'])
    # Process df
    return result
```

### Pattern 2: Chained Callbacks

```python
# First callback
@callback(
    Output('intermediate-data', 'data'),
    Input('button1', 'n_clicks')
)
def step1(n):
    return {'processed': True}

# Second callback (triggered by first)
@callback(
    Output('final-output', 'children'),
    Input('intermediate-data', 'data')  # ← Triggered by step1's output
)
def step2(data):
    if data['processed']:
        return "Done!"
```

### Pattern 3: Multiple Inputs

```python
@callback(
    Output('result', 'children'),
    [
        Input('input1', 'value'),
        Input('input2', 'value'),
        Input('input3', 'value')
    ]
)
def combine_inputs(val1, val2, val3):
    # Runs when ANY input changes
    return f"{val1} + {val2} + {val3}"
```

---

## 📊 Real Example: Groundhog CPT Processing

Let's trace the **complete user journey** through the Groundhog page:

### Step 1: User Loads Page

```
URL: http://localhost:8050/groundhog
      ↓
Dash routes to pages/groundhog/__init__.py
      ↓
Calls layout() function
      ↓
Returns UI components
      ↓
Browser renders page
```

### Step 2: User Uploads CPT File

**UI Components Involved:**
```python
# From layout.py:
dcc.Upload(
    id="upload-groundhog-cpt",
    children=dbc.Button("Upload excel_example_cpt.xlsx")
)
html.Div(id="upload-groundhog-cpt-status")
dash_table(id="groundhog-cpt-data-table")
```

**Callback Triggered:**
```python
# From callbacks.py:
@callback(
    Output("upload-groundhog-cpt-status", "children"),
    Output("groundhog-cpt-data-table", "data"),
    # ... more outputs
    Input("upload-groundhog-cpt", "contents"),  # ← This changed!
    State("upload-groundhog-cpt", "filename"),
)
def handle_groundhog_cpt_upload(contents, filename, ...):
```

**What Happens:**
1. User selects `excel_example_cpt.xlsx`
2. Browser reads file → Base64 encodes → Sets to `contents`
3. `contents` property changes
4. Callback `handle_groundhog_cpt_upload()` runs
5. Function processes file:
   ```python
   df = pd.read_excel(BytesIO(base64.b64decode(contents)))
   ```
6. Validates columns (z, qc, fs, u)
7. Stores in `global-store`
8. Returns 5 values
9. Dash updates 5 components
10. Page shows: ✓ "file uploaded", data table, graph

### Step 3: User Clicks "Process CPT"

**UI Components:**
```python
dbc.Button("Process CPT", id="run-groundhog-btn")
html.Div(id="groundhog-output")
```

**Callback Triggered:**
```python
@callback(
    Output('groundhog-output', 'children'),
    Output('global-store', 'data', allow_duplicate=True),
    Input('run-groundhog-btn', 'n_clicks'),  # ← Button clicked!
    State('global-store', 'data')  # Read uploaded data
)
def run_groundhog(n_clicks, store_data):
    # 1. Get data from storage
    cpt_df = pd.DataFrame(store_data['groundhog_cpt'])
    layering_df = pd.DataFrame(store_data['groundhog_layering'])

    # 2. Initialize Groundhog processor
    cpt = PCPTProcessing(title='CPT Process')

    # 3. Load data with FIXED u2_key parameter
    cpt.load_pandas(
        cpt_df,
        z_key='z [m]',
        qc_key='qc [MPa]',
        fs_key='fs [MPa]',
        u2_key='u [kPa]'  # ← BUG FIX #1
    )

    # 4. Create soil profile
    profile = SoilProfile(layering_df)

    # 5. Generate plot
    cpt.plot_raw_pcpt()  # ← BUG FIX #5 (no parameters)

    # 6. Convert plot to image
    img_src = matplotlib_to_base64(plt.gcf())

    # 7. Return HTML with image
    return html.Img(src=img_src), store_update
```

**Result:** Page displays CPT profile plot

---

## 🗃️ Global Storage (`dcc.Store`)

### What is dcc.Store?

**Browser-side data storage** - like a Python dict that persists in the browser.

```python
# In app.py layout:
dcc.Store(id='global-store', data={})
```

### How It Works

```python
# Writing to storage
@callback(
    Output('global-store', 'data'),
    Input('button', 'n_clicks')
)
def save_data(n):
    return {
        'groundhog_cpt': [...],
        'gempy_surfaces': [...],
        'user_name': 'Alice'
    }

# Reading from storage
@callback(
    Output('display', 'children'),
    Input('other-button', 'n_clicks'),
    State('global-store', 'data')  # ← Read stored data
)
def use_data(n, store_data):
    cpt_data = store_data.get('groundhog_cpt', [])
    return f"Found {len(cpt_data)} CPT points"
```

### Current Storage Structure

```python
{
    # Groundhog data
    'groundhog_cpt': [...],  # CPT data records
    'groundhog_layering': [...],  # Soil layers
    'groundhog_cpt_processed': [...],  # Processed results

    # GemPy data
    'gempy_surfaces': [...],
    'gempy_orientations': [...],
    'gempy_model': {  # ← Fixed: metadata only
        'computed': True,
        'n_formations': 2,
        'extent': [...]
    },

    # PyOMA2 data
    'pyoma2_data': [...],
    'pyoma2_result': {
        'freqs': [...],
        'amps': [...]
    },

    # Errors
    'error': 'Error message if any'
}
```

### `allow_duplicate=True`

When multiple callbacks update the same output:

```python
@callback(
    Output('global-store', 'data'),  # First callback
    Input('upload1', 'contents')
)
def save_upload1(contents):
    return {'data1': contents}

@callback(
    Output('global-store', 'data', allow_duplicate=True),  # ← Add this!
    Input('upload2', 'contents')
)
def save_upload2(contents):
    return {'data2': contents}
```

Without `allow_duplicate=True`, Dash throws an error.

---

## 🔍 Component Types

### Input Components

#### `dcc.Upload` - File Upload
```python
dcc.Upload(
    id='upload-data',
    children=dbc.Button('Upload File'),
    multiple=False  # Single file only
)
```

**Properties:**
- `contents`: Base64 encoded file data
- `filename`: Original filename
- `last_modified`: Timestamp

#### `dbc.Input` - Text Input
```python
dbc.Input(
    id='material-input',
    type='number',
    value=100,
    min=0,
    max=1000
)
```

#### `dbc.Button` - Button
```python
dbc.Button(
    "Process CPT",
    id="run-groundhog-btn",
    color="success"
)
```

**Property to watch:** `n_clicks` (increments each click)

### Output Components

#### `html.Div` - Container
```python
html.Div(
    id="output-div",
    children="Initial content"
)
```

**Common properties:**
- `children`: Content (text, components, lists)
- `style`: CSS styling dict
- `className`: CSS class

#### `dcc.Graph` - Plotly Graph
```python
dcc.Graph(
    id="my-graph",
    figure=px.line(df, x='x', y='y')
)
```

**Property:** `figure` (Plotly figure object)

#### `dash_table.DataTable` - Data Table
```python
dash_table(
    id="data-table",
    data=df.to_dict('records'),
    columns=[{"name": i, "id": i} for i in df.columns],
    editable=True,
    row_deletable=True
)
```

**Properties:**
- `data`: List of dicts (rows)
- `columns`: List of column definitions
- `editable`: Allow cell editing
- `selected_rows`: Currently selected rows

#### `html.Iframe` - Embedded Content
```python
html.Iframe(
    src='/assets/gempy_3d.html',
    style={"width": "100%", "height": "600px"}
)
```

---

## ⚠️ Common Patterns & Pitfalls

### ✅ Good: Handling Missing Data

```python
@callback(
    Output('result', 'children'),
    Input('button', 'n_clicks'),
    State('global-store', 'data')
)
def process(n, store_data):
    if not n:  # Button not clicked yet
        raise PreventUpdate  # Don't run

    if 'my_data' not in store_data:
        return dbc.Alert("Upload data first!", color="warning")

    # Process...
```

### ❌ Bad: Not Handling Errors

```python
@callback(...)
def bad_callback(n, store_data):
    df = pd.DataFrame(store_data['data'])  # ← Crashes if 'data' missing!
    # No try/except = user sees error page
```

### ✅ Good: Return Matching Outputs

```python
@callback(
    [Output('out1', 'children'), Output('out2', 'children')],
    Input('btn', 'n_clicks')
)
def good():
    return "Value 1", "Value 2"  # ✓ 2 values for 2 outputs
```

### ❌ Bad: Mismatched Returns

```python
@callback(
    [Output('out1', 'children'), Output('out2', 'children')],
    Input('btn', 'n_clicks')
)
def bad():
    return "Only one value"  # ✗ Error! Need 2 values
```

### ✅ Good: Preserve State on Error

```python
@callback(
    Output('global-store', 'data'),
    Input('upload', 'contents'),
    State('global-store', 'data')
)
def upload(contents, store_data):
    try:
        new_data = process(contents)
        store_update = store_data.copy()  # ✓ Copy existing
        store_update['new_key'] = new_data
        return store_update
    except Exception as e:
        return store_data  # ✓ Return unchanged on error
```

---

## 🎓 Advanced Concepts

### Prevent Initial Call

```python
@callback(
    ...,
    prevent_initial_call=True  # Don't run when page loads
)
```

**When to use:**
- Buttons (no initial click)
- File uploads (no initial file)
- Processing functions (need user action first)

### Clientside Callbacks

Run JavaScript instead of Python (faster!):

```python
app.clientside_callback(
    """
    function(n_clicks) {
        // JavaScript code
        return 'Clicked ' + n_clicks + ' times';
    }
    """,
    Output('output', 'children'),
    Input('button', 'n_clicks')
)
```

**Used for:**
- Theme switching
- Simple UI updates
- Export buttons (download without server)

### Background Callbacks

Long-running tasks:

```python
@callback(
    ...,
    background=True,
    running=[Output('button', 'disabled', True)],
    cancel=[Input('cancel-button', 'n_clicks')]
)
def long_task(n):
    # Runs in background
    time.sleep(60)  # Won't block other callbacks
    return result
```

---

## 📝 Summary

### Key Takeaways

1. **Callbacks = Reactivity**: User action → Callback → Update UI
2. **Component IDs = References**: Unique IDs connect layout to callbacks
3. **Input triggers, State doesn't**: Inputs run callbacks, States just read
4. **Return order matters**: Must match Output order exactly
5. **global-store = Shared data**: Store data between callbacks
6. **Error handling = UX**: Always handle errors gracefully

### Typical Page Flow

```
1. User loads page
   → layout() function renders UI

2. User interacts (upload, click, type)
   → Component property changes
   → Callback with matching Input triggers
   → Function runs with Input/State values
   → Returns new values
   → Outputs update
   → UI re-renders

3. Repeat for each interaction
```

### The Three Questions for Any Callback

1. **What triggers it?** → Look at `Input(...)`
2. **What does it read?** → Look at `State(...)`
3. **What does it update?** → Look at `Output(...)`

---

## 🔗 Additional Resources

- **Dash Documentation**: https://dash.plotly.com/
- **Dash Bootstrap Components**: https://dash-bootstrap-components.opensource.faculty.ai/
- **Plotly Express**: https://plotly.com/python/plotly-express/

---

**Generated:** 2025-12-01
**Purpose:** Understanding Dash app architecture for SNUGeoSHM project

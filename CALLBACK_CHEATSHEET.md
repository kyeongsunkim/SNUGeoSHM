# Dash Callback Cheatsheet

Quick reference for common callback patterns in the SNUGeoSHM dashboard.

---

## 🎯 Basic Callback Template

```python
from dash import callback, Input, Output, State
from dash.exceptions import PreventUpdate

@callback(
    Output('output-component-id', 'property-name'),
    Input('trigger-component-id', 'property-name'),
    State('read-component-id', 'property-name'),
    prevent_initial_call=True
)
def my_callback_function(trigger_value, read_value):
    # Your logic here
    return new_value_for_output
```

---

## 📤 File Upload Pattern

```python
@callback(
    [
        Output('status-message', 'children'),
        Output('global-store', 'data', allow_duplicate=True),
        Output('data-table', 'data')
    ],
    Input('upload-component', 'contents'),
    State('upload-component', 'filename'),
    State('global-store', 'data'),
    prevent_initial_call=True
)
def handle_upload(contents, filename, store_data):
    try:
        # 1. Decode and process file
        df = process_uploaded_file(contents, filename)

        # 2. Validate
        if df is None or len(df) == 0:
            raise ValueError("Empty file")

        # 3. Store in global storage
        store_update = store_data.copy()
        store_update['my_data'] = df.to_dict('records')

        # 4. Return success
        return (
            dbc.Alert(f"✓ {filename} uploaded", color="success"),
            store_update,
            df.to_dict('records')
        )

    except Exception as e:
        # Return error state
        return (
            dbc.Alert(f"✗ Error: {e}", color="danger"),
            store_data,  # Don't modify storage
            []  # Empty table
        )
```

---

## 🔘 Button Click Pattern

```python
@callback(
    Output('result-div', 'children'),
    Input('process-button', 'n_clicks'),
    State('global-store', 'data'),
    prevent_initial_call=True
)
def handle_button_click(n_clicks, store_data):
    # Check if button was actually clicked
    if not n_clicks:
        raise PreventUpdate

    # Check if data exists
    if 'my_data' not in store_data:
        return dbc.Alert("Upload data first!", color="warning")

    # Process data
    df = pd.DataFrame(store_data['my_data'])
    result = process(df)

    return html.Div([
        html.H5("Results"),
        html.P(f"Processed {len(df)} rows"),
        dcc.Graph(figure=create_plot(result))
    ])
```

---

## 💾 Update Global Storage

```python
@callback(
    Output('global-store', 'data', allow_duplicate=True),
    Input('save-button', 'n_clicks'),
    State('input-field', 'value'),
    State('global-store', 'data'),
    prevent_initial_call=True
)
def save_to_storage(n_clicks, value, store_data):
    if not n_clicks:
        raise PreventUpdate

    # Copy existing data
    store_update = store_data.copy()

    # Add/update key
    store_update['user_input'] = value
    store_update['timestamp'] = datetime.now().isoformat()

    return store_update
```

---

## 📊 Create Dynamic Graph

```python
@callback(
    Output('my-graph', 'figure'),
    Input('dropdown-selector', 'value'),
    State('global-store', 'data')
)
def update_graph(selected_column, store_data):
    # Get data from storage
    df = pd.DataFrame(store_data.get('my_data', []))

    if df.empty:
        return go.Figure()  # Empty plot

    # Create plot based on selection
    fig = px.line(
        df,
        x='x_column',
        y=selected_column,
        title=f"Plot of {selected_column}"
    )

    # Customize
    fig.update_layout(
        hovermode='x unified',
        height=500
    )

    return fig
```

---

## 📥 Download File

```python
@callback(
    Output('download-component', 'data'),
    Input('download-button', 'n_clicks'),
    State('global-store', 'data'),
    prevent_initial_call=True
)
def download_results(n_clicks, store_data):
    if not n_clicks or 'results' not in store_data:
        raise PreventUpdate

    df = pd.DataFrame(store_data['results'])

    return dcc.send_data_frame(
        df.to_csv,
        'results.csv',
        index=False
    )
```

---

## 🔄 Chained Callbacks

```python
# Callback 1: Upload → Store
@callback(
    Output('data-store', 'data'),
    Input('upload', 'contents')
)
def store_upload(contents):
    df = process_file(contents)
    return {'data': df.to_dict('records')}

# Callback 2: Store → Process (triggered by Callback 1)
@callback(
    Output('processed-store', 'data'),
    Input('data-store', 'data')  # ← Watches store from Callback 1
)
def process_data(store_data):
    df = pd.DataFrame(store_data['data'])
    result = analyze(df)
    return {'result': result}

# Callback 3: Display (triggered by Callback 2)
@callback(
    Output('display', 'children'),
    Input('processed-store', 'data')  # ← Watches store from Callback 2
)
def display_result(processed_data):
    return f"Result: {processed_data['result']}"
```

---

## 🎛️ Multiple Inputs

```python
@callback(
    Output('output', 'children'),
    [
        Input('input1', 'value'),
        Input('input2', 'value'),
        Input('checkbox', 'value')
    ]
)
def update_with_multiple_inputs(val1, val2, checkbox_values):
    # Runs when ANY input changes

    # Check which checkboxes are selected
    is_checked = 'option1' in (checkbox_values or [])

    # Combine inputs
    result = val1 + val2 if is_checked else val1 - val2

    return f"Result: {result}"
```

---

## 📋 Update Data Table

```python
@callback(
    [
        Output('data-table', 'data'),
        Output('data-table', 'columns')
    ],
    Input('load-button', 'n_clicks'),
    State('global-store', 'data')
)
def populate_table(n_clicks, store_data):
    if not n_clicks:
        raise PreventUpdate

    df = pd.DataFrame(store_data.get('my_data', []))

    # Table data: list of dicts
    data = df.to_dict('records')

    # Table columns: list of column definitions
    columns = [{"name": col, "id": col} for col in df.columns]

    return data, columns
```

---

## 🔀 Conditional Logic

```python
@callback(
    Output('result', 'children'),
    Input('mode-selector', 'value'),
    State('global-store', 'data')
)
def conditional_processing(mode, store_data):
    df = pd.DataFrame(store_data.get('data', []))

    if mode == 'plot':
        fig = px.scatter(df, x='x', y='y')
        return dcc.Graph(figure=fig)

    elif mode == 'stats':
        stats = df.describe()
        return html.Pre(stats.to_string())

    elif mode == 'download':
        # Trigger download differently
        return "Click download button"

    else:
        return "Select a mode"
```

---

## ⚠️ Error Handling

```python
@callback(
    Output('output', 'children'),
    Input('button', 'n_clicks'),
    State('global-store', 'data'),
    prevent_initial_call=True
)
def safe_callback(n_clicks, store_data):
    try:
        # Validate inputs
        if not n_clicks:
            raise PreventUpdate

        if 'data' not in store_data:
            return dbc.Alert("No data available", color="warning")

        # Process
        result = risky_operation(store_data['data'])

        # Validate output
        if result is None:
            return dbc.Alert("Processing failed", color="danger")

        return dbc.Alert("Success!", color="success")

    except ValueError as e:
        return dbc.Alert(f"Invalid data: {e}", color="danger")

    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return dbc.Alert(f"Error: {e}", color="danger")
```

---

## 🎨 Dynamic Component Creation

```python
@callback(
    Output('container', 'children'),
    Input('num-items', 'value')
)
def create_components(num_items):
    # Create list of components
    components = []

    for i in range(num_items):
        components.append(
            dbc.Card([
                dbc.CardHeader(f"Item {i+1}"),
                dbc.CardBody([
                    html.P(f"Content for item {i+1}"),
                    dbc.Button(f"Click {i+1}", id=f"btn-{i}")
                ])
            ], className="mb-2")
        )

    return components
```

---

## 🕒 Interval / Auto-Refresh

```python
@callback(
    Output('live-data', 'children'),
    Input('refresh-interval', 'n_intervals')  # Auto-triggers every interval
)
def update_live_data(n_intervals):
    # Fetch fresh data
    current_data = fetch_latest_data()

    return html.Div([
        html.H5(f"Last update: {datetime.now()}"),
        html.P(f"Current value: {current_data}"),
        html.Small(f"Update #{n_intervals}")
    ])
```

**Define interval in layout:**
```python
dcc.Interval(
    id='refresh-interval',
    interval=5*1000,  # 5 seconds in milliseconds
    n_intervals=0
)
```

---

## 🎭 Show/Hide Components

```python
@callback(
    Output('collapsible-content', 'is_open'),
    Input('toggle-button', 'n_clicks'),
    State('collapsible-content', 'is_open')
)
def toggle_collapse(n_clicks, is_open):
    if not n_clicks:
        raise PreventUpdate
    return not is_open  # Flip the state
```

**Layout:**
```python
dbc.Button("Toggle", id='toggle-button'),
dbc.Collapse(
    html.Div("Hidden content"),
    id='collapsible-content',
    is_open=False
)
```

---

## 🔍 Input Validation

```python
@callback(
    [
        Output('input-field', 'invalid'),
        Output('validation-message', 'children')
    ],
    Input('input-field', 'value')
)
def validate_input(value):
    if value is None or value == '':
        return False, ""

    try:
        num = float(value)

        if num < 0:
            return True, "Must be positive"
        elif num > 100:
            return True, "Must be ≤ 100"
        else:
            return False, "✓ Valid"

    except ValueError:
        return True, "Must be a number"
```

---

## 🎯 Pattern Matching Callbacks

For dynamically created components:

```python
from dash import ALL, MATCH

@callback(
    Output({'type': 'output', 'index': MATCH}, 'children'),
    Input({'type': 'button', 'index': MATCH}, 'n_clicks')
)
def dynamic_callback(n_clicks):
    # Works for any button with this pattern
    # Each button updates its corresponding output
    return f"Clicked {n_clicks} times"
```

**Layout:**
```python
# Create multiple instances
for i in range(5):
    components.append(
        html.Div([
            dbc.Button(
                f"Button {i}",
                id={'type': 'button', 'index': i}
            ),
            html.Div(id={'type': 'output', 'index': i})
        ])
    )
```

---

## 📝 Common Gotchas

### ❌ Wrong: Mismatched Return Count
```python
@callback(
    [Output('out1', 'children'), Output('out2', 'children')],
    Input('btn', 'n_clicks')
)
def bad():
    return "Only one value"  # ✗ ERROR! Need 2 values
```

### ✅ Correct:
```python
@callback(
    [Output('out1', 'children'), Output('out2', 'children')],
    Input('btn', 'n_clicks')
)
def good():
    return "Value 1", "Value 2"  # ✓ Two values
```

### ❌ Wrong: Modifying State Directly
```python
@callback(
    Output('global-store', 'data'),
    ...
    State('global-store', 'data')
)
def bad(store_data):
    store_data['new_key'] = value  # ✗ Modifies original!
    return store_data
```

### ✅ Correct:
```python
@callback(
    Output('global-store', 'data'),
    ...
    State('global-store', 'data')
)
def good(store_data):
    store_update = store_data.copy()  # ✓ Copy first
    store_update['new_key'] = value
    return store_update
```

### ❌ Wrong: No Error Handling
```python
@callback(...)
def bad(store_data):
    df = pd.DataFrame(store_data['data'])  # ✗ Crashes if missing!
    return process(df)
```

### ✅ Correct:
```python
@callback(...)
def good(store_data):
    if 'data' not in store_data:  # ✓ Check first
        return dbc.Alert("No data", color="warning")

    df = pd.DataFrame(store_data['data'])
    return process(df)
```

---

## 🎓 Quick Reference

| Task | Input | State | Output |
|------|-------|-------|--------|
| Upload file | `('upload', 'contents')` | `('upload', 'filename')` | `('table', 'data')` |
| Click button | `('btn', 'n_clicks')` | - | `('div', 'children')` |
| Select dropdown | `('dropdown', 'value')` | - | `('graph', 'figure')` |
| Type in input | `('input', 'value')` | - | `('output', 'children')` |
| Auto-refresh | `('interval', 'n_intervals')` | - | `('div', 'children')` |
| Read storage | - | `('store', 'data')` | - |
| Write storage | Input varies | `('store', 'data')` | `('store', 'data')` |

---

**Generated:** 2025-12-01
**For:** SNUGeoSHM Dashboard Development

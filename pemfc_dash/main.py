import pathlib
import re
import os
import dash
from dash.dependencies import Input, Output, State, ALL  # ClientsideFunction
from dash import dcc
from dash import html
from dash import dash_table as dt

import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go
import numpy as np
from pemfc.src import interpolation as ip
from flask_caching import Cache

from pemfc_gui import data_transfer
from pemfc.data import input_dicts
from pemfc import main_app

from . import dash_functions as df, dash_layout as dl, \
    dash_modal as dm, dash_collapse as dc

from .dash_app import app
from .dash_tabs import tab3
from .dash_tabs import tab1, tab2, tab4, tab6, tab5

import pemfc_gui.input as gui_input

import json

import collections
tabs_list = [tab1.tab_layout, tab2.tab_layout, tab3.tab_layout,
             tab4.tab_layout, tab5.tab_layout, tab6.tab_layout]

# get relative data folder
PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("data").resolve()
# app = dash.Dash(__name__)

server = app.server

# Setup caching
CACHE_CONFIG = {
    "DEBUG": True,          # some Flask specific configs
    "CACHE_TYPE": "simple",  # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 300
}
cache = Cache()
cache.init_app(app.server, config=CACHE_CONFIG)

app._favicon = 'logo-zbt.ico'
app.title = 'PEMFC Model'

app.layout = dbc.Container(
    [html.Div(  # HEADER
        [html.Div(
            html.Div(
                html.Img(
                    src=app.get_asset_url("logo-zbt.png"),
                    id="zbt-image",
                    style={"object-fit": 'contain',
                           'position': 'center',
                           "width": "auto",
                           "margin": "auto"}),
                id="logo-container", className="pretty_container h-100",
                style={'display': 'flex', 'justify-content': 'center',
                       'align-items': 'center'}
            ),# , 'overflow': 'hidden'}),
            # width=4, align='center', style={'display': 'block'}
            className='col-12 col-lg-4 mb-2'
        ),
         html.Div(
             html.Div(
                 html.H3("Fuel Cell Stack Model",
                         style={"margin": "auto",
                                "min-height": "47px",
                                "font-weight": "bold",
                                "-webkit-text-shadow-width": "1px",
                                "-webkit-text-shadow-color": "#aabad6",
                                "color": "#0062af",
                                "font-size": "40px",
                                "width": "auto",
                                "text-align": "center",
                                "vertical-align": "middle"}),
                 className="pretty_container h-100", id="title",
                 style={'justify-content': 'center', 'align-items': 'center',
                        'display': 'flex'}),
             # width=8, align='center',
             style={'justify-content': 'space-evenly'},
             className='col-12 col-lg-8 mb-2'),
                           # 'overflow': 'auto', 'display': 'block'}),
             # style={'border': '1px solid grey', 'overflow': 'auto', 'display': 'block'}},
             # className="eight columns",)
        ],
        id="header",
        className='row'
        # align='start',
        # style={'justify-content': 'center'}
    ),

     # dcc.Loading(dcc.Store(id="ret_data"), fullscreen=True,
     #             style={"backgroundColor": "transparent"}, type='circle',
     #             color="#0a60c2"),
     dbc.Spinner(dcc.Store(id="ret_data"), fullscreen=True,
                 spinner_class_name='loading_spinner',
                 fullscreen_class_name='loading_spinner_bg'),
        # color="#0a60c2"),
     # empty Div to trigger javascript file for graph resizing
     html.Div(id="output-clientside"),
     # modal for any warning
     dm.modal_axes,

     html.Div(  # MIDDLE
         [html.Div(  # LEFT MIDDLE
             [
              html.Div(  # LEFT MIDDLE MIDDLE
                  [dl.tab_container(
                          tabs_list, label=
                          [k['title'] for k in gui_input.main_frame_dicts],
                          ids=[f'tab{num + 1}' for num in
                               range(len(gui_input.main_frame_dicts))])],
              id='setting_container', # style={'flex': '1'}
              ),
              html.Div(   # LEFT MIDDLE BOTTOM
                  [html.Div(
                       [html.Div(
                           [html.Button('Load Settings', id='load-button',
                                        className='settings_button',
                                        style={'display': 'flex'}),
                            html.Button('Save Settings', id='save-button',
                                        className='settings_button',
                                        style={'display': 'flex'}),
                            html.Button('Run Simulation', id='run_button',
                                        className='settings_button',
                                        style={'display': 'flex'})
                            ],
                            style={
                                   'display': 'flex',
                                   'flex-wrap': 'wrap',
                                   # 'flex-direction': 'column',
                                   # 'margin': '5px',
                                   'justify-content': 'center'}
                       ),
                        dcc.Download(id="savefile-json"),
                        dc.collapses],
                       className='neat-spacing')], style={'flex': '1'},
                  id='load_save_setting', className='pretty_container')],
             id="left-column", className='col-12 col-lg-4 mb-2'),

          html.Div(  # RIGHT MIDDLE
              [
                  # html.Div(
                   html.Div(
                        [html.Div('Global Results', className='title'),
                            dt.DataTable(id='global_data_table',
                                     editable=True,
                                     column_selectable='multi')],
                   #               id='sub_div_global_table',
                   #               className='pretty_container'),
                   #      columns=[{'filter_options': 'sensitive'}]
                        id='div_global_table',
                        className='pretty_container', style={'overflow': 'auto'}),
                   # id='div_global_table',  # style={'overflow': 'auto'},
                   # className='pretty_container'),

               html.Div(
                   [
                       html.Div(
                           [html.Div(
                               dcc.Dropdown(
                                   id='results_dropdown',
                                   placeholder='Choose Heatmap',
                                   className='dropdown_input'),
                               id='div_results_dropdown',
                               style={'padding': '1px', 'min-width': '200px'}),
                            html.Div(
                               dcc.Dropdown(id='results_dropdown_2',
                                            className='dropdown_input',
                                            style={'visibility': 'hidden'}),
                               id='div_results_dropdown_2',
                               style={'padding': '1px', 'min-width': '200px'})
                           ],
                            # dcc.Dropdown(id='results_dropdown_2',
                            #              style={'visibility': 'hidden'},
                            #              className='dropdown_input')],
                           style={'display': 'flex',
                                  'flex-direction': 'row',
                                  'flex-wrap': 'wrap',
                                  'justify-content': 'left'},
                       ),
                  # RIGHT MIDDLE BOTTOM
                       dcc.Graph(id="heatmap_graph")
                   ],
                   id='heatmap_container',
                   className='graph pretty_container'),

               html.Div(
                 [
                     html.Div(
                         [html.Div(
                             dcc.Dropdown(
                                 id='dropdown_line',
                                 placeholder='Choose Plots',
                                 className='dropdown_input'),
                             id='div_dropdown_line',
                             style={'padding': '1px', 'min-width': '200px'}),
                             html.Div(
                             dcc.Dropdown(id='dropdown_line2',
                                          className='dropdown_input',
                                          style={'visibility': 'hidden'}),
                             id='div_dropdown_line_2',
                             style={'padding': '1px', 'min-width': '200px'})],
                         # dcc.Dropdown(id='results_dropdown_2',
                         #              style={'visibility': 'hidden'},
                         #              className='dropdown_input')],
                         style={'display': 'flex', 'flex-direction': 'row',
                                'flex-wrap': 'wrap',
                                'justify-content': 'left',
                                'margin-bottom': '10px'},
                     ),
                  html.Div(
                      [
                      html.Div(
                          [
                           html.Div(
                               dcc.Checklist(id='disp_data',
                                             style={'overflow': 'auto'}),
                               className='display_checklist'),
                           dcc.Store(id='disp_chosen'),
                           dcc.Store(id='disp_clicked'),
                           dcc.Store(id='append_check'),
                           html.Div(
                               [html.Button('Clear List', id='clear_button',
                                            className='local_data_buttons'),
                                html.Button('Export Data to Table',
                                            id='export_b',
                                            className='local_data_buttons'),
                                html.Button('Append New Data to Table',
                                            id='append_b',
                                            className='local_data_buttons'),
                                html.Button('Clear Table', id='clear_table_b',
                                            className='local_data_buttons')],
                               style={
                                   'display': 'flex',
                                   'flex-direction': 'column',
                                   'margin-bottom': '5px'}
                           )],
                          style={'width': '200px'}
                      ),
                      dcc.Store(id='cells_data'),
                      html.Div(dcc.Graph(id='line_graph',
                                         style={'flex': 'auto'}),
                               style={'display': 'flex', 'flex-direction': 'row',
                                      'width': 'calc(100% - 200px)'})
                    ],
                    style={'display': 'flex', 'flex-direction': 'row',
                           'justify-content': 'space-evenly'}),
                 ],
                 className="pretty_container",
                 style={'display': 'flex', 'flex': '1', 'flex-direction':
                        'column', 'justify-content': 'space-evenly'}
              ),],
              id='right-column', className='col-12 col-lg-8 mb-2')],

         className="row",
         style={'justify-content': 'space-evenly'}, ),
     # html.Div(
     #     [],
     #     style={'position': 'relative',
     #            'margin': '0 0.05% 0 0.7%'})
     html.Div(dt.DataTable(id='table', editable=True,
                           column_selectable='multi'),
             # columns=[{'filter_options': 'sensitive'}]),
              id='div_table', style={'overflow': 'auto',
                                     'position': 'relative',
                                     'margin': '0 0.05% 0 0.7%'},
              className='pretty_container')
    ],
    id="mainContainer",
    # className='twelve columns',
    fluid=True,
    style={'padding': '0px'})


@cache.memoize()
def simulation_store(**kwargs):
    data_transfer.gui_to_sim_transfer(kwargs, input_dicts.sim_dict)
    global_data, local_data, sim = main_app.main()
    return [global_data[0], local_data[0]]


def try_simulation_store(**kwargs):
    try:
        results = simulation_store(**kwargs)
    except Exception as E:
        raise PreventUpdate
    return results


@app.callback(
    Output('ret_data', 'data'),
    Output('modal-title', 'children'),
    Output('modal-body', 'children'),
    Output('modal', 'is_open'),
    Input("run_button", "n_clicks"),
    State({'type': 'input', 'id': ALL, 'specifier': ALL}, 'value'),
    State({'type': 'multiinput', 'id': ALL, 'specifier': ALL}, 'value'),
    State({'type': 'input', 'id': ALL, 'specifier': ALL}, 'id'),
    State({'type': 'multiinput', 'id': ALL, 'specifier': ALL}, 'id'),
    State('modal', 'is_open'),
)
def compute_simulation(n_click, inputs, inputs2, ids, ids2, modal_state):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    if 'run_button' in changed_id and n_click is not None:
        dict_data = df.process_inputs(inputs, inputs2, ids, ids2)

        datas = {}
        for k, v in dict_data.items():
            datas[k] = {'sim_name': k.split('-'), 'value': v}
        try:
            simulation_store(**datas)
        except Exception as E:
            modal_title, modal_body = \
                dm.modal_process('input-error', error=repr(E))
            return datas, modal_title, modal_body, not modal_state
    else:
        raise PreventUpdate
    return datas, None, None, modal_state


@app.callback(
    Output({'type': 'input', 'id': ALL, 'specifier': ALL}, 'value'),
    Output({'type': 'multiinput', 'id': ALL, 'specifier': ALL}, 'value'),
    Output('upload-file', 'contents'),
    Output('modal-title', 'children'),
    Output('modal-body', 'children'),
    Output('modal', 'is_open'),
    Input('upload-file', 'contents'),
    State('upload-file', 'filename'),
    State({'type': 'input', 'id': ALL, 'specifier': ALL}, 'value'),
    State({'type': 'multiinput', 'id': ALL, 'specifier': ALL}, 'value'),
    State({'type': 'input', 'id': ALL, 'specifier': ALL}, 'id'),
    State({'type': 'multiinput', 'id': ALL, 'specifier': ALL}, 'id'),
    State('modal', 'is_open'),
)
def upload_settings(contents, filename, value, multival, ids, ids2,
                    modal_state):
    if contents is None:
        raise PreventUpdate
    else:
        if 'json' in filename:
            try:
                j_file, err_l = df.parse_contents(contents)

                dict_ids = {id_l: val for id_l, val in
                            zip([id_l['id'] for id_l in ids], value)}
                dict_ids2 = {id_l: val for id_l, val in
                             zip([id_l['id'] for id_l in ids2], multival)}

                id_match = set.union(set(dict_ids),
                                     set([item[:-2] for item in dict_ids2]))

                for k, v in j_file.items():
                    if k in id_match:
                        if isinstance(v, list):
                            for num, val in enumerate(v):
                                dict_ids2[k+f'_{num}'] = df.check_ifbool(val)
                        else:
                            dict_ids[k] = df.check_ifbool(v)
                    else:
                        continue

                if not err_l:
                    # All JSON settings match Dash IDs
                    modal_title, modal_body = dm.modal_process('loaded')
                    return list(dict_ids.values()), list(dict_ids2.values()), \
                        None, modal_title, modal_body, not modal_state
                else:
                    # Some JSON settings do not match Dash IDs; return values
                    # that matched with Dash IDs
                    modal_title, modal_body = \
                        dm.modal_process('id-not-loaded', err_l)
                    return list(dict_ids.values()), list(dict_ids2.values()), \
                        None, modal_title, modal_body, not modal_state
            except Exception as e:
                # Error / JSON file cannot be processed; return old value
                modal_title, modal_body = dm.modal_process('error')
                return value, multival, None, modal_title, modal_body, \
                    not modal_state
        else:
            # Not JSON file; return old value
            modal_title, modal_body = dm.modal_process('wrong-file')
            return value, multival, None, modal_title, modal_body, \
                not modal_state


@app.callback(
    Output("savefile-json", "data"),
    Output('save-as-button', "n_clicks"),
    Input('save-as-button', "n_clicks"),
    State('save_as_input', 'value'),
    State({'type': 'input', 'id': ALL, 'specifier': ALL}, 'value'),
    State({'type': 'multiinput', 'id': ALL, 'specifier': ALL}, 'value'),
    State({'type': 'input', 'id': ALL, 'specifier': ALL}, 'id'),
    State({'type': 'multiinput', 'id': ALL, 'specifier':  ALL}, 'id'),
    prevent_initial_call=True,
)
def save_settings(n_clicks, name, val1, val2, ids, ids2):
    if n_clicks is not None:
        dict_data = df.process_inputs(val1, val2, ids, ids2)  # values first
        sep_id_list = [joined_id.split('-') for joined_id in
                       dict_data.keys()]

        val_list = dict_data.values()
        new_dict = {}
        for sep_id, vals in zip(sep_id_list, val_list):
            current_level = new_dict
            for id_l in sep_id:
                if id_l not in current_level:
                    if id_l != sep_id[-1]:
                        current_level[id_l] = {}
                    else:
                        current_level[id_l] = vals
                current_level = current_level[id_l]
        if name:
            setting_name = name if '.json' in name else name + '.json'
        else:
            setting_name = 'settings.json'

        return dict(content=json.dumps(new_dict, sort_keys=True, indent=2),
                    filename=setting_name), None


@app.callback(
    [Output({'type': 'global_children', 'id': ALL}, 'children'),
     Output({'type': 'global_value', 'id': ALL}, 'children'),
     Output({'type': 'global_unit', 'id': ALL}, 'children'),
     # Output({'type': 'global_container', 'id': ALL}, 'style'),
     Output('global-data', 'style')],
    Input('ret_data', 'data')
)
def global_outputs(data):
    results = try_simulation_store(**data)
    g = results[0]
    glob = list(results[0])
    glob_len = len(glob)

    desc = [gl for gl in glob]
    unit = [g[gl]['units'] for gl in glob]
    val = \
        ['{:g}'.format(float('{:.5g}'.format(g[gl]['value'])))
         for gl in glob]
    disp = {'display': 'flex'}
    # disps = [{k: v} for k, v in disp.items() for _ in range(glob_len)]
    return desc, val, unit, disp


@app.callback(
    [Output('global_data_table', 'columns'),
     Output('global_data_table', 'data'),
     Output('global_data_table', 'export_format')],
    Input('ret_data', 'data')
)
def global_outputs_table(data):
    results = simulation_store(**data)
    global_result_dict = results[0]
    names = list(global_result_dict.keys())
    values = [v['value'] for k, v in global_result_dict.items()]
    units = [v['units'] for k, v in global_result_dict.items()]

    column_names = ['Quantity', 'Value', 'Units']
    columns = [{'deletable': True, 'renamable': True,
                'selectable': True, 'name': col, 'id': col}
               for col in column_names]
    datas = [{column_names[0]: names[i],
              column_names[1]: values[i],
              column_names[2]: units[i]} for i in range(len(values))]

    return columns, datas, 'csv',


@app.callback(
    [Output('results_dropdown', 'options'),
     Output('results_dropdown', 'value'),
     Output('dropdown_line', 'options')],
    Input('ret_data', 'data')
)
def get_dropdown_options(data):
    results = try_simulation_store(**data)
    local_data = results[1]
    values = [{'label': key, 'value': key} for key in local_data if key not in
              ["Channel Location", "Cells", "Cathode",
               "Coolant Channels", "Normalized Flow Distribution"]]
    return values, 'Current Density', values


@app.callback(
    [Output('results_dropdown_2', 'options'),
     Output('results_dropdown_2', 'value'),
     Output('results_dropdown_2', 'style')],
    [Input('results_dropdown', 'value'),
     Input('ret_data', 'data')]
)
def get_dropdown_options_2(dropdown_key, data):
    if dropdown_key is None:
        raise PreventUpdate
    else:
        results = try_simulation_store(**data)
        local_data = results[1]
        if 'value' in local_data[dropdown_key]:
            return [], None, {'visibility': 'hidden'}
        else:
            options = [{'label': key, 'value': key} for key in
                       local_data[dropdown_key]]
            value = options[0]['value']
            return options, value, {'visibility': 'visible'}


@app.callback(
    [Output('dropdown_line2', 'options'),
     Output('dropdown_line2', 'value'),
     Output('dropdown_line2', 'style')],
    [Input('dropdown_line', 'value'),
     Input('ret_data', 'data')]
)
def dropdown_line2(dropdown_key, data):
    if dropdown_key is None:
        raise PreventUpdate
    else:
        results = try_simulation_store(**data)
        local_data = results[1]
        if 'value' in local_data[dropdown_key]:
            return [], None, {'visibility': 'hidden'}
        else:
            options = [{'label': key, 'value': key} for key in
                       local_data[dropdown_key]]
            value = options[0]['value']
            return options, value, {'visibility': 'visible'}


@app.callback(
    [Output('line_graph', 'figure'),
     Output('cells_data', 'data'),
     Output('disp_data', 'options'),
     Output('disp_data', 'value'),
     Output('disp_chosen', 'data')],
    [Input('dropdown_line', 'value'),
     Input('dropdown_line2', 'value'),
     Input('disp_data', 'value'),
     Input('clear_button', 'n_clicks'),
     Input('line_graph', 'restyleData')],
    [State('ret_data', 'data'),
     State('cells_data', 'data'),
     State('disp_data', 'value'),
     State('disp_chosen', 'data')]
)
def update_line_graph(drop1, drop2, checklist, n_click, rdata,
                      data, state2, state3, state4):
    ctx = dash.callback_context.triggered[0]['prop_id']
    if drop1 is None:
        raise PreventUpdate
    else:

        results = try_simulation_store(**data)
        local_data = results[1]

        x_key = 'Channel Location'
        xvalues = ip.interpolate_1d(local_data[x_key]['value'])

        if drop1 is None:
            yvalues = np.zeros(len(xvalues))
        else:
            if 'value' in local_data[drop1]:
                yvalues = local_data[drop1]['value']
            elif drop2 is not None:
                yvalues = local_data[drop1][drop2]['value']
            else:
                yvalues = np.zeros((len(local_data['Cell Voltage']['value']),
                                    len(xvalues)))

        fig = go.Figure()
        cells = {}
        for num, yval in enumerate(yvalues):
            fig.add_trace(go.Scatter(x=xvalues, y=yval,
                                     mode='lines+markers',
                                     name=f'Cell {num+1}'))
            cells.update({num+1: {'name': f'Cell {num+1}', 'data': yval}})


        if drop2 is None:
            y_title = drop1 +  ' / ' + local_data[drop1]['units']
        else:
            y_title = drop1 + ' - ' + drop2 + ' / ' \
                       + local_data[drop1][drop2]['units']

        layout = go.Layout(
            font={'color': 'black', 'family': 'Arial'},
            # title='Local Results in Heat Map',
            titlefont={'size': 11, 'color': 'black'},
            xaxis={'tickfont': {'size': 11}, 'titlefont': {'size': 14},
                   'title': x_key + ' / ' + local_data[x_key]['units']},
            yaxis={'tickfont': {'size': 11}, 'titlefont': {'size': 14},
                   'title': y_title},
            margin={'l': 100, 'r': 20, 't': 20, 'b': 20})


        fig.update_layout(layout)

        options = [{'label': ' ' + cells[k]['name'], 'value': cells[k]['name']}
                   for k in cells]
        val = sorted([k for k in cells])
        value = [f'Cell {num}' for num in val]
        check = [] if state4 is None else state4

        if 'clear_button.n_clicks' in ctx:
            fig.data = []
            return fig, {}, [], [], []
        else:
            if state3 is None:
                return fig, cells, options, value, check
            else:
                if 'disp_data.value' in ctx:
                    fig.for_each_trace(
                        lambda trace: trace.update(
                            visible=True) if trace.name in state3
                        else trace.update(visible='legendonly'))
                    new_check = list(k['value'] for k in options)
                    [new_check.remove(cell) for cell in state3 if cell in
                     new_check]
                    return fig, cells, options, state3, new_check
                elif 'line_graph.restyleData' in ctx:
                    read = rdata[0]['visible']
                    read_num = rdata[1][0]

                    if len(read) == 1:
                        if isinstance(read[0], str):  # lose (legendonly)
                            if f'Cell {read_num+1}' not in check:
                                check.append(f'Cell {read_num+1}')
                        else:  # isinstance(read, bool): #add (True)
                            try:
                                if 'Cell {}'.format(read_num + 1) in check:
                                    check.remove('Cell {}'.format(read_num + 1))
                            except ValueError:
                                pass
                        [value.remove(val) for val in check if val in value]
                        fig.for_each_trace(
                            lambda trace: trace.update(
                                visible=True) if trace.name in value
                            else trace.update(visible='legendonly'))

                        return fig, cells, options, value, check
                    else:
                        check_new = [f'Cell {x[0]+1}' for x in enumerate(read)
                                     if x[1] == 'legendonly']
                        [value.remove(che) for che in check_new
                         if che in value]
                        fig.for_each_trace(
                            lambda trace: trace.update(
                                visible=True) if trace.name in value
                            else trace.update(visible='legendonly'))

                        return fig, cells, options, value, check_new
                else:
                    return fig, cells, options, value, check


@app.callback(
    [Output('table', 'columns'),
     Output('table', 'data'),
     Output('table', 'export_format'),
     Output('append_check', 'data')],
    [Input('disp_data', 'value'),  # from display
     Input('cells_data', 'data'),  # from line graph
     Input('disp_chosen', 'data'),  # from line graph (but only the val of cell)
     Input('export_b', 'n_clicks'),  # button1
     Input('append_b', 'n_clicks'),  # button2
     Input('clear_table_b', 'n_clicks')],
    [State('ret_data', 'data'),
     State('table', 'columns'),
     State('table', 'data'),
     State('append_check', 'data')]
)
def list_to_table(val, data, data2, n1, n2, n3, state, state2, state3, state4):
    ctx = dash.callback_context.triggered[0]['prop_id']
    if val is None:
        raise PreventUpdate
    else:
        results = try_simulation_store(**data)
        local_data = results[1]
        digit_list = \
            sorted([int(re.sub('[^0-9\.]', '', inside)) for inside in val])

        index = [{'id': 'Channel Location', 'name': 'Channel Location',
                  'deletable': True}]
        columns = [{'deletable': True, 'renamable': True,
                    'selectable': True, 'name': 'Cell {}'.format(d),
                    'id': 'Cell {}'.format(d)} for d in digit_list]
        # list with nested dict

        x_key = 'Channel Location'
        xvalues = ip.interpolate_1d(local_data[x_key]['value'])
        datas = [{**{'Channel Location': cell},
                  **{data[k]['name']: data[k]['data'][num] for k in data}}
                 for num, cell in enumerate(xvalues)]  # list with nested dict

        if state4 is None:
            appended = 0
        else:
            appended = state4

        if 'export_b.n_clicks' in ctx:
            return index+columns, datas, 'csv', appended
        elif 'clear_table_b.n_clicks' in ctx:
            return [], [], 'none', appended
        elif 'append_b.n_clicks' in ctx:
            if n1 is None or state3 == [] or state2 == [] or \
                    ctx == 'clear_table_b.n_clicks':
                raise PreventUpdate
            else:
                appended += 1
                app_columns = \
                    [{'deletable': True, 'renamable': True,
                      'selectable': True, 'name': 'Cell {}'.format(d),
                      'id': 'Cell {}'.format(d) + '-'+str(appended)}
                     for d in digit_list]
                new_columns = state2 + app_columns
                app_datas = \
                    [{**{'Channel Location': cell},
                      **{data[k]['name']+'-'+str(appended): data[k]['data'][num]
                         for k in data}}
                     for num, cell in enumerate(xvalues)]
                new_data_list = []
                new_datas = \
                    [{**state3[i], **app_datas[i]}
                     if state3[i][x_key] == app_datas[i][x_key]
                     else new_data_list.extend([state3[i], app_datas[i]])
                     for i in range(len(app_datas))]
                new_datas = list(filter(None.__ne__, new_datas))
                new_datas.extend(new_data_list)

                return new_columns, new_datas, 'csv', appended
        else:
            if n1 is None or state2 == []:
                return state2, state3, 'none', appended
            else:
                return state2, state3, 'csv', appended


@app.callback(
    Output("heatmap_graph", "figure"),
    [Input('results_dropdown', 'value'), Input('results_dropdown_2', 'value'),
     Input('ret_data', 'data')],
)
def update_graph(dropdown_key, dropdown_key_2, data):
    if dropdown_key is None:
        raise PreventUpdate
    else:
        results = try_simulation_store(**data)
        local_data = results[1]
        x_key = 'Channel Location'
        y_key = 'Cells'
        xvalues = ip.interpolate_1d(local_data[x_key]['value'])
        yvalues = local_data[y_key]['value']

        if dropdown_key is None:
            zvalues = np.zeros((len(xvalues), len(yvalues)))
        else:
            if 'value' in local_data[dropdown_key]:
                zvalues = local_data[dropdown_key]['value']
            elif dropdown_key_2 is not None:
                zvalues = local_data[dropdown_key][dropdown_key_2]['value']
            else:
                zvalues = np.zeros((len(xvalues), len(yvalues)))
            # else:
            #     zvalues = local_data[dropdown_key][dropdown_key_2]['value']

        if dropdown_key_2 is None:
            z_title = dropdown_key +  ' / ' + local_data[dropdown_key]['units']
        else:
            z_title = dropdown_key + ' - ' + dropdown_key_2 + ' / ' \
                       + local_data[dropdown_key][dropdown_key_2]['units']

        layout = go.Layout(
            font={'color': 'black', 'family': 'Arial'},
            # title='Local Results in Heat Map',
            titlefont={'size': 11, 'color': 'black'},
            xaxis={'tickfont': {'size': 11}, 'titlefont': {'size': 14},
                   'title': x_key + ' / ' + local_data[x_key]['units']},
            yaxis={'tickfont': {'size': 11}, 'titlefont': {'size': 14},
                   'title': y_key + ' / ' + local_data[y_key]['units']},
            margin={'l': 75, 'r': 20, 't': 20, 'b': 20})

        heatmap = go.Heatmap(z=zvalues, x=xvalues, y=yvalues, xgap=1, ygap=1,
                             colorbar={'tickfont': {'size': 11},
                                       'title': {'text': z_title,
                                                 'font': {'size': 14},
                                                 'side': 'right'}})

        fig = go.Figure(data=heatmap, layout=layout)

        fig.update_xaxes(showgrid=True, tickmode='array',
                         tickvals=local_data[x_key]['value'])
        fig.update_yaxes(showgrid=True, tickmode='array', tickvals=yvalues)
    return fig


# if __name__ == "__main__":
#     # [print(num, x) for num, x in enumerate(dl.ID_LIST) ]
#     app.run_server(debug=True, use_reloader=False)
#     # app.run_server(debug=True, use_reloader=False,
#     #                host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

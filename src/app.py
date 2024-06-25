import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import numpy as np
import plotly.graph_objs as go
import pandas as pd

import os
import logging

app = dash.Dash(__name__)
server = app.server

def shift_spectrum(wavelengths, intensities, redshift):
    shifted_wavelengths = wavelengths * (1 + redshift)
    return shifted_wavelengths, intensities

# MIRI IFU transmission
pce = pd.read_excel('./JWST_filter/IFU/MRS_photon_conversion_efficiency.xlsx', skiprows=0)

# # Read in Res table
# miri_R = pd.read_table('/Users/thomaslai/Documents/astro/CAFE/CAFE/CAFE/tables/resolving_power/R_JWST_MIRI.txt', comment=';', 
#                        names=['name','wmin','wmax','slope','bias'], delim_whitespace=True)

colors = ['rgba(94, 79, 162, 0.5)', 'rgba(171, 221, 164, 0.5)', 'rgba(255, 153, 153, 0.5)']

name = ['CH1S',
        'CH1M',
        'CH1L',
        'CH2S',
        'CH2M',
        'CH2L',
        'CH3S',
        'CH3M',
        'CH3L',
        'CH4S',
        'CH4M',
        'CH4L']

sub_ch_name = ['Short', 'Medium', 'Long']

# Create a list to hold all the transmission profile traces
transmission_traces = []

# Create a list to hold all the annotations
annotations = []

for i in range(0,12):
    c = i % 3 
    sub = pce[pce['Sub-band'] == i]
    
    # Determine if legend should be shown. Only show for the first instance of each color group.
    show_legend = True if i < 3 else False

    trace = go.Scatter(
        x=sub.Wavelength.values.astype('float'), 
        y=sub.PCE.values.astype('float'), 
        fill='tozeroy',
        fillcolor=colors[c],
        line=dict(color=colors[c]),
        name=sub_ch_name[c], #name.iloc[i][1:-1].split('MRS')[1],
        mode='lines', 
        legendgroup=f'group{c}',  # Group traces by color
        showlegend=show_legend  # Show legend only for the first trace of each group
        #name=f'Transmission Profile {i+1}',  # Update the name for each profile
        #line={'dash': 'dash'}
    )
    
    # Append the created trace to the list
    transmission_traces.append(trace)


# Read in MIRI imaging filters
band_list = ['F560W', 'F770W', 'F1000W', 'F1130W', 'F1280W', 'F1500W', 'F1800W', 'F2100W', 'F2550W']

img_dirc = './JWST_filter/image/'

for b in band_list:
    miri_df = pd.read_csv(img_dirc + 'JWST_MIRI.'+b+'.dat', names=['w','f'], delim_whitespace=True)

    trace = go.Scatter(
        x=miri_df.w.values.astype('float') / 10000, # convert Angstrom to um 
        y=miri_df.f.values.astype('float') * 2/5, # into a arbitrary factor 
        fill='tozeroy',
        #fillcolor=colors[c],
        #line=dict(color=colors[c]),
        name=b, #name.iloc[i][1:-1].split('MRS')[1],
        mode='lines', 
        #legendgroup=f'group{c}',  # Group traces by color
        showlegend=True
    )
    
    # Append the created trace to the list
    transmission_traces.append(trace)

    # Add the annotation
    annotations.append(
        {
            'x': 5, #miri_df.w.values.astype('float').max()/ 10000,
            'y': miri_df.f.values.astype('float').max() * 2/5,
            'xref': 'x',
            'yref': 'y',
            'text': b,
            'showarrow': False,
            'font': dict(size=10, color='black')
        }
    )


# Read in NIRCAM imaging filters
band_list = ['F150W', 'F200W', 'F300M', 'F335M', 'F360M', 'F444W']

for b in band_list:
    img_dirc = './JWST_filter/image/'
    nircam_df = pd.read_csv(img_dirc + 'JWST_NIRCam.'+b+'.dat', names=['w','f'], delim_whitespace=True)

    trace = go.Scatter(
        x=nircam_df.w.values.astype('float') / 10000, # convert Angstrom to um 
        y=nircam_df.f.values.astype('float') * 2/5, # into a arbitrary factor 
        fill='tozeroy',
        #fillcolor=colors[c],
        #line=dict(color=colors[c]),
        name=b, #name.iloc[i][1:-1].split('MRS')[1],
        mode='lines', 
        #legendgroup=f'group{c}',  # Group traces by color
        showlegend=True
    )
    
    # Append the created trace to the list
    transmission_traces.append(trace)


# Initial galaxy spectrum trace
# NGC7469
n7469 = pd.read_csv('./NGC7469_sum_sf_spec.csv')
z = 0.0163
shifted_wavelengths, shifted_intensities = shift_spectrum(n7469.w/(1+z), n7469.f, 0.0)
spectrum_trace_n7469 = go.Scatter(x=shifted_wavelengths, y=shifted_intensities, mode='lines', name='NGC7469', yaxis='y2')

# VV114
vv114 = pd.read_csv('./VV114_spec.csv')
shifted_wavelengths_vv114, shifted_intensities_vv114 = shift_spectrum(vv114.w, vv114.f, 0.0)
spectrum_trace_vv114 = go.Scatter(x=shifted_wavelengths_vv114, y=shifted_intensities_vv114, mode='lines', name='VV114', yaxis='y2')

# Adding both galaxy spectra to the existing list of transmission traces
transmission_traces = [spectrum_trace_n7469, spectrum_trace_vv114] + transmission_traces


# Read in the line list
# =====================
line_list_df = pd.read_csv('line_list_gt3um.csv')
unique_species = line_list_df['Species'].unique()
species_options = [{'label': species, 'value': species} for species in unique_species]

# Define the app layout using the list of traces
app.layout = html.Div([
    html.H1("JWST Imager & IFU Filter Viewer"),
    
    html.Div([
        html.Label("Enter Redshift:"),
        dcc.Input(id='redshift-input', value='0', type='number', step=0.01, min=0),
    ]),
    
    dcc.Graph(
        id='spectrum-plot',
        figure={
            'data': transmission_traces, 
            'layout': go.Layout(
                title='Transmission Profiles', 
                xaxis={'title': 'Wavelength', 'type': 'log'}, 
                yaxis={'title': 'Transmission'},
                yaxis2={
                    'title': 'Intensity',
                    'overlaying': 'y',
                    'side': 'right',
                    'type': 'log'
                },
                height=600
            )
        }
    ),
    
    html.Div([
        html.Label("Toggle Species (line list from the PDRs4All team):"),
        dcc.Checklist(
            id='species-checklist',
            options=species_options,
            value=[]
        ),
    ]),
])



def generate_species_lines(df, species, redshift, color='rgba(178, 34, 34, 0.5)'):
    species_df = df[df['Species'] == species]
    lines = []
    for wavelength in species_df['Wavelength']:
        shifted_wavelength = wavelength * (1 + float(redshift))  # Include redshift
        line = go.Scatter(
            x=[shifted_wavelength, shifted_wavelength],
            y=[0, 6],  # Set the range for the line
            mode='lines',
            line=dict(color=color),
            name=f'{species} line',
            yaxis='y2'
        )
        lines.append(line)
    return lines


# Update the callback to also take the existing figure as an Input
@app.callback(
    Output('spectrum-plot', 'figure'),
    [Input('redshift-input', 'value'),
    Input('species-checklist', 'value'),
    Input('spectrum-plot', 'figure')]
)
def update_spectrum_plot(redshift_value, selected_species, existing_figure):
    redshift_value = float(redshift_value)  # Convert the input value to float

    # Shift galaxy spectrum for NGC7469
    n7469 = pd.read_csv('./NGC7469_sum_sf_spec.csv')
    z = 0.0163  # initial redshift
    shifted_wavelengths, shifted_intensities = shift_spectrum(n7469.w / (1 + z), n7469.f, redshift_value)
    existing_figure['data'][0]['x'] = shifted_wavelengths
    existing_figure['data'][0]['y'] = shifted_intensities

    # Shift galaxy spectrum for VV114
    vv114 = pd.read_csv('./VV114_spec.csv')
    shifted_wavelengths_vv114, shifted_intensities_vv114 = shift_spectrum(vv114.w, vv114.f, redshift_value)
    existing_figure['data'][1]['x'] = shifted_wavelengths_vv114
    existing_figure['data'][1]['y'] = shifted_intensities_vv114

    # Remove existing species lines
    existing_figure['data'] = [trace for trace in existing_figure['data'] if 'line' not in trace.get('name', '')]

    # Generate and add the species lines, shifted by the redshift
    for species in selected_species:
        lines = generate_species_lines(line_list_df, species, redshift_value)  # Include redshift when generating lines
        existing_figure['data'].extend(lines)

    return existing_figure

# app.run_server(debug=True, use_reloader=True, port=8052)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8050))
    app.run_server(host='0.0.0.0', port=port)

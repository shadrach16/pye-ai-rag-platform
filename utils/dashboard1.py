import dash
from dash import dcc
from dash import html
import plotly.graph_objs as go
import pandas as pd
import numpy as np

# Create sample data for ETL jobs
etl_data = {'job_id': range(1, 21),
            'transformer_name': ['T1', 'T2', 'T3', 'T2', 'T1', 'T3', 'T1', 'T1', 'T2', 'T3',
                                 'T1', 'T2', 'T3', 'T1', 'T1', 'T3', 'T2', 'T2', 'T3', 'T1'],
            'source_connector': ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J',
                                 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T'],
            'target_connector': ['X', 'Y', 'Z', 'X', 'Y', 'Z', 'X', 'Y', 'Z', 'X',
                                 'Y', 'Z', 'X', 'Y', 'Z', 'X', 'Y', 'Z', 'X', 'Y'],
            'status': ['success', 'success', 'success', 'failed', 'success',
                       'success', 'success', 'success', 'failed', 'success',
                       'success', 'success', 'success', 'success', 'success',
                       'failed', 'success', 'success', 'failed', 'success']
           }

etl_db = pd.DataFrame(etl_data)

# Define the data to display
successful_jobs = etl_db[etl_db['status'] == 'success']
failed_jobs = etl_db[etl_db['status'] == 'failed']
job_counts = etl_db.groupby('transformer_name')['job_id'].nunique()

# Create a new DataFrame to store the connections between source and target connectors
connections = pd.DataFrame(columns=['source_connector', 'target_connector'])

# Loop through each transformer and extract the source and target connectors
for transformer_name in etl_db['transformer_name'].unique():
    transformer_jobs = etl_db[etl_db['transformer_name'] == transformer_name]
    source_connector = transformer_jobs['source_connector'].iloc[0]
    target_connector = transformer_jobs['target_connector'].iloc[-1]
    connections = connections.append({'source_connector': source_connector, 'target_connector': target_connector},
                                     ignore_index=True)

# Create the dashboard components
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1('ETL Dashboard'),
    dcc.Graph(
        id='job-count-graph',
        figure={
            'data': [
                go.Bar(
                    x=job_counts.index,
                    y=job_counts.values,
                    name='Job Count'
                )
            ],
            'layout': go.Layout(
                title='Job Count by Transformer Name',
                xaxis={'title': 'Transformer Name'},
                yaxis={'title': 'Job Count'}
            )
        }
    ),
    dcc.Graph(
        id='job-status-graph',
        figure={
            'data': [
                go.Pie(
                    labels=['Successful Jobs', 'Failed Jobs'],
                    values=[len(successful_jobs), len(failed_jobs)]
                )
            ],
            'layout': go.Layout(
                title='Job Status',
                height=400
            )
        }
    ),
    dcc.Graph(
        id='connector-graph',
        figure={
            'data': [
                go.Sankey(
                    arrangement='snap',
                    node=dict(
                        pad=15,
                        thickness=20,
                        line=dict(color='black', width=0.5),
                        label=connections['source_connector'].unique().tolist() + connections['target_connector'].unique().tolist(),
                        color=['lightblue']*len(connections['source_connector'].unique().tolist()) + ['lightgreen']*len(connections['target_connector'].unique().tolist())
                    ),
                    link=dict(
                        source=[connections['source_connector'].unique().tolist().index(source) for source in connections['source_connector']],
                        target=[len(connections['source_connector'].unique().tolist()) + connections['target_connector'].unique().tolist().index(target) for target in connections['target_connector']],
                        value=[1]*len(connections)
                    )
                )
            ],
            'layout': go.Layout(
                title='Connector Connections',
                height=600
            )
        }
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)

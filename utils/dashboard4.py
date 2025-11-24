
import dash
from dash import dcc
from dash import html
import plotly.graph_objs as go
import pandas as pd

# Sample data for the etl_jobs table
etl_jobs = pd.DataFrame({
    'job_id': [1, 2, 3, 4, 5, 6],
    'transformer_name': ['DB Connector', 'File Connector', 'DB Connector', 'File Connector', 'DB Connector', 'File Connector'],
    'source': ['db1.table1', 'file1.csv', 'db2.table2', 'file2.csv', 'db3.table3', 'file3.csv'],
    'destination': ['db4.table4', 'file4.csv', 'db5.table5', 'file5.csv', 'db6.table6', 'file6.csv'],
    'status': ['success', 'success', 'success', 'failed', 'failed', 'failed']
})

# Define the data to display
successful_jobs = etl_jobs[etl_jobs['status'] == 'success']
failed_jobs = etl_jobs[etl_jobs['status'] == 'failed']
job_counts = etl_jobs.groupby('transformer_name')['job_id'].nunique()

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
        id='job-connections-graph',
        figure={
            'data': [
                go.Scatter(
                    x=etl_jobs[etl_jobs['transformer_name'] == 'DB Connector']['source'],
                    y=etl_jobs[etl_jobs['transformer_name'] == 'DB Connector']['destination'],
                    mode='lines',
                    name='DB Connector',
                    line=dict(color='blue', width=2)
                ),
                go.Scatter(
                    x=etl_jobs[etl_jobs['transformer_name'] == 'File Connector']['source'],
                    y=etl_jobs[etl_jobs['transformer_name'] == 'File Connector']['destination'],
                    mode='lines',
                    name='File Connector',
                    line=dict(color='green', width=2)
                )
            ],
            'layout': go.Layout(
                title='ETL Job Connections',
                xaxis=dict(title='Source'),
                yaxis=dict(title='Destination'),
                height=500,
                showlegend=True,
                legend=dict(x=0.8, y=0.1)
            )
        }
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)

import dash
from dash import dcc
from dash import html
import plotly.graph_objs as go
import pandas as pd

# Connect to the ETL database
etl_jobs_data = {
    'job_id': [1, 2, 3, 4, 5, 6],
    'transformer_name': ['Transformer A', 'Transformer B', 'Transformer B', 'Transformer C', 'Transformer C', 'Transformer C'],
    'input_type': ['Database', 'File', 'File', 'Database', 'File', 'Database'],
    'input_name': ['DB1', 'file1.csv', 'file2.csv', 'DB2', 'file3.csv', 'DB3'],
    'output_type': ['File', 'Database', 'File', 'File', 'Database', 'Database'],
    'output_name': ['file4.csv', 'DB4', 'file5.csv', 'file6.csv', 'DB5', 'DB6'],
    'status': ['success', 'failed', 'success', 'success', 'success', 'failed'],
    'created_date': ['2022-01-01', '2022-01-02', '2022-01-03', '2022-01-04', '2022-01-05', '2022-01-06']
}

etl_db = pd.DataFrame(etl_jobs_data)

# Define the data to display
successful_jobs = etl_db[etl_db['status'] == 'success']
failed_jobs = etl_db[etl_db['status'] == 'failed']
job_counts = etl_db.groupby('transformer_name')['job_id'].nunique()

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
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)

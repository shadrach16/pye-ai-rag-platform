import dash
from dash import dcc
from dash import html
import plotly.graph_objs as go
import pandas as pd

etl_db = pd.DataFrame({
    'job_id': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    'transformer_name': ['transformer_1', 'transformer_1', 'transformer_2', 'transformer_2', 'transformer_3', 'transformer_3', 'transformer_4', 'transformer_4', 'transformer_5', 'transformer_5'],
    'status': ['success', 'success', 'failed', 'success', 'success', 'failed', 'success', 'success', 'failed', 'success'],
    'job_timestamp': ['2022-01-01 12:00:00', '2022-01-02 13:00:00', '2022-01-03 14:00:00', '2022-01-04 15:00:00', '2022-01-05 16:00:00', '2022-01-06 17:00:00', '2022-01-07 18:00:00', '2022-01-08 19:00:00', '2022-01-09 20:00:00', '2022-01-10 21:00:00']
})

# Convert the job_timestamp column to a datetime type
etl_db['job_timestamp'] = pd.to_datetime(etl_db['job_timestamp'])

# Compute the required data for the charts
successful_jobs = etl_db[etl_db['status'] == 'success']
failed_jobs = etl_db[etl_db['status'] == 'failed']
job_counts = etl_db.groupby('transformer_name')['job_id'].nunique()
most_recent_jobs = etl_db.groupby('transformer_name').apply(lambda x: x.nlargest(5, 'job_timestamp'))
most_recent_jobs['job_date'] = pd.to_datetime(most_recent_jobs['job_timestamp']).dt.date


# Create the dashboard components
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1('ETL Dashboard'),
    html.Div([
        html.Div([
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
            )
        ], className='six columns'),
        html.Div([
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
        ], className='six columns')
    ], className='row'),
    html.Div([
        html.Div([
            html.H3('Most Recent Job Statuses by Transformer'),
            html.Table([
                html.Thead(html.Tr([
                    html.Th('Transformer Name'),
                    html.Th('Job ID'),
                    html.Th('Job Status'),
                    html.Th('Job Timestamp')
                ])),
                html.Tbody([
                    html.Tr([
                        html.Td(row['transformer_name']),
                        html.Td(row['job_id']),
                        html.Td(row['status']),
                        html.Td(row['job_date'].strftime('%Y-%m-%d %H:%M:%S'))
                    ]) for _, row in most_recent_jobs.iterrows()
                ])
            ])
        ], className='six columns'),
        html.Div([
            dcc.Graph(
                id='job-timeline-graph',
                figure={
                    'data': [
                        go.Scatter(
                            x=etl_db['job_timestamp'],
                            y=etl_db['job_id'],
                            mode='markers',
                            marker={
                                'color': etl_db['status'].apply(lambda x: 'green' if x == 'success' else 'red'),
                                'size': 10
                            },
                            text=etl_db['transformer_name']
                        )
                    ],
                    'layout': go.Layout(
                        title='Job Timeline',
                        xaxis={'title': 'Job Timestamp'},
                        yaxis={'title': 'Job ID'}
                    )
                }
            )
        ], className='six columns')
    ], className='row')
])

if __name__ == '__main__':
    app.run_server(debug=True)

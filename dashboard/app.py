"""
Dash web dashboard for the induction system
"""

import dash
from dash import dcc, html, Input, Output, callback_context
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import requests
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css'])

# API base URL
API_BASE = "http://localhost:8080/api/v1"

app.layout = html.Div([
    html.H1("KMRL Trainset Induction Dashboard", style={'textAlign': 'center'}),
    
    # Control Panel
    html.Div([
        html.H3("Control Panel"),
        html.Div([
            html.Label("Service Demand:"),
            dcc.Slider(
                id='service-demand-slider',
                min=15, max=25, step=1, value=20,
                marks={i: str(i) for i in range(15, 26)},
                tooltip={"placement": "bottom", "always_visible": True}
            )
        ], style={'width': '48%', 'display': 'inline-block'}),
        
        html.Div([
            html.Button('Optimize Induction', id='optimize-btn', n_clicks=0,
                       style={'backgroundColor': '#007cba', 'color': 'white', 'margin': '10px'}),
            html.Button('Refresh Data', id='refresh-btn', n_clicks=0,
                       style={'backgroundColor': '#28a745', 'color': 'white', 'margin': '10px'}),
        ], style={'textAlign': 'center', 'margin': '20px'})
    ], style={'border': '1px solid #ddd', 'padding': '20px', 'margin': '10px'}),
    
    # Status Overview
    html.Div([
        html.H3("Fleet Status Overview"),
        html.Div(id='status-cards'),
    ], style={'margin': '20px'}),
    
    # Charts
    html.Div([
        html.Div([
            html.H4("Trainset Allocation"),
            dcc.Graph(id='allocation-chart')
        ], style={'width': '48%', 'display': 'inline-block'}),
        
        html.Div([
            html.H4("Priority Scores"),
            dcc.Graph(id='priority-chart')
        ], style={'width': '48%', 'float': 'right', 'display': 'inline-block'})
    ]),
    
    # Detailed Table
    html.Div([
        html.H3("Induction Decisions"),
        html.Div(id='decisions-table')
    ], style={'margin': '20px'}),
    
    # Auto-refresh
    dcc.Interval(
        id='interval-component',
        interval=30*1000,  # Update every 30 seconds
        n_intervals=0
    ),
    
    # Store for data
    dcc.Store(id='trainset-data'),
    dcc.Store(id='decisions-data')
])

@app.callback(
    Output('trainset-data', 'data'),
    [Input('refresh-btn', 'n_clicks'),
     Input('interval-component', 'n_intervals')]
)
def refresh_trainset_data(refresh_clicks, intervals):
    """Fetch trainset data from API"""
    try:
        response = requests.get(f"{API_BASE}/trainsets", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"API error: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"Error fetching trainset data: {e}")
        return []

@app.callback(
    Output('decisions-data', 'data'),
    [Input('optimize-btn', 'n_clicks')],
    [dash.dependencies.State('service-demand-slider', 'value')]
)
def optimize_induction(n_clicks, service_demand):
    """Run optimization and get decisions"""
    if n_clicks == 0:
        return []
    
    try:
        response = requests.post(
            f"{API_BASE}/optimize",
            params={'service_demand': service_demand},
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Optimization API error: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"Error running optimization: {e}")
        return []

@app.callback(
    Output('status-cards', 'children'),
    [Input('trainset-data', 'data')]
)
def update_status_cards(trainset_data):
    """Update status overview cards"""
    if not trainset_data:
        return html.Div("No data available")
    
    # Count trainsets by status
    status_counts = {}
    total_trainsets = len(trainset_data)
    
    for trainset in trainset_data:
        status = trainset.get('current_status', 'unknown')
        status_counts[status] = status_counts.get(status, 0) + 1
    
    # Create status cards
    cards = []
    colors = {
        'revenue_service': '#28a745',
        'standby': '#ffc107', 
        'maintenance': '#dc3545',
        'cleaning': '#17a2b8'
    }
    
    for status, count in status_counts.items():
        color = colors.get(status, '#6c757d')
        cards.append(
            html.Div([
                html.H4(f"{count}", style={'margin': '0', 'color': color}),
                html.P(status.replace('_', ' ').title(), style={'margin': '0'})
            ], style={
                'textAlign': 'center',
                'border': f'2px solid {color}',
                'borderRadius': '5px',
                'padding': '15px',
                'margin': '5px',
                'width': '150px',
                'display': 'inline-block'
            })
        )
    
    return cards

@app.callback(
    Output('allocation-chart', 'figure'),
    [Input('decisions-data', 'data')]
)
def update_allocation_chart(decisions_data):
    """Update allocation pie chart"""
    if not decisions_data:
        return go.Figure()
    
    # Count allocations
    allocations = {}
    for decision in decisions_data:
        status = decision.get('recommended_status', 'unknown')
        allocations[status] = allocations.get(status, 0) + 1
    
    fig = px.pie(
        values=list(allocations.values()),
        names=list(allocations.keys()),
        title="Recommended Allocation"
    )
    
    return fig

@app.callback(
    Output('priority-chart', 'figure'),
    [Input('decisions-data', 'data')]
)
def update_priority_chart(decisions_data):
    """Update priority scores bar chart"""
    if not decisions_data:
        return go.Figure()
    
    # Extract priority scores
    trainset_ids = [d['trainset_id'] for d in decisions_data]
    scores = [d['priority_score'] for d in decisions_data]
    
    fig = px.bar(
        x=trainset_ids,
        y=scores,
        title="Priority Scores by Trainset",
        labels={'x': 'Trainset ID', 'y': 'Priority Score'}
    )
    
    fig.update_layout(xaxis_tickangle=-45)
    return fig

@app.callback(
    Output('decisions-table', 'children'),
    [Input('decisions-data', 'data')]
)
def update_decisions_table(decisions_data):
    """Update decisions table"""
    if not decisions_data:
        return html.Div("Run optimization to see decisions")
    
    # Create table rows
    header = html.Tr([
        html.Th("Trainset ID"),
        html.Th("Recommended Status"),
        html.Th("Priority Score"),
        html.Th("Reasoning"),
        html.Th("Conflicts")
    ])
    
    rows = [header]
    for decision in decisions_data:
        row = html.Tr([
            html.Td(decision['trainset_id']),
            html.Td(decision['recommended_status'].replace('_', ' ').title()),
            html.Td(f"{decision['priority_score']:.3f}"),
            html.Td("; ".join(decision.get('reasoning', []))),
            html.Td("; ".join(decision.get('conflicts', [])) or "None")
        ])
        rows.append(row)
    
    return html.Table(rows, style={'width': '100%', 'border': '1px solid #ddd'})

if __name__ == '__main__':
    app.run_server(debug=True, port=8050)
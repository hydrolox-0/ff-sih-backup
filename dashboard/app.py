"""
Dash web dashboard for the induction system
"""

import dash
from dash import dcc, html, Input, Output, callback_context, State
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import requests
from datetime import datetime, timedelta
import logging
import json
import os
from config.loader import config_loader

# Load failure prediction data
def load_failure_predictions():
    """Load ML failure predictions from CSV"""
    try:
        df = pd.read_csv('data/failure_predictions.csv')
        # Convert train_id to uppercase to match dashboard format (TS-001 vs ts-001)
        df['train_id'] = df['train_id'].str.upper()
        # Create a dictionary for quick lookup
        failure_dict = {}
        for _, row in df.iterrows():
            failure_dict[row['train_id']] = {
                'probability': row['failure_probability'],
                'flag_for_review': row['flag_for_review']
            }
        return failure_dict
    except Exception as e:
        print(f"Error loading failure predictions: {e}")
        return {}

logger = logging.getLogger(__name__)

# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css'])

# Load users from JSON for authentication
def load_users():
    try:
        with open('config/users.json', 'r') as f:
            return json.load(f)
    except:
        return {}  # Allow access if file missing

def validate_user(email, password):
    """Validate user credentials"""
    users = load_users()
    return users.get(email) == password

# Login page layout
def create_login_layout():
    return html.Div([
        html.Div([
            html.Div([
                html.H2("KMRL Trainset Induction System", 
                       style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': '30px'}),
                html.H4("Login", 
                       style={'textAlign': 'center', 'color': '#34495e', 'marginBottom': '30px'}),
                
                html.Div([
                    html.Label("Email:", style={'fontWeight': 'bold', 'marginBottom': '5px', 'display': 'block'}),
                    dcc.Input(
                        id='login-email',
                        type='email',
                        placeholder='Enter your email',
                        style={
                            'width': '100%',
                            'padding': '12px',
                            'marginBottom': '20px',
                            'border': '1px solid #ddd',
                            'borderRadius': '4px',
                            'fontSize': '16px'
                        }
                    ),
                    
                    html.Label("Password:", style={'fontWeight': 'bold', 'marginBottom': '5px', 'display': 'block'}),
                    dcc.Input(
                        id='login-password',
                        type='password',
                        placeholder='Enter your password',
                        style={
                            'width': '100%',
                            'padding': '12px',
                            'marginBottom': '20px',
                            'border': '1px solid #ddd',
                            'borderRadius': '4px',
                            'fontSize': '16px'
                        }
                    ),
                    
                    html.Button(
                        'Login',
                        id='login-button',
                        n_clicks=0,
                        style={
                            'width': '100%',
                            'padding': '12px',
                            'backgroundColor': '#3498db',
                            'color': 'white',
                            'border': 'none',
                            'borderRadius': '4px',
                            'fontSize': '16px',
                            'cursor': 'pointer',
                            'marginBottom': '20px'
                        }
                    ),
                    
                    html.Div(id='login-error', style={'color': 'red', 'textAlign': 'center'})
                    
                ], style={'padding': '20px'})
                
            ], style={
                'maxWidth': '400px',
                'margin': '100px auto',
                'backgroundColor': 'white',
                'borderRadius': '8px',
                'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
                'border': '1px solid #e1e8ed'
            })
        ], style={
            'minHeight': '100vh',
            'backgroundColor': '#ecf0f1',
            'fontFamily': 'Arial, sans-serif'
        })
    ])

# API base URL
API_BASE = "http://localhost:8080/api/v1"

# Load configuration for dynamic slider
fleet_config = config_loader.get_fleet_config()
total_trainsets = fleet_config.get('total_trainsets', 25)
target_service = fleet_config.get('target_service_trainsets', 20)

# Calculate slider range (always start from 10, max 90% of total trainsets)
slider_min = 10
slider_max = min(total_trainsets, int(total_trainsets * 0.9))
slider_default = min(target_service, slider_max)

# Main dashboard layout (your existing layout)
def create_dashboard_layout():
    return html.Div([

        # Dark mode toggle
        html.Div([
            html.Button('🌙', id='dark-mode-toggle', n_clicks=0,
                       style={'position': 'absolute', 'top': '10px', 'right': '10px', 
                             'backgroundColor': 'transparent', 'border': 'none', 
                             'fontSize': '24px', 'cursor': 'pointer', 'zIndex': '1000'})
        ]),
        
        html.H1("KMRL Trainset Induction Dashboard", style={'textAlign': 'center'}),
    
    # Control Panel
    html.Div([
        html.H3("Control Panel"),
        html.Div([
            html.Label("Service Demand:"),
            dcc.Slider(
                id='service-demand-slider',
                min=slider_min, max=slider_max, step=1, value=slider_default,
                marks={i: str(i) for i in range(slider_min, slider_max + 1)},
                tooltip={"placement": "bottom", "always_visible": True}
            )
        ], style={'width': '48%', 'display': 'inline-block'}),
        
        html.Div([
            html.Button('Optimize Induction', id='optimize-btn', n_clicks=0),
            html.Button('Refresh Data', id='refresh-btn', n_clicks=0),
        ], style={'textAlign': 'center', 'margin': '20px'})
    ], id='control-panel'),
    
    # Status Overview
    html.Div([
        html.H3("Fleet Status Overview"),
        html.Div(id='status-cards'),
    ], id='status-overview', style={'margin': '20px'}),
    
    # Charts
    html.Div([
        html.Div([
            html.H4("Trainset Allocation"),
            dcc.Graph(id='allocation-chart')
        ], id='allocation-container', style={'width': '48%', 'display': 'inline-block'}),
        
        html.Div([
            html.H4("Priority Scores"),
            dcc.Graph(id='priority-chart')
        ], id='priority-container', style={'width': '48%', 'float': 'right', 'display': 'inline-block'})
    ], id='charts-section'),
    
    # Detailed Table
    html.Div([
        html.H3("Induction Decisions"),
        html.Div(id='decisions-table')
    ], id='decisions-section', style={'margin': '20px'}),
    
    # Auto-refresh
    dcc.Interval(
        id='interval-component',
        interval=30*1000,  # Update every 30 seconds
        n_intervals=0
    ),
    
        # Store for data
        dcc.Store(id='trainset-data'),
        dcc.Store(id='decisions-data'),
        dcc.Store(id='theme-store', data={'dark_mode': False})
    ], id='main-container')

# App layout with session management
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='session-store', data={'authenticated': False}),
    html.Div(id='page-content')
])

# Authentication callback
@app.callback(
    [Output('session-store', 'data'),
     Output('login-error', 'children')],
    [Input('login-button', 'n_clicks')],
    [State('login-email', 'value'),
     State('login-password', 'value'),
     State('session-store', 'data')]
)
def authenticate_user(n_clicks, email, password, session_data):
    if n_clicks == 0:
        return session_data, ""
    
    if not email or not password:
        return session_data, "Please enter both email and password"
    
    if validate_user(email, password):
        return {'authenticated': True, 'user': email}, ""
    else:
        return session_data, "Invalid email or password"

# Page routing callback
@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname'),
     Input('session-store', 'data')]
)
def display_page(pathname, session_data):
    if session_data.get('authenticated', False):
        return create_dashboard_layout()
    else:
        return create_login_layout()

# Dark mode styles
def get_theme_styles(dark_mode):
    if dark_mode:
        return {
            'main_container': {
                'backgroundColor': '#1a1a1a',
                'color': '#ffffff',
                'minHeight': '100vh',
                'fontFamily': 'Arial, sans-serif'
            },
            'panel': {
                'border': '1px solid #444',
                'backgroundColor': '#2d2d2d',
                'padding': '20px',
                'margin': '10px'
            },
            'button_primary': {
                'backgroundColor': '#0056b3',
                'color': 'white',
                'margin': '10px',
                'border': 'none',
                'padding': '10px 20px',
                'borderRadius': '4px'
            },
            'button_success': {
                'backgroundColor': '#1e7e34',
                'color': 'white',
                'margin': '10px',
                'border': 'none',
                'padding': '10px 20px',
                'borderRadius': '4px'
            },
            'status_card': {
                'backgroundColor': '#2d2d2d',
                'border': '2px solid',
                'borderRadius': '5px',
                'padding': '15px',
                'margin': '5px',
                'width': '150px',
                'display': 'inline-block',
                'textAlign': 'center'
            },
            'table': {
                'width': '100%',
                'border': '1px solid #444',
                'backgroundColor': '#2d2d2d',
                'color': '#ffffff'
            },
            'chart_container': {
                'backgroundColor': '#2d2d2d',
                'padding': '15px',
                'borderRadius': '5px',
                'margin': '10px',
                'border': '1px solid #444'
            }
        }
    else:
        return {
            'main_container': {
                'backgroundColor': '#ffffff',
                'color': '#000000',
                'minHeight': '100vh',
                'fontFamily': 'Arial, sans-serif'
            },
            'panel': {
                'border': '1px solid #ddd',
                'backgroundColor': '#ffffff',
                'padding': '20px',
                'margin': '10px'
            },
            'button_primary': {
                'backgroundColor': '#007cba',
                'color': 'white',
                'margin': '10px',
                'border': 'none',
                'padding': '10px 20px',
                'borderRadius': '4px'
            },
            'button_success': {
                'backgroundColor': '#28a745',
                'color': 'white',
                'margin': '10px',
                'border': 'none',
                'padding': '10px 20px',
                'borderRadius': '4px'
            },
            'status_card': {
                'backgroundColor': '#ffffff',
                'border': '2px solid',
                'borderRadius': '5px',
                'padding': '15px',
                'margin': '5px',
                'width': '150px',
                'display': 'inline-block',
                'textAlign': 'center'
            },
            'table': {
                'width': '100%',
                'border': '1px solid #ddd',
                'backgroundColor': '#ffffff',
                'color': '#000000'
            },
            'chart_container': {
                'backgroundColor': '#ffffff',
                'padding': '15px',
                'borderRadius': '5px',
                'margin': '10px',
                'border': '1px solid #ddd'
            }
        }

@app.callback(
    [Output('theme-store', 'data'),
     Output('dark-mode-toggle', 'children')],
    [Input('dark-mode-toggle', 'n_clicks')],
    [dash.dependencies.State('theme-store', 'data')]
)
def toggle_dark_mode(n_clicks, theme_data):
    """Toggle between dark and light mode"""
    if n_clicks == 0:
        return theme_data, '🌙'
    
    current_dark_mode = theme_data.get('dark_mode', False)
    new_dark_mode = not current_dark_mode
    
    icon = '☀️' if new_dark_mode else '🌙'
    
    return {'dark_mode': new_dark_mode}, icon

@app.callback(
    Output('main-container', 'style'),
    [Input('theme-store', 'data')]
)
def update_main_container_style(theme_data):
    """Update main container styling based on theme"""
    dark_mode = theme_data.get('dark_mode', False)
    styles = get_theme_styles(dark_mode)
    return styles['main_container']

@app.callback(
    [Output('control-panel', 'style'),
     Output('optimize-btn', 'style'),
     Output('refresh-btn', 'style')],
    [Input('theme-store', 'data')]
)
def update_control_panel_style(theme_data):
    """Update control panel styling based on theme"""
    dark_mode = theme_data.get('dark_mode', False)
    styles = get_theme_styles(dark_mode)
    
    return (
        styles['panel'],
        styles['button_primary'],
        styles['button_success']
    )

@app.callback(
    [Output('charts-section', 'style'),
     Output('allocation-container', 'style'),
     Output('priority-container', 'style')],
    [Input('theme-store', 'data')]
)
def update_chart_container_styles(theme_data):
    """Update chart container styling based on theme"""
    dark_mode = theme_data.get('dark_mode', False)
    styles = get_theme_styles(dark_mode)
    
    # Charts section with flexbox for horizontal alignment
    charts_section_style = {
        'display': 'flex',
        'flexDirection': 'row',
        'justifyContent': 'space-between',
        'alignItems': 'flex-start',
        'gap': '20px',
        'margin': '20px 0'
    }
    
    allocation_style = styles['chart_container'].copy()
    allocation_style.update({
        'flex': '1',
        'minWidth': '0'
    })
    
    priority_style = styles['chart_container'].copy()
    priority_style.update({
        'flex': '1',
        'minWidth': '0'
    })
    
    return charts_section_style, allocation_style, priority_style

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
    [Input('trainset-data', 'data'),
     Input('theme-store', 'data')]
)
def update_status_cards(trainset_data, theme_data):
    """Update status overview cards"""
    if not trainset_data:
        return html.Div("No data available")
    
    dark_mode = theme_data.get('dark_mode', False)
    styles = get_theme_styles(dark_mode)
    
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
        card_style = styles['status_card'].copy()
        card_style['borderColor'] = color
        
        cards.append(
            html.Div([
                html.H4(f"{count}", style={'margin': '0', 'color': color}),
                html.P(status.replace('_', ' ').title(), style={'margin': '0'})
            ], style=card_style)
        )
    
    return cards

@app.callback(
    Output('allocation-chart', 'figure'),
    [Input('decisions-data', 'data'),
     Input('theme-store', 'data')]
)
def update_allocation_chart(decisions_data, theme_data):
    """Update allocation pie chart"""
    if not decisions_data:
        return go.Figure()
    
    dark_mode = theme_data.get('dark_mode', False)
    
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
    
    # Apply dark mode styling
    if dark_mode:
        fig.update_layout(
            plot_bgcolor='#2d2d2d',
            paper_bgcolor='#2d2d2d',
            font_color='#ffffff',
            title_font_color='#ffffff'
        )
    else:
        fig.update_layout(
            plot_bgcolor='#ffffff',
            paper_bgcolor='#ffffff',
            font_color='#000000',
            title_font_color='#000000'
        )
    
    return fig

@app.callback(
    Output('priority-chart', 'figure'),
    [Input('decisions-data', 'data'),
     Input('theme-store', 'data')]
)
def update_priority_chart(decisions_data, theme_data):
    """Update priority scores bar chart"""
    if not decisions_data:
        return go.Figure()
    
    dark_mode = theme_data.get('dark_mode', False)
    
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
    
    # Apply dark mode styling
    if dark_mode:
        fig.update_layout(
            plot_bgcolor='#2d2d2d',
            paper_bgcolor='#2d2d2d',
            font_color='#ffffff',
            title_font_color='#ffffff',
            xaxis=dict(gridcolor='#444444', color='#ffffff'),
            yaxis=dict(gridcolor='#444444', color='#ffffff')
        )
    else:
        fig.update_layout(
            plot_bgcolor='#ffffff',
            paper_bgcolor='#ffffff',
            font_color='#000000',
            title_font_color='#000000',
            xaxis=dict(gridcolor='#cccccc', color='#000000'),
            yaxis=dict(gridcolor='#cccccc', color='#000000')
        )
    
    return fig

@app.callback(
    Output('decisions-table', 'children'),
    [Input('decisions-data', 'data'),
     Input('theme-store', 'data')]
)
def update_decisions_table(decisions_data, theme_data):
    """Update decisions table"""
    if not decisions_data:
        return html.Div("Run optimization to see decisions")
    
    dark_mode = theme_data.get('dark_mode', False)
    styles = get_theme_styles(dark_mode)
    
    # Load failure predictions
    failure_predictions = load_failure_predictions()
    
    # Create table rows
    header = html.Tr([
        html.Th("Trainset ID"),
        html.Th("Recommended Status"),
        html.Th("Priority Score"),
        html.Th("Reasoning"),
        html.Th("Risk Alert")
    ])
    
    rows = [header]
    for decision in decisions_data:
        trainset_id = decision['trainset_id']
        
        # Check if this trainset has failure risk
        risk_cell = html.Td("")  # Default empty cell
        if trainset_id in failure_predictions:
            prediction = failure_predictions[trainset_id]
            if prediction['flag_for_review']:
                # Create red warning icon with tooltip
                risk_cell = html.Td([
                    html.Span(
                        "⚠️",
                        id=f"risk-icon-{trainset_id}",
                        style={
                            'color': 'red',
                            'fontSize': '18px',
                            'cursor': 'pointer'
                        }
                    ),
                    # Tooltip using title attribute
                    html.Span(
                        f"Risk of failure - Early Warning System (Probability: {prediction['probability']:.1%})",
                        style={'display': 'none'}
                    )
                ], title=f"Risk of failure - Early Warning System (Probability: {prediction['probability']:.1%})")
        
        row = html.Tr([
            html.Td(trainset_id),
            html.Td(decision['recommended_status'].replace('_', ' ').title()),
            html.Td(f"{decision['priority_score']:.3f}"),
            html.Td("; ".join(decision.get('reasoning', []))),
            risk_cell
        ])
        rows.append(row)
    
    return html.Table(rows, style=styles['table'])

if __name__ == '__main__':
    app.run_server(debug=True, port=8050)
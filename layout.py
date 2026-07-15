# layout.py
from dash import dcc, html
from config import COLORS

def create_layout():
    return html.Div([
        # Hidden Storage Memory Fields
        dcc.Store(id='file-repository-store', storage_type='memory'),
        dcc.Store(id='chat-history-repository', storage_type='memory'),
        dcc.Store(id='visible-columns-config-store', storage_type='memory'),
        
        # Background Heartbeat Synchronizer (10 seconds)
        dcc.Interval(id='directory-scan-heartbeat', interval=10000, n_intervals=0),
        
        # Upper Navigation App Banner
        html.Div([
            html.Div([
                html.Button("☰", id="toggle-sidebar-btn", n_clicks=0, style={
                    'backgroundColor': 'transparent', 'border': 'none', 'fontSize': '1.2rem', 
                    'cursor': 'pointer', 'color': COLORS['text_main'], 'marginRight': '12px'
                }),
                html.H1("Portfolio Analytics Suite", style={'margin': 0, 'fontSize': '1.3rem', 'color': COLORS['primary'], 'fontWeight': '700'})
            ], style={'display': 'flex', 'alignItems': 'center'}),
            
            html.Div(id='sheet-status-indicator', style={'fontSize': '0.8rem', 'color': '#64748b', 'fontWeight': '500'})
        ], style={
            'height': '60px', 'backgroundColor': '#fff', 'borderBottom': f"1px solid {COLORS['border']}",
            'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between', 'padding': '0 24px',
            'position': 'fixed', 'top': 0, 'left': 0, 'right': 0, 'zIndex': 100
        }),
        
        # Main Window Split Layout Container
        html.Div([
            
            # Left Sidebar Panel: Sheet Manager Selector
            html.Div([
                html.P("AVAILABLE TRACKERS", style={'fontSize': '0.7rem', 'fontWeight': '700', 'color': '#94a3b8', 'letterSpacing': '1px', 'margin': '0 0 14px 0'}),
                dcc.Dropdown(id='active-sheet-dropdown', placeholder="Select active source tracker...", style={'marginBottom': '20px', 'display': 'none'}),
                html.Div(id='gemini-file-list-stream', style={'display': 'flex', 'flexDirection': 'column', 'gap': '6px', 'flex': 1, 'overflowY': 'auto'})
            ], id='app-sidebar-panel', style={
                'width': '260px', 'backgroundColor': '#fff', 'borderRight': f"1px solid {COLORS['border']}",
                'position': 'fixed', 'top': '60px', 'bottom': 0, 'left': 0, 'padding': '24px',
                'display': 'flex', 'flexDirection': 'column', 'zIndex': 90
            }),
            
            # Main Analytics Data Viewport
            html.Div([
                
                # Top Performance Metrics Ribbon Panel
                html.Div(id='executive-metrics-ribbon', style={'display': 'flex', 'gap': '16px', 'marginBottom': '24px'}),
                
                # Mid Section Double Column Charts Group
                html.Div([
                    html.Div([
                        html.H3("📊 Progress Matrix View", style={'margin': '0 0 4px 0', 'fontSize': '1rem', 'color': COLORS['text_main']}),
                        html.P("Task item operational status grouped by workspace tracks", style={'margin': '0 0 16px 0', 'fontSize': '0.78rem', 'color': '#64748b'}),
                        dcc.Graph(id='status-matrix-chart', config={'displayModeBar': False})
                    ], style={'flex': 1, 'backgroundColor': '#fff', 'padding': '24px', 'borderRadius': '12px', 'border': f"1px solid {COLORS['border']}"}),
                    
                    html.Div([
                        html.H3("👷 Resource Workload Distribution", style={'margin': '0 0 4px 0', 'fontSize': '1rem', 'color': COLORS['text_main']}),
                        html.P("Active task volume assigned across team resources", style={'margin': '0 0 16px 0', 'fontSize': '0.78rem', 'color': '#64748b'}),
                        dcc.Graph(id='predictive-stacked-chart', config={'displayModeBar': False})
                    ], style={'flex': 1, 'backgroundColor': '#fff', 'padding': '24px', 'borderRadius': '12px', 'border': f"1px solid {COLORS['border']}"})
                ], style={'display': 'flex', 'gap': '24px', 'marginBottom': '24px'}),
                
                # Bottom Row Grid: Interactive Table Block
                html.Div([
                    html.Div([
                        html.Div([
                            html.H3("📑 Tracked Task Ledger Matrix", style={'margin': 0, 'fontSize': '1rem', 'color': COLORS['text_main']}),
                            html.P("Interactive row inspector for complete project milestones", style={'margin': '4px 0 0 0', 'fontSize': '0.78rem', 'color': '#64748b'})
                        ]),
                        # Customize Columns Control Trigger Button positioned next to headers
                        html.Button("⚙️ Customize Columns", id="open-column-modal-btn", n_clicks=0, style={
                            'padding': '8px 14px', 'backgroundColor': '#f1f5f9', 'border': f"1px solid {COLORS['border']}",
                            'borderRadius': '6px', 'fontSize': '0.82rem', 'fontWeight': '500', 'color': '#475569', 'cursor': 'pointer'
                        })
                    ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 'marginBottom': '20px'}),
                    
                    html.Div(id='master-table-container')
                ], style={'backgroundColor': '#fff', 'padding': '24px', 'borderRadius': '12px', 'border': f"1px solid {COLORS['border']}", 'marginBottom': '40px'})
                
            ], id='main-content-viewport', style={'marginLeft': '285px', 'padding': '40px', 'marginTop': '60px', 'flex': 1, 'transition': 'all 0.2s'})
            
        ], style={'display': 'flex', 'minHeight': '100vh', 'backgroundColor': '#f8fafc'}),
        
        # Pop-up Dialog Modal for Column Checkboxes (Shows/Hides columns dynamically)
        html.Div([
            html.Div([
                html.Div([
                    html.H4("Customize columns", style={'margin': 0, 'fontSize': '1.1rem', 'color': COLORS['primary'], 'fontWeight': '600'}),
                    html.Button("✕", id="close-column-modal-btn", n_clicks=0, style={
                        'border': 'none', 'backgroundColor': 'transparent', 'fontSize': '1.1rem', 'cursor': 'pointer', 'color': '#94a3b8'
                    })
                ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 'paddingBottom': '16px', 'borderBottom': f"1px solid {COLORS['border']}"}),
                
                html.P("Show or hide columns", style={'fontSize': '0.82rem', 'color': '#64748b', 'margin': '16px 0 12px 0', 'fontWeight': '500'}),
                
                # Checkbox container
                html.Div([
                    dcc.Checklist(
                        id='column-selection-checklist',
                        options=[],
                        value=[],
                        labelStyle={'display': 'flex', 'alignItems': 'center', 'gap': '10px', 'padding': '8px 0', 'fontSize': '0.88rem', 'color': '#334155', 'cursor': 'pointer'},
                        style={'display': 'flex', 'flexDirection': 'column', 'maxHeight': '260px', 'overflowY': 'auto'}
                    )
                ], style={'marginBottom': '24px'}),
                
                html.Div([
                    html.Button("Cancel", id="cancel-column-modal-btn", n_clicks=0, style={
                        'padding': '8px 16px', 'backgroundColor': 'transparent', 'border': f"1px solid {COLORS['border']}", 'borderRadius': '6px', 'fontSize': '0.85rem', 'cursor': 'pointer', 'color': '#64748b'
                    }),
                    html.Button("Apply", id="apply-column-modal-btn", n_clicks=0, style={
                        'padding': '8px 16px', 'backgroundColor': COLORS['secondary'], 'border': 'none', 'borderRadius': '6px', 'fontSize': '0.85rem', 'cursor': 'pointer', 'color': 'white', 'fontWeight': '500'
                    })
                ], style={'display': 'flex', 'justifyContent': 'flex-end', 'gap': '10px', 'paddingTop': '16px', 'borderTop': f"1px solid {COLORS['border']}"})
            ], style={
                'backgroundColor': 'white', 'width': '400px', 'borderRadius': '12px', 'padding': '24px', 'boxShadow': '0 20px 25px -5px rgba(0,0,0,0.1), 0 10px 10px -5px rgba(0,0,0,0.04)'
            })
        ], id="column-customizer-modal", style={
            'position': 'fixed', 'top': 0, 'left': 0, 'right': 0, 'bottom': 0, 'backgroundColor': 'rgba(15, 23, 42, 0.4)',
            'zIndex': 1000, 'display': 'none', 'alignItems': 'center', 'justifyContent': 'center'
        }),
        
        # Right Drawer AI Float Token Widget Wrapper
        html.Div([
            html.Div("💬 AI", id="chat-circle-token", n_clicks=0, style={
                'width': '56px', 'height': '56px', 'borderRadius': '50%', 'backgroundColor': COLORS['primary'],
                'color': 'white', 'display': 'none', 'alignItems': 'center', 'justifyContent': 'center',
                'boxShadow': '0 4px 12px rgba(0,0,0,0.15)', 'cursor': 'pointer', 'fontWeight': '600', 'fontSize': '0.9rem'
            }),
            
            html.Div([
                html.Div([
                    html.Span("🤖 Analytics Co-Pilot", style={'fontWeight': '600', 'fontSize': '0.88rem', 'color': COLORS['primary']}),
                    html.Button("—", id="minimize-btn", n_clicks=0, style={
                        'border': 'none', 'backgroundColor': 'transparent', 'cursor': 'pointer', 'fontSize': '1rem', 'color': '#64748b'
                    })
                ], style={
                    'padding': '14px 16px', 'borderBottom': f"1px solid {COLORS['border']}", 'display': 'flex',
                    'justifyContent': 'space-between', 'alignItems': 'center', 'backgroundColor': '#f8fafc',
                    'borderTopLeftRadius': '12px', 'borderTopRightRadius': '12px'
                }),
                html.Div(id="chat-history-stream", style={
                    'flex': 1, 'padding': '16px', 'overflowY': 'auto', 'display': 'flex', 'flexDirection': 'column', 'gap': '10px'
                }),
                html.Div([
                    dcc.Input(id="chat-user-input", type="text", placeholder="Ask co-pilot about task blockers...", n_submit=0, style={
                        'flex': 1, 'padding': '10px 12px', 'borderRadius': '6px', 'border': f"1px solid {COLORS['border']}", 'fontSize': '0.82rem'
                    }),
                    html.Button("Send", id="send-chat-btn", n_clicks=0, style={
                        'padding': '10px 14px', 'backgroundColor': COLORS['primary'], 'color': 'white', 'border': 'none',
                        'borderRadius': '6px', 'fontSize': '0.82rem', 'cursor': 'pointer', 'fontWeight': '500'
                    })
                ], style={'padding': '12px 16px', 'borderTop': f"1px solid {COLORS['border']}", 'display': 'flex', 'gap': '8px'})
            ], id="chat-panel-window", style={
                'width': '340px', 'height': '460px', 'backgroundColor': '#fff', 'borderRadius': '12px',
                'boxShadow': '0 8px 24px rgba(0,0,0,0.12)', 'display': 'flex', 'flexDirection': 'column',
                'border': f"1px solid {COLORS['border']}"
            })
        ], id="toggle-bar-wrapper", style={'position': 'fixed', 'bottom': '25px', 'right': '25px', 'zIndex': 200})
    ])
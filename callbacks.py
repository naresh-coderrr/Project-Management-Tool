# callbacks.py
import io
import os
import glob
import pandas as pd
import plotly.express as px
from dash import Input, Output, State, html, dash_table, no_update, ALL, ctx

from config import COLORS
import database as db

# Targets your system directory path for local CSV assets
TARGET_DIR = r"C:\Users\DELL\OneDrive\文档\Office"

def register_callbacks(app):
    
    # 1. LIVE REPOSITORY SYNCHRONIZER
    @app.callback(
        Output('file-repository-store', 'data'),
        Input('directory-scan-heartbeat', 'n_intervals'),
        State('file-repository-store', 'data')
    )
    def silent_directory_sync(n_intervals, current_repo):
        current_repo = current_repo if current_repo else {}

        if os.path.exists(TARGET_DIR):
            search_path = os.path.join(TARGET_DIR, "**", "*.csv")
            for filepath in glob.glob(search_path, recursive=True):
                filename = os.path.basename(filepath)
                
                try:
                    raw_df = pd.read_csv(filepath, encoding='latin1')
                    raw_df = raw_df.dropna(how='all')
                    if raw_df.empty:
                        continue

                    processed_rows = []
                    current_section = "General Project Portfolio"
                    raw_df.columns = [str(c).strip().lower() for c in raw_df.columns]

                    for idx, row in raw_df.iterrows():
                        sno_raw = str(row.get('s.no', '')).strip() if pd.notna(row.get('s.no')) else ''
                        task_raw = str(row.get('task', '')).strip() if pd.notna(row.get('task')) else ''
                        
                        if not sno_raw and not task_raw:
                            continue
                            
                        if not sno_raw and task_raw:
                            if any(keyword in task_raw.lower() for keyword in ["project", "integration", "wave", "bip"]):
                                current_section = task_raw
                            continue
                            
                        if task_raw:
                            row_dict = row.to_dict()
                            row_dict['projectgroup'] = current_section
                            processed_rows.append(row_dict)

                    if not processed_rows:
                        continue

                    df = pd.DataFrame(processed_rows)
                    df = df[df['task'].astype(str).str.strip() != '']

                    current_repo[filename] = df.to_json(date_format='iso', orient='split')
                    
                except Exception as e:
                    print(f"❌ Error processing file {filename}: {str(e)}")
                    continue
        return current_repo

    # 2. RUN SHEET DROPDOWN POPULATOR
    @app.callback(
        Output('gemini-file-list-stream', 'children'),
        Output('active-sheet-dropdown', 'options'),
        Output('active-sheet-dropdown', 'value'),
        Output('chat-history-repository', 'data'),
        Input('file-repository-store', 'data'),
        Input({'type': 'sidebar-file-item', 'index': ALL}, 'n_clicks'),
        State('active-sheet-dropdown', 'value'),
        State('chat-history-repository', 'data'),
        prevent_initial_call=True
    )
    def render_gemini_sidebar_links(repo_data, list_clicks, current_active_val, chat_repo):
        chat_repo = chat_repo or {}
        if not repo_data:
            return html.P("No trackers loaded.", style={'padding':'10px','color':'#94a3b8'}), [], None, chat_repo

        triggered_id = ctx.triggered_id
        if isinstance(triggered_id, dict) and triggered_id.get('type') == 'sidebar-file-item':
            current_active_val = triggered_id.get('index')
                
        file_keys = list(repo_data.keys())
        if not current_active_val and file_keys: current_active_val = file_keys[0]
        if current_active_val and current_active_val in file_keys:
            chat_repo[current_active_val] = db.load_chat_history(current_active_val)

        sidebar_children = []
        for f_name in file_keys:
            is_selected = (f_name == current_active_val)
            sidebar_children.append(html.Button(
                f"📄 {f_name}", id={'type': 'sidebar-file-item', 'index': f_name}, n_clicks=0,
                style={
                    'textAlign': 'left', 'padding': '10px 12px', 'borderRadius': '6px', 'border': 'none', 'fontSize': '0.82rem', 
                    'cursor': 'pointer', 'fontWeight': '500', 'width': '100%',
                    'backgroundColor': '#f1f5f9' if is_selected else 'transparent',
                    'color': COLORS['secondary'] if is_selected else '#475569',
                    'whiteSpace': 'nowrap', 'overflow': 'hidden', 'textOverflow': 'ellipsis', 'transition': 'all 0.1s'
                }
            ))
        return sidebar_children, [{'label': k, 'value': k} for k in file_keys], current_active_val, chat_repo

    # 3. SIDEBAR PANEL VISIBILITY TOGGLE
    @app.callback(
        Output('app-sidebar-panel', 'style'), Output('main-content-viewport', 'style'), Output('toggle-bar-wrapper', 'style'),
        Input('toggle-sidebar-btn', 'n_clicks'), State('app-sidebar-panel', 'style'), State('main-content-viewport', 'style'), State('toggle-bar-wrapper', 'style'),
        prevent_initial_call=True
    )
    def toggle_sidebar_visibility(n_clicks, sidebar_style, content_style, bar_style):
        sidebar_style, content_style, bar_style = sidebar_style or {}, content_style or {}, bar_style or {}
        if sidebar_style.get('display') != 'none':
            sidebar_style['display'], content_style['marginLeft'], bar_style['left'] = 'none', '20px', '25px'
        else:
            sidebar_style['display'], content_style['marginLeft'], bar_style['left'] = 'flex', '295px', '285px'
        return sidebar_style, content_style, bar_style

    # 4. CUSTOM DIALOG MODAL CONTROLLER (Toggles custom checkboxes window)
    @app.callback(
        Output('column-customizer-modal', 'style'),
        Output('column-selection-checklist', 'options'),
        Output('column-selection-checklist', 'value'),
        Output('visible-columns-config-store', 'data'),
        Input('open-column-modal-btn', 'n_clicks'),
        Input('close-column-modal-btn', 'n_clicks'),
        Input('cancel-column-modal-btn', 'n_clicks'),
        Input('apply-column-modal-btn', 'n_clicks'),
        Input('active-sheet-dropdown', 'value'),
        State('column-selection-checklist', 'value'),
        State('file-repository-store', 'data'),
        State('visible-columns-config-store', 'data'),
        prevent_initial_call=True
    )
    def control_modal_operations(open_c, close_c, cancel_c, apply_c, active_file, checked_vals, repo_data, config_store):
        config_store = config_store if config_store else {}
        trigger = ctx.triggered_id
        
        modal_style = {'position': 'fixed', 'top': 0, 'left': 0, 'right': 0, 'bottom': 0, 'backgroundColor': 'rgba(15, 23, 42, 0.4)', 'zIndex': 1000, 'display': 'none', 'alignItems': 'center', 'justifyContent': 'center'}
        
        if not active_file or not repo_data or active_file not in repo_data:
            return modal_style, [], [], config_store

        df = pd.read_json(io.StringIO(repo_data[active_file]), orient='split')
        all_cols = [str(c).strip() for c in df.columns if str(c).strip().lower() != 'projectgroup']
        checklist_options = [{'label': c.upper() if c.lower() != 's.no' else 'S.No', 'value': c.lower()} for c in all_cols]

        if active_file not in config_store:
            config_store[active_file] = [c.lower() for c in all_cols]

        if trigger == 'active-sheet-dropdown':
            return modal_style, checklist_options, config_store[active_file], config_store

        if trigger == 'open-column-modal-btn':
            modal_style['display'] = 'flex'
            return modal_style, checklist_options, config_store[active_file], config_store

        if trigger == 'apply-column-modal-btn':
            config_store[active_file] = checked_vals
            modal_style['display'] = 'none'
            return modal_style, checklist_options, checked_vals, config_store

        if trigger in ['close-column-modal-btn', 'cancel-column-modal-btn']:
            modal_style['display'] = 'none'
            return modal_style, checklist_options, config_store[active_file], config_store

        return modal_style, checklist_options, config_store[active_file], config_store

    # 5. RENDERING CHARTS & DYNAMIC MASTER VIEW (Hides default Plotly modebars)
    @app.callback(
        Output('executive-metrics-ribbon', 'children'),
        Output('status-matrix-chart', 'figure'),
        Output('predictive-stacked-chart', 'figure'),
        Output('master-table-container', 'children'),
        Output('sheet-status-indicator', 'children'),
        Input('active-sheet-dropdown', 'value'),
        Input('visible-columns-config-store', 'data'),
        State('file-repository-store', 'data')
    )
    def render_analytics(active_file, config_store, repo_data):
        if not active_file or not repo_data or active_file not in repo_data:
            return [no_update]*4 + ["💡 Feed raw worksheets inside targeted local root repositories."]
        
        df = pd.read_json(io.StringIO(repo_data[active_file]), orient='split')
        df.columns = [str(c).strip().lower() for c in df.columns]
        
        df['status'] = df.get('status', pd.Series(['Pending']*len(df))).replace('', 'Pending').fillna('Pending').astype(str).str.strip()
        df['primary'] = df.get('primary', pd.Series(['Unassigned']*len(df))).replace('', 'Unassigned').fillna('Unassigned').astype(str).str.strip()
        df['projectgroup'] = df.get('projectgroup', pd.Series(['General Portfolio']*len(df))).fillna('General Portfolio').astype(str).str.strip()

        total_items = len(df)
        wip_items = len(df[df['status'].str.upper().str.contains('WIP|TESTING|UNIT|DEVELOPMENT|FUNCTIONAL')])
        
        comp_col = '% completion' if '% completion' in df.columns else 'completion'
        done_items = len(df[df[comp_col].astype(str).str.contains('100%')]) if comp_col in df.columns else 0
        completion_pct = round((done_items / total_items * 100), 1) if total_items > 0 else 0
        
        remark_col = 'remark' if 'remark' in df.columns else 'unassigned'
        has_issue = df[remark_col].fillna('').astype(str).str.lower().str.contains('issue|fail|error|bug|missing') if remark_col in df.columns else pd.Series([False]*len(df))
        ftr_count = len(df[(df[comp_col].astype(str).str.contains('100%')) & (~has_issue)]) if comp_col in df.columns else 0
        ftr_ratio = round((ftr_count / total_items * 100), 1) if total_items > 0 else 100

        ribbon = [
            html.Div([html.P("Total Run Log", style={'margin':0,'fontSize':'0.75rem','color':'#64748b','fontWeight':'600'}), html.H2(f"{total_items} Tasks", style={'color':COLORS['primary'],'margin':'4px 0 0 0','fontWeight':'700','fontSize':'1.35rem'})], style={'flex':1,'padding':'16px','backgroundColor':'#fff', 'borderRadius':'8px','border':f"1px solid {COLORS['border']}"}),
            html.Div([html.P("Active Pipelines", style={'margin':0,'fontSize':'0.75rem','color':'#64748b','fontWeight':'600'}), html.H2(f"{wip_items} Active", style={'color':COLORS['warning'],'margin':'4px 0 0 0','fontWeight':'700','fontSize':'1.35rem'})], style={'flex':1,'padding':'16px','backgroundColor':'#fff', 'borderRadius':'8px','border':f"1px solid {COLORS['border']}"}),
            html.Div([html.P("Aggregate Delivery Rate", style={'margin':0,'fontSize':'0.75rem','color':'#64748b','fontWeight':'600'}), html.H2(f"{completion_pct}%", style={'color':COLORS['accent'],'margin':'4px 0 0 0','fontWeight':'700','fontSize':'1.35rem'})], style={'flex':1,'padding':'16px','backgroundColor':'#fff', 'borderRadius':'8px','border':f"1px solid {COLORS['border']}"}),
            html.Div([html.P("🛡️ Quality Audit Pass", style={'margin':0,'fontSize':'0.75rem','color':'#64748b','fontWeight':'600'}), html.H2(f"{ftr_ratio}%", style={'color':COLORS['secondary'],'margin':'4px 0 0 0','fontWeight':'700','fontSize':'1.35rem'})], style={'flex':1,'padding':'16px','backgroundColor':'#fff', 'borderRadius':'8px','border':f"1px solid {COLORS['border']}"})
        ]
        
        # Matrix Chart
        group_status = df.groupby(['projectgroup', 'status']).size().reset_index(name='Task Volume')
        fig_status = px.bar(
            group_status, x='projectgroup', y='Task Volume', color='status', barmode='group',
            color_discrete_sequence=['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#64748b']
        )
        fig_status.update_layout(
            height=260, margin={'l':10,'r':10,'t':10,'b':10}, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Inter, sans-serif', size=11, color='#64748b'), 
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=9)),
            bargap=0.3, bargroupgap=0.1
        )
        fig_status.update_xaxes(showgrid=False, title="", fixedrange=True)
        fig_status.update_yaxes(gridcolor='#f1f5f9', title="", fixedrange=True)
        
        # Workload Chart
        resource_load = df.groupby(['primary', 'status']).size().reset_index(name='Tasks')
        fig_resource = px.bar(
            resource_load, x='primary', y='Tasks', color='status', barmode='stack',
            color_discrete_sequence=['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#94a3b8']
        )
        fig_resource.update_layout(
            height=260, margin={'l':10,'r':10,'t':10,'b':10}, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Inter, sans-serif', size=11, color='#64748b'),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=9)),
            bargap=0.4
        )
        fig_resource.update_xaxes(showgrid=False, title="", fixedrange=True)
        fig_resource.update_yaxes(gridcolor='#f1f5f9', title="", fixedrange=True)
        
        # Determine Custom Columns
        active_config = config_store.get(active_file) if config_store else [c for c in df.columns if c != 'projectgroup']
        grid_cols = [{"name": str(i).upper() if i != 's.no' else 'S.No', "id": i} for i in df.columns if i in active_config and i != 'projectgroup']
        
        table = dash_table.DataTable(
            data=df.to_dict('records'), 
            columns=grid_cols,
            style_cell={
                'textAlign': 'left', 'padding': '12px 14px', 'fontFamily': 'Inter, sans-serif', 'fontSize': '0.82rem', 'color': COLORS['text_main'],
                'minWidth': '140px', 'width': '180px', 'maxWidth': '300px',
                'overflow': 'hidden', 'textOverflow': 'ellipsis', 'whiteSpace': 'nowrap'
            },
            style_header={'backgroundColor': COLORS['primary'], 'color': 'white', 'fontWeight': '500', 'border': 'none'},
            style_data={'borderBottom': '1px solid #f1f5f9'},
            style_table={'overflowX': 'auto', 'width': '100%', 'minWidth': '100%'},
            tooltip_data=[{column: {'value': str(value), 'type': 'markdown'} for column, value in row.items()} for row in df.to_dict('records')],
            tooltip_duration=None,
            page_size=30  
        )
        return ribbon, fig_status, fig_resource, table, f"Instance: {active_file}"

    # 6. CO-PILOT CHAT DIAGNOSTIC VERSION
    @app.callback(
        Output('chat-history-stream', 'children'), 
        Output('chat-user-input', 'value'),
        Input('chat-user-input', 'n_submit'), 
        Input('send-chat-btn', 'n_clicks'), 
        Input('active-sheet-dropdown', 'value'),
        State('chat-user-input', 'value'), 
        State('chat-history-repository', 'data'), 
        State('file-repository-store', 'data'),
        prevent_initial_call=True
    )
    def process_chat_operation(n_submit, n_clicks, active_file, user_raw_text, chat_repo, data_repo):
        print(f"\n[DEBUG] Chat Callback Triggered! Active File: {active_file}")
        if not active_file: 
            return [html.Div("🤖 Select workspace sheet...", style={'color':'#64748b'})], no_update
        
        ctx_id = ctx.triggered_id
        print(f"[DEBUG] Triggered by Component ID: {ctx_id}")
        chat_repo = chat_repo or {}
        
        if active_file not in chat_repo: 
            try:
                chat_repo[active_file] = db.load_chat_history(active_file)
                print(f"[DEBUG] Successfully loaded history from DB. Messages found: {len(chat_repo[active_file])}")
            except Exception as e:
                print(f"[DEBUG] ❌ Database Load Error: {e}")
                chat_repo[active_file] = []
            
        if ctx_id == 'active-sheet-dropdown':
            return [html.Div(m['content'], style={'padding':'8px 12px','borderRadius':'8px','fontSize':'0.8rem','maxWidth':'85%','backgroundColor': COLORS['secondary'] if m['role']=='user' else '#e2e8f0','color':'white' if m['role']=='user' else COLORS['primary'],'alignSelf':'flex-end' if m['role']=='user' else 'flex-start','marginBottom':'6px'}) for m in chat_repo[active_file]], no_update

        if ctx_id in ['chat-user-input', 'send-chat-btn']:
            if not user_raw_text or user_raw_text.strip() == "":
                print("[DEBUG] User input was completely empty. Aborting.")
                return no_update, no_update
                
            clean_input = user_raw_text.strip()
            print(f"[DEBUG] Received User Input text: '{clean_input}'")
            
            try:
                db.save_chat_message(active_file, "user", clean_input)
                print("[DEBUG] User message saved to SQLite database successfully.")
            except Exception as e:
                print(f"[DEBUG] ❌ Database Save Error: {e}")
                
            chat_repo[active_file].append({"role": "user", "content": clean_input})
            
            context_string = ""
            if data_repo and active_file in data_repo:
                try:
                    context_string = pd.read_json(io.StringIO(data_repo[active_file]), orient='split').to_string(index=False)
                    print(f"[DEBUG] CSV Context converted successfully. Total context length: {len(context_string)} chars.")
                except Exception as e:
                    print(f"[DEBUG] ❌ DataFrame Context Extraction Error: {e}")
            else:
                print("[DEBUG] ⚠️ WARNING: No data context found for this file key in memory stores.")
            
            import datetime
            today = datetime.date.today()
            past_7_days = [(today - datetime.timedelta(days=i)).strftime("%d/%m") for i in range(7)]
            days_string = ", ".join(past_7_days)
            
            structured_prompt = (
                f"SYSTEM INSTRUCTION:\n"
                f"You are an expert Project Management AI Assistant. The current system date is {today.strftime('%B %d, %Y')}.\n\n"
                f"Core Remarks Log Pattern: The 'remark' column contains sequential timeline logs structured exactly as: "
                f"dd/mm \"content\" dd/mm \"content\", dd/mm \"content\". Read them left to right.\n\n"
                f"Core Trend Filtering Pattern: When asked to analyze a 7-day trend, scan all rows and evaluate logs "
                f"matching the exact calendar dates for the past 7 days, which are: [{days_string}].\n\n"
                f"DATASET CONTEXT:\n{context_string}\n\n"
                f"USER QUESTION: {clean_input}"
            )
            
            print("[DEBUG] Sending structured prompt to Groq Cloud Engine via ai_engine.py...")
            try: 
                from ai_engine import query_ollama_context
                reply = query_ollama_context(structured_prompt, context_data="")
                print(f"[DEBUG] Groq responded successfully! Reply snippet: {reply[:60]}...")
            except Exception as e: 
                print(f"[DEBUG] ❌ Critical failure during Groq API execution: {e}")
                reply = "⚠️ Connection Interrupted or local processing engine encountered an unexpected error."
                
            try:
                db.save_chat_message(active_file, "assistant", reply)
                print("[DEBUG] Assistant response logged to database.")
            except Exception as e:
                print(f"[DEBUG] ❌ Database Save Assistant Error: {e}")
                
            chat_repo[active_file].append({"role": "assistant", "content": reply})
            
            return [html.Div(m['content'], style={'padding':'8px 12px','borderRadius':'8px','fontSize':'0.8rem','maxWidth':'85%','backgroundColor': COLORS['secondary'] if m['role']=='user' else '#e2e8f0','color':'white' if m['role']=='user' else COLORS['primary'],'alignSelf':'flex-end' if m['role']=='user' else 'flex-start','marginBottom':'6px'}) for m in chat_repo[active_file]], ""
            
        return no_update, no_update
    # 7. CHAT WINDOW VISIBILITY WIDGET
    @app.callback(
        Output('chat-panel-window', 'style'), Output('chat-circle-token', 'style'),
        Input('minimize-btn', 'n_clicks'), Input('chat-circle-token', 'n_clicks'), State('chat-panel-window', 'style'), State('chat-circle-token', 'style'),
        prevent_initial_call=True
    )
    def manage_minimized_tokens(min_clicks, open_clicks, panel_style, token_style):
        trigger_id = ctx.triggered_id
        panel_style, token_style = panel_style or {}, token_style or {}
        if trigger_id == 'minimize-btn': panel_style['display'], token_style['display'] = 'none', 'flex'
        elif trigger_id == 'chat-circle-token': panel_style['display'], token_style['display'] = 'flex', 'none'
        return panel_style, token_style
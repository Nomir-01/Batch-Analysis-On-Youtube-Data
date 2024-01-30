import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objects as go
import dash_bootstrap_components as dbc

# Use Bootstrap CSS for better styling
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Custom function to parse 'publish_time' column
def custom_date_parser(date_str):
    try:
        return pd.to_datetime(date_str, format='%Y-%m-%dT%H:%M:%S.%fZ', utc=True).strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        print(f"Error parsing date: {date_str}")
        return pd.NaT  # Return NaT for invalid dates

# Load your CSV files with custom date parsing
file_names = ["preprocessed_table_yt_table_ca", "preprocessed_table_yt_table_de", "preprocessed_table_yt_table_fr", "preprocessed_table_yt_table_gb", "preprocessed_table_yt_table_in", "preprocessed_table_yt_table_jp", "preprocessed_table_yt_table_kr", "preprocessed_table_yt_table_mx", "preprocessed_table_yt_table_ru", "preprocessed_table_yt_table_us"]

dfs = {name: pd.read_csv(f"{name}.csv", encoding='latin1', parse_dates=['publish_time'], date_parser=custom_date_parser) for name in file_names}

# Define color scheme
black_color = '#1E1E1E'  # Dark gray
red_color = '#FF4136'    # Red
white_color = '#FFFFFF'  # White

# Define the layout of the dashboard
app.layout = dbc.Container(
    [
        html.H1("YouTube Analytics Dashboard", className="my-4 text-center", style={'color': white_color}),

        dbc.Row(
            [
                dbc.Col(
                    dcc.Dropdown(
                        id='country-dropdown',
                        options=[{'label': name, 'value': name} for name in file_names],
                        value='preprocessed_table_yt_table_us',
                        style={'width': '100%'}
                    ),
                    width=12,
                    className="mb-4"
                ),
            ]
        ),

        dbc.Row(
            [
                dbc.Col(dcc.Graph(id='views-bar-chart'), width=12),
                dbc.Col(dcc.Graph(id='likes-dislikes-pie-chart'), width=6),
                dbc.Col(
                    dash_table.DataTable(
                        id='video-table',
                        columns=[
                            {'name': 'Video ID', 'id': 'video_id', 'presentation': 'markdown'},
                            {'name': 'Title', 'id': 'title', 'presentation': 'markdown'},
                            {'name': 'Channel Title', 'id': 'channel_title', 'presentation': 'markdown'},
                        ],
                        style_table={'height': '400px', 'overflowY': 'auto'},
                        row_selectable='single',
                        selected_rows=[0],
                    ),
                    width=6,
                ),
            ]
        ),

        dbc.Row(
            [
                dbc.Col(html.Div(id='selected-video-info', style={'color': white_color}), width=12),
            ]
        ),
    ],
    fluid=True,
    style={'background-color': black_color, 'padding': '20px'}
)

# Define callback to update charts and table based on dropdown selection
@app.callback(
    [Output('views-bar-chart', 'figure'),
     Output('likes-dislikes-pie-chart', 'figure'),
     Output('video-table', 'data'),
     Output('selected-video-info', 'children')],
    [Input('country-dropdown', 'value'),
     Input('video-table', 'selected_rows')]
)
def update_charts_and_table(selected_country, selected_rows):
    df = dfs[selected_country]

    # Check if the selected rows list is not empty
    if selected_rows:
        selected_video = df.iloc[selected_rows[0]]

        # Bar chart for views
        views_bar_chart = go.Figure()
        views_bar_chart.add_trace(go.Bar(x=df['trending_date'], y=df['views'], name='Views', marker_color=red_color))
        views_bar_chart.update_layout(title='Views Over Time', paper_bgcolor=black_color, plot_bgcolor=black_color,
                                      font_color=white_color)

        # Pie chart for likes and dislikes of the selected video
        likes_dislikes_pie_chart_selected = go.Figure()
        likes_dislikes_pie_chart_selected.add_trace(go.Pie(labels=['Likes', 'Dislikes'],
                                                           values=[selected_video['likes'], selected_video['dislikes']],
                                                           marker=dict(colors=[red_color, white_color])))
        likes_dislikes_pie_chart_selected.update_layout(title='Likes vs Dislikes (Selected Video)',
                                                       paper_bgcolor=black_color, font_color=white_color)

        # Calculate total likes and dislikes for the whole region
        total_likes = df['likes'].sum()
        total_dislikes = df['dislikes'].sum()

        # Pie chart for total likes and dislikes of the region
        likes_dislikes_pie_chart_total = go.Figure()
        likes_dislikes_pie_chart_total.add_trace(go.Pie(labels=['Likes', 'Dislikes'],
                                                        values=[total_likes, total_dislikes],
                                                        marker=dict(colors=[red_color, white_color])))
        likes_dislikes_pie_chart_total.update_layout(title='Total Likes vs Dislikes (Region)', paper_bgcolor=black_color,
                                                    font_color=white_color)

        # Data for DataTable
        table_data = df[['video_id', 'title', 'channel_title']].to_dict('records')

        # Selected video information
        selected_video_info = html.Div([
            html.H4(f"Selected Video Information", style={'color': white_color}),
            html.Table([
                html.Tr([html.Th(col, style={'color': white_color}), html.Td(selected_video[col])]) for col in df.columns
                if col not in ['comments_disabled', 'ratings_disabled', 'video_error_or_removed', 'video_id',
                               'category_id', 'tags', 'description']
            ]),
            dcc.Graph(
                id='selected-video-stats',
                figure=likes_dislikes_pie_chart_selected,
            ),
        ])

        return views_bar_chart, likes_dislikes_pie_chart_total, table_data, selected_video_info
    else:
        # If no video is selected, return no_update for all outputs
        return go.Figure(), go.Figure(), dash.no_update, dash.no_update

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)

import gradio as gr
from utils.data_loader import fetch_and_save_chess_data
from utils.game_analysis import (
    analyze_games,
    generate_monthly_report,
    calculate_average_and_median_games,
    analyze_streaks,
    analyze_sequences,
    format_duration
)
from datetime import datetime
import os
import json

import matplotlib.pyplot as plt
import io
from PIL import Image
import plotly.graph_objects as go
import pandas as pd
import csv

logged_in_user = None  # Global state to store the logged-in user


# Define your user credentials
auth_users = [
    ("Sacha", "SachaIsTheBest"),
    ("Florian", "FlorianIsTheBest"),
    ("Lucas", "Slevin"),
    ("Gael", "Kalel"),
    ("BlueNote", "MamaLinda")
]



DATA_FOLDER = 'data/'
LOG_FILE = 'user_logs.csv'

# Initialize log file if it doesn't exist
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, 'w', newline='') as log_file:
        writer = csv.writer(log_file)
        writer.writerow(["Username", "Timestamp", "Action", "Query"])

def log_user_action(username, action, query=""):
    """Log user actions to a CSV file."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILE, 'a', newline='') as log_file:
        writer = csv.writer(log_file)
        writer.writerow([username, timestamp, action, query])

def get_monthly_report(username, logged_in_user):
    """Fetch data for a given username, reuse existing data if available, and generate a monthly report."""
    current_date = datetime.now().strftime('%Y-%m-%d')
    filename = os.path.join(DATA_FOLDER, f"{username}_{current_date}.json")

    log_user_action(logged_in_user, "Search", username)

    if os.path.exists(filename):
        print(f"Using existing data file: {filename}")
        with open(filename, 'r') as file:
            games = json.load(file)
    else:
        games = fetch_and_save_chess_data(username, filename)
        if not games:
            return "No data found for the specified username."
        
    games_sorted = sorted(games, key=lambda x: x.get('end_time'))

    # Perform monthly analysis
    games_per_month, stats_per_month, total_games, total_wins, total_losses, total_timeouts, total_months_played = analyze_games(games, username)
    report_df = generate_monthly_report(games_per_month, stats_per_month)

    # Calculate average and median games per day
    average_games, median_games = calculate_average_and_median_games(games)
    
    # Calculate streak probabilities
    win_prob, loss_prob = analyze_streaks(games_sorted, username)

    # Calculate sequence probabilities
    win_after_wl_prob, win_after_lw_prob = analyze_sequences(games_sorted, username)
    
    # Format the duration of months played
    formatted_duration = format_duration(total_months_played)


    # Prepare the text summary
    summary_text = (
        f"Total duration played: {formatted_duration}\n"
        f"Total games played: {total_games}\n"
        f"Total wins: {total_wins}\n"
        f"Total losses: {total_losses}\n"
        f"Total timeouts: {total_timeouts}\n"
        f"Average games played per day: {average_games:.2f}\n"
        f"Median games played per day: {median_games}\n"
        f"Probability of winning the next game after a win in the same hour: {win_prob:.2f}%\n"
        f"Probability of losing the next game after a loss in the same hour: {loss_prob:.2f}%\n"
        f"Probability of winning the next game after a 'win-loss' sequence in the same hour: {win_after_wl_prob:.2f}%\n"
        f"Probability of winning the next game after a 'loss-win' sequence in the same hour: {win_after_lw_prob:.2f}%"
    )
    
    stacked_bar_img = generate_stacked_bar_chart(report_df)

    return report_df, summary_text, stacked_bar_img




def generate_stacked_bar_chart(report_df):
    """Generate an interactive stacked bar chart with wins, losses, and a line plot for timeouts using Plotly."""
    # Extract data
    months = pd.to_datetime(report_df['Month']).dt.strftime('%b, %Y')
    wins = report_df['Wins']
    losses = report_df['Losses']
    timeouts = report_df['Timeout Rate (%)']
    total_games = report_df['Games Played']

    # Create the figure
    fig = go.Figure()

    # Add wins bars
    fig.add_trace(go.Bar(
        x=months,
        y=wins,
        name='Wins',
        marker=dict(color='#1f77b4'),
        hovertemplate='<b>Wins</b>: %{y}<extra></extra>'
    ))

    # Add losses bars stacked on top of wins
    fig.add_trace(go.Bar(
        x=months,
        y=losses,
        name='Losses',
        marker=dict(color='#ff7f0e'),
        hovertemplate='<b>Losses</b>: %{y}<extra></extra>'
    ))

    # Add timeouts as a line plot
    fig.add_trace(go.Scatter(
        x=months,
        y=timeouts,
        mode='lines+markers',
        name='Timeouts',
        line=dict(color='#da5bac', width=2),
        hovertemplate='<b>Timeouts</b>: %{y:.1f}%<extra></extra>'
    ))

    # Add rotated annotations for total games on top of each bar
    for i, total in enumerate(total_games):
        fig.add_annotation(
            x=months[i],
            y=total + 5,
            text=str(int(total)),
            showarrow=False,
            font=dict(size=12, color='white'),
            align='center',
            textangle=-45  # Rotate the text label by -45 degrees
        )

    # Update layout for stacked bars and hover information
    fig.update_layout(
        barmode='stack',
        title='Monthly Win/Loss Stacked Bar Chart with Total Games and Timeouts',
        xaxis_title='Month',
        yaxis_title='Count',
        legend_title='Legend',
        hovermode='x unified',
        template='plotly_dark'
    )

    # Return the Plotly figure
    return fig

logged_in_user_state = gr.State()

# Authentication callback function
def auth_callback(username, password):
    global logged_in_user
    valid_users = dict(auth_users)
    if username in valid_users and valid_users[username] == password:
        log_user_action(username, "Login")
        logged_in_user = username  # Store the logged-in user globally
        return True
    return False




def get_report_with_user(username):
    global logged_in_user
    return get_monthly_report(username, logged_in_user or "Unknown")







# Custom layout using gr.Blocks with CSS
with gr.Blocks(css="style.css", theme=gr.themes.Soft()) as app:
    gr.Markdown("# Chess Analysis App")
    username_input = gr.Textbox(label="Chess.com Username", placeholder="Enter Chess.com username")
    submit_button = gr.Button("Submit")

    # Define outputs
    output_data = gr.Dataframe(headers=["Month", "Games Played", "Wins", "Losses", "Win Rate (%)", "Loss Rate (%)", "Timeout Rate (%)"])
    summary_text = gr.Textbox(label="Summary", interactive=False)
    # stacked_bar_img = gr.Image(label="Monthly Stacked Bar Chart with Timeouts")
    stacked_bar_img = gr.Plot(label="Monthly Stacked Bar Chart with Timeouts")


    # Link the click event
    submit_button.click(
        fn=get_report_with_user,
        inputs=[username_input],
        outputs=[output_data, summary_text, stacked_bar_img]
    )



app.launch(auth=auth_users, share=True)




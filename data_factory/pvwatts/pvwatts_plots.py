import pandas as pd
import plotly.graph_objects as go
from plotly.offline import plot
from plotly.subplots import make_subplots
import plotly.express as px

def chart(fig):
    """Helper function to display chart"""
    fig.update_layout(template="plotly_dark", margin=dict(l=40, r=20, t=50, b=40))
    return plot(fig, output_type="div", include_plotlyjs=False)

# ================================================================
#   POWER GENERATION ANALYSIS
# ================================================================

def power_generation_timeseries(df):
    """Time series of AC and DC power generation"""
    daily_power = df.resample('D').mean()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=daily_power.index, y=daily_power['ac_power'], 
                            name='AC Power', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=daily_power.index, y=daily_power['dc_power'], 
                            name='DC Power', line=dict(color='red')))
    
    fig.update_layout(
        title="Daily Average Power Generation",
        xaxis_title="Date",
        yaxis_title="Power (kW)",
        hovermode='x unified'
    )
    return chart(fig)

def power_heatmap(df, power_type='ac_power'):
    """Heatmap of power generation by hour and day of year"""
    df_heatmap = df.copy()
    df_heatmap['day_of_year'] = df_heatmap['day_of_year']
    df_heatmap['hour'] = df_heatmap['hour']
    
    pivot = df_heatmap.pivot_table(index='day_of_year', columns='hour', 
                                  values=power_type, aggfunc='mean')
    
    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=pivot.columns,
        y=pivot.index,
        colorscale='Viridis',
        colorbar=dict(title='Power (kW)')
    ))
    
    power_label = 'AC Power' if power_type == 'ac_power' else 'DC Power'
    fig.update_layout(
        title=f"{power_label} Heatmap (Day of Year vs Hour)",
        xaxis_title="Hour of Day",
        yaxis_title="Day of Year"
    )
    return chart(fig)

def monthly_average_power(df):
    """Monthly average AC and DC power"""
    monthly_stats = df.groupby('month').agg({
        'ac_power': 'mean',
        'dc_power': 'mean'
    }).round(2).reset_index()
    
    fig = go.Figure()
    fig.add_trace(go.Bar(x=monthly_stats['month'], y=monthly_stats['ac_power'], 
                        name='AC Average', marker_color='blue'))
    fig.add_trace(go.Bar(x=monthly_stats['month'], y=monthly_stats['dc_power'], 
                        name='DC Average', marker_color='red'))
    
    fig.update_layout(
        title="Monthly Average Power",
        xaxis_title="Month",
        yaxis_title="Power (kW)",
        barmode='group'
    )
    return chart(fig)

def monthly_maximum_power(df):
    """Monthly maximum AC and DC power"""
    monthly_stats = df.groupby('month').agg({
        'ac_power': 'max',
        'dc_power': 'max'
    }).round(2).reset_index()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=monthly_stats['month'], y=monthly_stats['ac_power'], 
                           name='AC Max', line=dict(color='red', width=3)))
    fig.add_trace(go.Scatter(x=monthly_stats['month'], y=monthly_stats['dc_power'], 
                           name='DC Max', line=dict(color='orange', width=3)))
    
    fig.update_layout(
        title="Monthly Maximum Power",
        xaxis_title="Month",
        yaxis_title="Power (kW)"
    )
    return chart(fig)

def monthly_total_energy(df):
    """Monthly total energy production"""
    monthly_stats = df.groupby('month').agg({
        'ac_power': 'sum',
        'dc_power': 'sum'
    }).round(2).reset_index()
    
    fig = go.Figure()
    fig.add_trace(go.Bar(x=monthly_stats['month'], y=monthly_stats['ac_power'], 
                        name='AC Total Energy', marker_color='green'))
    
    fig.update_layout(
        title="Monthly Total Energy Production",
        xaxis_title="Month",
        yaxis_title="Energy (kWh)"
    )
    return chart(fig)

def monthly_efficiency(df):
    """Monthly system efficiency (AC/DC ratio)"""
    monthly_stats = df.groupby('month').agg({
        'ac_power': 'sum',
        'dc_power': 'sum'
    }).round(2).reset_index()
    
    monthly_stats['Efficiency'] = (monthly_stats['ac_power'] / monthly_stats['dc_power'] * 100).round(2)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=monthly_stats['month'], y=monthly_stats['Efficiency'], 
                           name='Efficiency %', line=dict(color='green', width=3),
                           mode='lines+markers'))
    
    fig.update_layout(
        title="Monthly System Efficiency",
        xaxis_title="Month",
        yaxis_title="Efficiency (%)"
    )
    return chart(fig)

# ================================================================
#   IRRADIANCE ANALYSIS
# ================================================================

def irradiance_daily_pattern(df):
    """Daily irradiance patterns by month"""
    # Filter only daylight hours (6 AM to 6 PM)
    daylight_hours = df[(df['hour'] >= 6) & (df['hour'] <= 18)]
    
    monthly_hourly = daylight_hours.groupby(['month', 'hour']).agg({
        'poa_irradiance': 'mean'
    }).reset_index()
    
    fig = px.line(monthly_hourly, x='hour', y='poa_irradiance', color='month',
                 title="Average Daily Irradiance Patterns by Month")
    fig.update_layout(
        xaxis_title="Hour of Day",
        yaxis_title="POA Irradiance (W/m²)"
    )
    return chart(fig)

def irradiance_vs_power_scatter(df):
    """Scatter plot of irradiance vs power generation"""
    # Filter non-zero irradiance points
    daylight_data = df[df['poa_irradiance'] > 10]
    
    fig = make_subplots(rows=1, cols=2, 
                       subplot_titles=('POA vs AC Power', 'POA vs DC Power'))
    
    fig.add_trace(go.Scatter(x=daylight_data['poa_irradiance'], 
                            y=daylight_data['ac_power'], 
                            mode='markers', opacity=0.3, name='AC Power'),
                 row=1, col=1)
    
    fig.add_trace(go.Scatter(x=daylight_data['poa_irradiance'], 
                            y=daylight_data['dc_power'], 
                            mode='markers', opacity=0.3, name='DC Power',
                            marker=dict(color='red')),
                 row=1, col=2)
    
    fig.update_layout(title_text="Irradiance vs Power Generation")
    fig.update_xaxes(title_text="POA Irradiance (W/m²)", row=1, col=1)
    fig.update_xaxes(title_text="POA Irradiance (W/m²)", row=1, col=2)
    fig.update_yaxes(title_text="AC Power (kW)", row=1, col=1)
    fig.update_yaxes(title_text="DC Power (kW)", row=1, col=2)
    
    return chart(fig)

# ================================================================
#   SYSTEM PERFORMANCE ANALYSIS
# ================================================================

def efficiency_distribution(df):
    """Distribution of system efficiency"""
    production_data = df[df['dc_power'] > 0.1].copy()
    production_data['efficiency'] = (production_data['ac_power'] / production_data['dc_power'] * 100).clip(0, 100)
    
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=production_data['efficiency'], nbinsx=50,
                             name='Efficiency Distribution'))
    
    fig.update_layout(
        title="System Efficiency Distribution",
        xaxis_title="Efficiency (%)",
        yaxis_title="Count"
    )
    return chart(fig)

def efficiency_by_month(df):
    """Average efficiency by month"""
    production_data = df[df['dc_power'] > 0.1].copy()
    production_data['efficiency'] = (production_data['ac_power'] / production_data['dc_power'] * 100).clip(0, 100)
    
    monthly_eff = production_data.groupby('month')['efficiency'].mean().reset_index()
    
    fig = go.Figure()
    fig.add_trace(go.Bar(x=monthly_eff['month'], y=monthly_eff['efficiency'],
                        name='Monthly Avg Efficiency', marker_color='purple'))
    
    fig.update_layout(
        title="Average Efficiency by Month",
        xaxis_title="Month",
        yaxis_title="Efficiency (%)"
    )
    return chart(fig)

def efficiency_vs_irradiance(df):
    """Efficiency vs irradiance scatter plot"""
    production_data = df[df['dc_power'] > 0.1].copy()
    production_data['efficiency'] = (production_data['ac_power'] / production_data['dc_power'] * 100).clip(0, 100)
    
    sampled_data = production_data.sample(n=min(1000, len(production_data)))
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=sampled_data['poa_irradiance'], 
                           y=sampled_data['efficiency'], mode='markers',
                           opacity=0.5, name='Efficiency'))
    
    fig.update_layout(
        title="Efficiency vs Irradiance",
        xaxis_title="POA Irradiance (W/m²)",
        yaxis_title="Efficiency (%)"
    )
    return chart(fig)

def efficiency_by_hour(df):
    """Average efficiency by hour of day"""
    production_data = df[df['dc_power'] > 0.1].copy()
    production_data['efficiency'] = (production_data['ac_power'] / production_data['dc_power'] * 100).clip(0, 100)
    
    hourly_eff = production_data.groupby('hour')['efficiency'].mean().reset_index()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hourly_eff['hour'], y=hourly_eff['efficiency'],
                           name='Hourly Efficiency', line=dict(color='orange', width=3),
                           mode='lines+markers'))
    
    fig.update_layout(
        title="Average Efficiency by Hour of Day",
        xaxis_title="Hour of Day",
        yaxis_title="Efficiency (%)"
    )
    return chart(fig)

# ================================================================
#   SEASONAL ANALYSIS
# ================================================================

def seasonal_average_power(df):
    """Average power by season"""
    season_map = {12: 'Winter', 1: 'Winter', 2: 'Winter',
                  3: 'Spring', 4: 'Spring', 5: 'Spring',
                  6: 'Summer', 7: 'Summer', 8: 'Summer',
                  9: 'Fall', 10: 'Fall', 11: 'Fall'}
    
    df_season = df.copy()
    df_season['season'] = df_season['month'].map(season_map)
    
    seasonal_stats = df_season.groupby('season').agg({
        'ac_power': 'mean',
        'dc_power': 'mean'
    }).round(2)
    
    # Reorder seasons
    season_order = ['Winter', 'Spring', 'Summer', 'Fall']
    seasonal_stats = seasonal_stats.reindex(season_order)
    
    fig = go.Figure()
    fig.add_trace(go.Bar(x=seasonal_stats.index, 
                        y=seasonal_stats['ac_power'],
                        name='AC Power', marker_color='blue'))
    fig.add_trace(go.Bar(x=seasonal_stats.index, 
                        y=seasonal_stats['dc_power'],
                        name='DC Power', marker_color='red'))
    
    fig.update_layout(
        title="Average Power by Season",
        xaxis_title="Season",
        yaxis_title="Power (kW)",
        barmode='group'
    )
    return chart(fig)

def seasonal_total_energy(df):
    """Total energy by season"""
    season_map = {12: 'Winter', 1: 'Winter', 2: 'Winter',
                  3: 'Spring', 4: 'Spring', 5: 'Spring',
                  6: 'Summer', 7: 'Summer', 8: 'Summer',
                  9: 'Fall', 10: 'Fall', 11: 'Fall'}
    
    df_season = df.copy()
    df_season['season'] = df_season['month'].map(season_map)
    
    seasonal_stats = df_season.groupby('season').agg({
        'ac_power': 'sum'
    }).round(2)
    
    # Reorder seasons
    season_order = ['Winter', 'Spring', 'Summer', 'Fall']
    seasonal_stats = seasonal_stats.reindex(season_order)
    
    fig = go.Figure()
    fig.add_trace(go.Bar(x=seasonal_stats.index, 
                        y=seasonal_stats['ac_power'],
                        name='AC Energy', marker_color='green'))
    
    fig.update_layout(
        title="Total Energy by Season",
        xaxis_title="Season",
        yaxis_title="Energy (kWh)"
    )
    return chart(fig)

def seasonal_maximum_power(df):
    """Maximum power by season"""
    season_map = {12: 'Winter', 1: 'Winter', 2: 'Winter',
                  3: 'Spring', 4: 'Spring', 5: 'Spring',
                  6: 'Summer', 7: 'Summer', 8: 'Summer',
                  9: 'Fall', 10: 'Fall', 11: 'Fall'}
    
    df_season = df.copy()
    df_season['season'] = df_season['month'].map(season_map)
    
    seasonal_stats = df_season.groupby('season').agg({
        'ac_power': 'max',
        'dc_power': 'max'
    }).round(2)
    
    # Reorder seasons
    season_order = ['Winter', 'Spring', 'Summer', 'Fall']
    seasonal_stats = seasonal_stats.reindex(season_order)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=seasonal_stats.index, 
                           y=seasonal_stats['ac_power'],
                           name='AC Max', line=dict(color='red', width=3)))
    fig.add_trace(go.Scatter(x=seasonal_stats.index, 
                           y=seasonal_stats['dc_power'],
                           name='DC Max', line=dict(color='orange', width=3)))
    
    fig.update_layout(
        title="Maximum Power by Season",
        xaxis_title="Season",
        yaxis_title="Power (kW)"
    )
    return chart(fig)

def seasonal_irradiance(df):
    """Average irradiance by season"""
    season_map = {12: 'Winter', 1: 'Winter', 2: 'Winter',
                  3: 'Spring', 4: 'Spring', 5: 'Spring',
                  6: 'Summer', 7: 'Summer', 8: 'Summer',
                  9: 'Fall', 10: 'Fall', 11: 'Fall'}
    
    df_season = df.copy()
    df_season['season'] = df_season['month'].map(season_map)
    
    seasonal_stats = df_season.groupby('season').agg({
        'poa_irradiance': 'mean'
    }).round(2)
    
    # Reorder seasons
    season_order = ['Winter', 'Spring', 'Summer', 'Fall']
    seasonal_stats = seasonal_stats.reindex(season_order)
    
    fig = go.Figure()
    fig.add_trace(go.Bar(x=seasonal_stats.index, 
                        y=seasonal_stats['poa_irradiance'],
                        name='POA Irradiance', marker_color='yellow'))
    
    fig.update_layout(
        title="Average Irradiance by Season",
        xaxis_title="Season",
        yaxis_title="Irradiance (W/m²)"
    )
    return chart(fig)

# ================================================================
#   MAIN EXECUTION FUNCTION
# ================================================================

def generate_all_analytics(df):
    """Generate all analytics charts"""
    # Ensure timestamp is datetime and set as index
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')
    
    charts = {}
    
    # Generate all charts
    charts['power_timeseries'] = power_generation_timeseries(df)
    charts['ac_power_heatmap'] = power_heatmap(df, 'ac_power')
    charts['dc_power_heatmap'] = power_heatmap(df, 'dc_power')
    
    # Monthly analysis charts
    charts['monthly_average_power'] = monthly_average_power(df)
    charts['monthly_maximum_power'] = monthly_maximum_power(df)
    charts['monthly_total_energy'] = monthly_total_energy(df)
    charts['monthly_efficiency'] = monthly_efficiency(df)
    
    # Irradiance analysis charts
    charts['irradiance_patterns'] = irradiance_daily_pattern(df)
    charts['irradiance_vs_power'] = irradiance_vs_power_scatter(df)
    
    # Efficiency analysis charts
    charts['efficiency_distribution'] = efficiency_distribution(df)
    charts['efficiency_by_month'] = efficiency_by_month(df)
    charts['efficiency_vs_irradiance'] = efficiency_vs_irradiance(df)
    charts['efficiency_by_hour'] = efficiency_by_hour(df)
    
    # Seasonal analysis charts
    charts['seasonal_average_power'] = seasonal_average_power(df)
    charts['seasonal_total_energy'] = seasonal_total_energy(df)
    charts['seasonal_maximum_power'] = seasonal_maximum_power(df)
    charts['seasonal_irradiance'] = seasonal_irradiance(df)
    
    return charts
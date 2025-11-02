import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

def create_solar_energy_plots(raw_data, insights):
    """Create comprehensive solar energy plots"""
    solar_data = raw_data[raw_data['parameter'] == 'ALLSKY_SFC_SW_DWN'].copy()
    solar_data['date'] = pd.to_datetime(solar_data['date'])
    solar_data['year'] = solar_data['date'].dt.year
    solar_data['month'] = solar_data['date'].dt.month
    
    # Daily time series
    fig_daily = go.Figure()
    fig_daily.add_trace(go.Scatter(
        x=solar_data['date'], 
        y=solar_data['value'],
        mode='lines',
        name='Daily Solar Radiation',
        line=dict(color='orange', width=1),
        opacity=0.7
    ))
    
    # 30-day moving average
    solar_data = solar_data.sort_values('date')
    solar_data['moving_avg_30'] = solar_data['value'].rolling(window=30, center=True).mean()
    fig_daily.add_trace(go.Scatter(
        x=solar_data['date'], 
        y=solar_data['moving_avg_30'],
        mode='lines',
        name='30-day Moving Average',
        line=dict(color='red', width=2)
    ))
    
    fig_daily.update_layout(
        title='Solar Radiation Time Series (ALLSKY_SFC_SW_DWN)',
        xaxis_title='Date',
        yaxis_title='Solar Radiation (kW-hr/m²/day)',
        template='plotly_white'
    )
    
    # Monthly climatology
    monthly_clima = insights['ALLSKY_SFC_SW_DWN']['seasonal_climatology_monthly']
    months = list(monthly_clima.keys())
    values = list(monthly_clima.values())
    
    fig_monthly = go.Figure()
    fig_monthly.add_trace(go.Bar(
        x=months,
        y=values,
        marker_color='gold',
        name='Monthly Average'
    ))
    
    fig_monthly.update_layout(
        title='Monthly Solar Radiation Climatology',
        xaxis_title='Month',
        yaxis_title='Solar Radiation (kW-hr/m²/day)',
        xaxis=dict(tickmode='array', tickvals=list(range(1, 13)), 
                  ticktext=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                           'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']),
        template='plotly_white'
    )
    
    # Annual trends
    annual_avg = solar_data.groupby('year')['value'].mean().reset_index()
    
    fig_annual = go.Figure()
    fig_annual.add_trace(go.Scatter(
        x=annual_avg['year'],
        y=annual_avg['value'],
        mode='lines+markers',
        name='Annual Average',
        line=dict(color='darkorange', width=3)
    ))
    
    fig_annual.update_layout(
        title='Annual Solar Radiation Trends',
        xaxis_title='Year',
        yaxis_title='Average Solar Radiation (kW-hr/m²/day)',
        template='plotly_white'
    )
    
    return fig_daily, fig_monthly, fig_annual

def create_temperature_plots(raw_data, insights):
    """Create comprehensive temperature plots"""
    # Extract temperature data
    temp_data = raw_data[raw_data['parameter'].isin(['T2M', 'T2M_MAX', 'T2M_MIN'])].copy()
    temp_data['date'] = pd.to_datetime(temp_data['date'])
    
    # Pivot to get all temperature metrics in columns
    temp_pivot = temp_data.pivot_table(
        index='date', 
        columns='parameter', 
        values='value'
    ).reset_index()
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'Daily Temperature Time Series', 
            'Monthly Temperature Climatology',
            'Annual Temperature Trends',
            'Temperature Distribution'
        ),
        specs=[[{"colspan": 2}, None], [{}, {}]]
    )
    
    # Daily time series
    fig.add_trace(go.Scatter(
        x=temp_pivot['date'], y=temp_pivot['T2M'],
        mode='lines', name='Avg Temp', line=dict(color='blue', width=1)
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=temp_pivot['date'], y=temp_pivot['T2M_MAX'],
        mode='lines', name='Max Temp', line=dict(color='red', width=1)
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=temp_pivot['date'], y=temp_pivot['T2M_MIN'],
        mode='lines', name='Min Temp', line=dict(color='lightblue', width=1)
    ), row=1, col=1)
    
    # Monthly climatology
    t2m_clima = insights['T2M']['seasonal_climatology_monthly']
    t2m_max_clima = insights['T2M_MAX']['seasonal_climatology_monthly']
    t2m_min_clima = insights['T2M_MIN']['seasonal_climatology_monthly']
    
    months = list(t2m_clima.keys())
    
    fig.add_trace(go.Scatter(
        x=months, y=list(t2m_clima.values()),
        mode='lines+markers', name='Avg Temp', line=dict(color='blue', width=3)
    ), row=2, col=1)
    
    fig.add_trace(go.Scatter(
        x=months, y=list(t2m_max_clima.values()),
        mode='lines+markers', name='Max Temp', line=dict(color='red', width=3)
    ), row=2, col=1)
    
    fig.add_trace(go.Scatter(
        x=months, y=list(t2m_min_clima.values()),
        mode='lines+markers', name='Min Temp', line=dict(color='lightblue', width=3)
    ), row=2, col=1)
    
    # Temperature distribution
    for temp_type, color in [('T2M', 'blue'), ('T2M_MAX', 'red'), ('T2M_MIN', 'lightblue')]:
        temp_values = temp_data[temp_data['parameter'] == temp_type]['value']
        fig.add_trace(go.Box(
            y=temp_values, name=temp_type, marker_color=color,
            boxpoints=False
        ), row=2, col=2)
    
    fig.update_layout(
        height=800,
        title_text="Temperature Analysis Dashboard",
        template='plotly_white',
        showlegend=True
    )
    
    return fig

def create_hydrological_plots(raw_data, insights):
    """Create precipitation and humidity plots"""
    # Extract hydrological data
    hydro_data = raw_data[raw_data['parameter'].isin(['PRECTOTCORR', 'RH2M'])].copy()
    hydro_data['date'] = pd.to_datetime(hydro_data['date'])
    
    # Pivot data
    hydro_pivot = hydro_data.pivot_table(
        index='date', 
        columns='parameter', 
        values='value'
    ).reset_index()
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'Daily Precipitation', 
            'Daily Relative Humidity',
            'Monthly Precipitation Climatology',
            'Monthly Humidity Climatology'
        ),
        specs=[[{}, {}], [{}, {}]]
    )
    
    # Precipitation time series
    fig.add_trace(go.Scatter(
        x=hydro_pivot['date'], y=hydro_pivot['PRECTOTCORR'],
        mode='lines', name='Precipitation', line=dict(color='blue', width=1),
        fill='tozeroy', fillcolor='rgba(0,0,255,0.1)'
    ), row=1, col=1)
    
    # Humidity time series
    fig.add_trace(go.Scatter(
        x=hydro_pivot['date'], y=hydro_pivot['RH2M'],
        mode='lines', name='Humidity', line=dict(color='green', width=1)
    ), row=1, col=2)
    
    # Monthly climatology - Precipitation
    precip_clima = insights['PRECTOTCORR']['seasonal_climatology_monthly']
    fig.add_trace(go.Bar(
        x=list(precip_clima.keys()), y=list(precip_clima.values()),
        name='Precipitation', marker_color='blue'
    ), row=2, col=1)
    
    # Monthly climatology - Humidity
    rh_clima = insights['RH2M']['seasonal_climatology_monthly']
    fig.add_trace(go.Bar(
        x=list(rh_clima.keys()), y=list(rh_clima.values()),
        name='Humidity', marker_color='green'
    ), row=2, col=2)
    
    fig.update_layout(
        height=600,
        title_text="Hydrological Parameters Dashboard",
        template='plotly_white',
        showlegend=True
    )
    
    # Update y-axis labels
    fig.update_yaxes(title_text="Precipitation (mm/day)", row=1, col=1)
    fig.update_yaxes(title_text="Relative Humidity (%)", row=1, col=2)
    fig.update_yaxes(title_text="Precipitation (mm/day)", row=2, col=1)
    fig.update_yaxes(title_text="Relative Humidity (%)", row=2, col=2)
    
    return fig

def create_wind_plots(raw_data, insights):
    """Create wind speed analysis plots"""
    wind_data = raw_data[raw_data['parameter'] == 'WS10M'].copy()
    wind_data['date'] = pd.to_datetime(wind_data['date'])
    wind_data['year'] = wind_data['date'].dt.year
    wind_data['month'] = wind_data['date'].dt.month
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'Daily Wind Speed Time Series', 
            'Monthly Wind Speed Climatology',
            'Annual Wind Speed Trends',
            'Wind Speed Distribution'
        )
    )
    
    # Daily time series
    fig.add_trace(go.Scatter(
        x=wind_data['date'], y=wind_data['value'],
        mode='lines', name='Wind Speed', line=dict(color='purple', width=1)
    ), row=1, col=1)
    
    # Monthly climatology
    wind_clima = insights['WS10M']['seasonal_climatology_monthly']
    fig.add_trace(go.Bar(
        x=list(wind_clima.keys()), y=list(wind_clima.values()),
        name='Wind Speed', marker_color='purple'
    ), row=1, col=2)
    
    # Annual trends
    annual_wind = wind_data.groupby('year')['value'].mean().reset_index()
    fig.add_trace(go.Scatter(
        x=annual_wind['year'], y=annual_wind['value'],
        mode='lines+markers', name='Annual Avg',
        line=dict(color='purple', width=3)
    ), row=2, col=1)
    
    # Distribution
    fig.add_trace(go.Histogram(
        x=wind_data['value'], name='Distribution',
        marker_color='purple', nbinsx=30
    ), row=2, col=2)
    
    fig.update_layout(
        height=600,
        title_text="Wind Speed Analysis Dashboard",
        template='plotly_white',
        showlegend=True
    )
    
    # Update y-axis labels
    fig.update_yaxes(title_text="Wind Speed (m/s)", row=1, col=1)
    fig.update_yaxes(title_text="Wind Speed (m/s)", row=1, col=2)
    fig.update_yaxes(title_text="Wind Speed (m/s)", row=2, col=1)
    fig.update_yaxes(title_text="Frequency", row=2, col=2)
    
    return fig

def create_agricultural_water_plots(et0_df, cwr_df, balance_df, insights):
    """Create agricultural water management plots"""
    # Convert dates
    et0_df['date'] = pd.to_datetime(et0_df['date'])
    cwr_df['date'] = pd.to_datetime(cwr_df['date'])
    balance_df['month'] = pd.to_datetime(balance_df['month'])
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'Daily ET₀ and Crop Water Requirement', 
            'Monthly Water Balance',
            'ET₀ Monthly Climatology',
            'CWR Monthly Climatology'
        )
    )
    
    # Daily ET0 and CWR
    fig.add_trace(go.Scatter(
        x=et0_df['date'], y=et0_df['ET0_mm_day'],
        mode='lines', name='ET₀', line=dict(color='green', width=1)
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=cwr_df['date'], y=cwr_df['CWR_mm_day'],
        mode='lines', name='CWR', line=dict(color='brown', width=1)
    ), row=1, col=1)
    
    # Monthly water balance
    fig.add_trace(go.Bar(
        x=balance_df['month'], y=balance_df['CWR_mm_day'],
        name='Crop Water Requirement', marker_color='brown'
    ), row=1, col=2)
    
    fig.add_trace(go.Bar(
        x=balance_df['month'], y=balance_df['precip_mm_day'],
        name='Precipitation', marker_color='blue'
    ), row=1, col=2)
    
    fig.add_trace(go.Scatter(
        x=balance_df['month'], y=balance_df['irrigation_need_mm_day'],
        mode='lines+markers', name='Irrigation Need',
        line=dict(color='red', width=3)
    ), row=1, col=2)
    
    # ET0 monthly climatology
    et0_clima = insights['ET0']['seasonal_climatology']
    fig.add_trace(go.Bar(
        x=list(et0_clima.keys()), y=list(et0_clima.values()),
        name='ET₀', marker_color='lightgreen'
    ), row=2, col=1)
    
    # CWR monthly climatology
    cwr_clima = insights['CWR']['seasonal_climatology']
    fig.add_trace(go.Bar(
        x=list(cwr_clima.keys()), y=list(cwr_clima.values()),
        name='CWR', marker_color='sandybrown'
    ), row=2, col=2)
    
    fig.update_layout(
        height=700,
        title_text="Agricultural Water Management Dashboard",
        template='plotly_white',
        barmode='group',
        showlegend=True
    )
    
    # Update y-axis labels
    fig.update_yaxes(title_text="Water (mm/day)", row=1, col=1)
    fig.update_yaxes(title_text="Water (mm/day)", row=1, col=2)
    fig.update_yaxes(title_text="ET₀ (mm/day)", row=2, col=1)
    fig.update_yaxes(title_text="CWR (mm/day)", row=2, col=2)
    
    return fig

def create_irrigation_balance_plots(balance_df, insights):
    """Create irrigation balance and deficit analysis"""
    balance_df['month'] = pd.to_datetime(balance_df['month'])
    balance_df['year'] = balance_df['month'].dt.year
    balance_df['month_num'] = balance_df['month'].dt.month
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'Monthly Irrigation Need', 
            'Annual Irrigation Deficit',
            'Seasonal Deficit Pattern',
            'Irrigation Need Distribution'
        )
    )
    
    # Monthly irrigation need
    fig.add_trace(go.Bar(
        x=balance_df['month'], y=balance_df['irrigation_need_mm_day'],
        name='Irrigation Need', marker_color='red'
    ), row=1, col=1)
    
    # Annual deficit
    annual_deficit = balance_df.groupby('year')['irrigation_need_mm_day'].sum().reset_index()
    annual_deficit['deficit_mm'] = -annual_deficit['irrigation_need_mm_day']
    
    fig.add_trace(go.Bar(
        x=annual_deficit['year'], y=annual_deficit['deficit_mm'],
        name='Annual Deficit', marker_color='darkred'
    ), row=1, col=2)
    
    # Seasonal pattern
    monthly_avg_deficit = balance_df.groupby('month_num')['irrigation_need_mm_day'].mean().reset_index()
    monthly_avg_deficit['deficit_mm'] = -monthly_avg_deficit['irrigation_need_mm_day']
    
    fig.add_trace(go.Scatter(
        x=monthly_avg_deficit['month_num'], y=monthly_avg_deficit['deficit_mm'],
        mode='lines+markers', name='Seasonal Pattern',
        line=dict(color='red', width=3)
    ), row=2, col=1)
    
    # Distribution
    fig.add_trace(go.Histogram(
        x=-balance_df['irrigation_need_mm_day'], name='Deficit Distribution',
        marker_color='red', nbinsx=20
    ), row=2, col=2)
    
    fig.update_layout(
        height=600,
        title_text="Irrigation Balance Analysis",
        template='plotly_white',
        showlegend=True
    )
    
    # Update y-axis labels
    fig.update_yaxes(title_text="Irrigation Need (mm/day)", row=1, col=1)
    fig.update_yaxes(title_text="Annual Deficit (mm)", row=1, col=2)
    fig.update_yaxes(title_text="Average Deficit (mm/day)", row=2, col=1)
    fig.update_yaxes(title_text="Frequency", row=2, col=2)
    
    return fig

def create_summary_dashboard(insights):
    """Create a summary dashboard with key metrics"""
    metrics = [
        'Solar Radiation (kW-hr/m²/day)',
        'Temperature (°C)',
        'Precipitation (mm/day)',
        'Relative Humidity (%)',
        'Wind Speed (m/s)',
        'ET₀ (mm/day)',
        'CWR (mm/day)'
    ]
    
    values = [
        insights['ALLSKY_SFC_SW_DWN']['mean'],
        insights['T2M']['mean'],
        insights['PRECTOTCORR']['mean'],
        insights['RH2M']['mean'],
        insights['WS10M']['mean'],
        insights['ET0']['mean_mm_day'],
        insights['CWR']['mean_mm_day']
    ]
    
    trends = [
        insights['ALLSKY_SFC_SW_DWN']['trend_per_decade'],
        insights['T2M']['trend_per_decade'],
        insights['PRECTOTCORR']['trend_per_decade'],
        insights['RH2M']['trend_per_decade'],
        insights['WS10M']['trend_per_decade'],
        insights['ET0']['trend_per_decade_mm_day'],
        insights['CWR']['trend_per_decade_mm_day']
    ]
    
    colors = ['orange', 'blue', 'lightblue', 'green', 'purple', 'lightgreen', 'brown']
    
    fig = go.Figure()
    
    for i, (metric, value, trend, color) in enumerate(zip(metrics, values, trends, colors)):
        fig.add_trace(go.Indicator(
            mode = "number+delta",
            value = value,
            number = {'suffix': " ", 'font': {'size': 24}},
            delta = {'reference': value - trend/10, 'relative': False, 
                    'valueformat': '.3f', 'font': {'size': 14}},
            title = {'text': metric, 'font': {'size': 16}},
            domain = {'row': i % 4, 'column': i // 4},
            gauge = {'axis': {'range': [None, max(values)*1.1]},
                    'bar': {'color': color}}
        ))
    
    fig.update_layout(
        grid = {'rows': 4, 'columns': 2, 'pattern': "independent"},
        template = 'plotly_white',
        height = 600,
        title = 'Agricultural Solar Monitoring - Key Metrics Summary'
    )
    
    return fig

# Main function to generate all plots
def generate_all_plots(data_dict):
    """Generate all plots for the agricultural solar monitoring dashboard"""
    
    plots = {}
    
    # Summary dashboard
    plots['summary'] = create_summary_dashboard(data_dict['insights'])
    
    # Solar energy plots
    solar_daily, solar_monthly, solar_annual = create_solar_energy_plots(
        data_dict['raw_data'], data_dict['insights']
    )
    plots['solar_daily'] = solar_daily
    plots['solar_monthly'] = solar_monthly
    plots['solar_annual'] = solar_annual
    
    # Temperature plots
    plots['temperature'] = create_temperature_plots(data_dict['raw_data'], data_dict['insights'])
    
    # Hydrological plots
    plots['hydrological'] = create_hydrological_plots(data_dict['raw_data'], data_dict['insights'])
    
    # Wind plots
    plots['wind'] = create_wind_plots(data_dict['raw_data'], data_dict['insights'])
    
    # Agricultural water plots
    plots['agricultural_water'] = create_agricultural_water_plots(
        data_dict['et0_df'], data_dict['cwr_df'], data_dict['balance_df'], data_dict['insights']
    )
    
    # Irrigation balance plots
    plots['irrigation_balance'] = create_irrigation_balance_plots(
        data_dict['balance_df'], data_dict['insights']
    )
    
    return plots

# Usage example:
# plots = generate_all_plots(your_data_dict)
# plots['summary'].show()
# plots['solar_daily'].show()
# etc.
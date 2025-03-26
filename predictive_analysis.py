"""
Module for predictive analysis of EV charging data.
This module uses time series analysis to forecast future charging costs and usage.
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import statsmodels.api as sm
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.seasonal import seasonal_decompose
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline


def prepare_time_series_data(df):
    """
    Prepare charging data for time series analysis.
    
    Args:
        df (DataFrame): DataFrame containing charging data with date column
        
    Returns:
        DataFrame: Resampled and prepared data for time series analysis
    """
    # Ensure data is sorted by date
    df = df.copy()
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # Create a time series DataFrame with date as index
        ts_df = df.set_index('date')
        
        # Handle missing values
        if 'total_cost' in ts_df.columns:
            ts_df['total_cost'] = pd.to_numeric(ts_df['total_cost'], errors='coerce')
        
        if 'energy_kwh' in ts_df.columns:
            ts_df['energy_kwh'] = pd.to_numeric(ts_df['energy_kwh'], errors='coerce')
            
        return ts_df
    else:
        return None


def forecast_monthly_cost(df, forecast_periods=3):
    """
    Forecast monthly charging costs for the next few months.
    
    Args:
        df (DataFrame): DataFrame containing charging data
        forecast_periods (int): Number of months to forecast
        
    Returns:
        tuple: (forecast DataFrame, forecast figure)
    """
    ts_df = prepare_time_series_data(df)
    
    if ts_df is None or len(ts_df) < 5:  # Need at least 5 data points for a meaningful forecast
        return None, None
    
    try:
        # Resample to monthly data
        monthly_data = ts_df.resample('M')['total_cost'].sum().fillna(0)
        
        # Fit ARIMA model
        if len(monthly_data) >= 12:  # If we have at least a year of data, try seasonal decomposition
            try:
                # Try to use seasonal ARIMA if enough data points
                result = seasonal_decompose(monthly_data, model='additive', period=min(12, len(monthly_data)//2))
                model = sm.tsa.statespace.SARIMAX(monthly_data,
                                                order=(1, 1, 1),
                                                seasonal_order=(1, 1, 1, min(12, len(monthly_data)//2)),
                                                enforce_stationarity=False)
            except:
                # Fallback to simple ARIMA
                model = ARIMA(monthly_data, order=(1, 1, 1))
        else:
            # Use simple ARIMA for less data
            model = ARIMA(monthly_data, order=(1, 1, 1))
            
        model_fit = model.fit()
        
        # Make forecast
        forecast = model_fit.forecast(steps=forecast_periods)
        forecast_index = pd.date_range(start=monthly_data.index[-1] + pd.DateOffset(months=1), 
                                      periods=forecast_periods, 
                                      freq='M')
        forecast = pd.Series(forecast, index=forecast_index)
        
        # Create forecast DataFrame
        forecast_df = pd.DataFrame({
            'date': forecast.index,
            'predicted_cost': forecast.values
        })
        
        # Create visualization
        fig = go.Figure()
        
        # Historical data
        fig.add_trace(go.Scatter(
            x=monthly_data.index,
            y=monthly_data.values,
            mode='lines+markers',
            name='Historical Cost',
            line=dict(color='blue')
        ))
        
        # Forecast
        fig.add_trace(go.Scatter(
            x=forecast.index,
            y=forecast.values,
            mode='lines+markers',
            name='Forecast',
            line=dict(color='red', dash='dash')
        ))
        
        # Add confidence intervals (simple approximation)
        std_err = np.std(monthly_data) * 1.96 / np.sqrt(len(monthly_data))
        fig.add_trace(go.Scatter(
            x=forecast.index,
            y=forecast.values + std_err,
            mode='lines',
            line=dict(width=0),
            showlegend=False
        ))
        
        fig.add_trace(go.Scatter(
            x=forecast.index,
            y=forecast.values - std_err,
            mode='lines',
            line=dict(width=0),
            fillcolor='rgba(255, 0, 0, 0.1)',
            fill='tonexty',
            name='95% Confidence Interval'
        ))
        
        fig.update_layout(
            title='Monthly Charging Cost Forecast',
            xaxis_title='Month',
            yaxis_title='Total Cost',
            legend_title='',
            hovermode="x unified"
        )
        
        return forecast_df, fig
        
    except Exception as e:
        print(f"Forecasting error: {e}")
        return None, None


def predict_cost_by_provider(df):
    """
    Predict cost trends by provider over time.
    
    Args:
        df (DataFrame): DataFrame containing charging data
        
    Returns:
        plotly figure: Visualization of cost trends by provider
    """
    if 'provider' not in df.columns or len(df) < 5:
        return None
    
    try:
        # Ensure provider column exists and has values
        df = df.copy()
        df['date'] = pd.to_datetime(df['date'])
        df['total_cost'] = pd.to_numeric(df['total_cost'], errors='coerce')
        df['energy_kwh'] = pd.to_numeric(df['energy_kwh'], errors='coerce')
        
        # Group by provider and month
        df['year_month'] = df['date'].dt.strftime('%Y-%m')
        provider_monthly = df.groupby(['provider', 'year_month']).agg({
            'total_cost': 'sum',
            'energy_kwh': 'sum',
            'date': 'count'
        }).reset_index()
        
        provider_monthly.rename(columns={'date': 'session_count'}, inplace=True)
        provider_monthly['cost_per_kwh'] = provider_monthly['total_cost'] / provider_monthly['energy_kwh']
        
        # Create date sequence for prediction
        all_months = pd.date_range(
            start=df['date'].min().replace(day=1),
            end=(df['date'].max().replace(day=1) + pd.DateOffset(months=3)),
            freq='MS'
        )
        future_months = [d.strftime('%Y-%m') for d in all_months]
        
        # Get list of providers
        providers = df['provider'].unique()
        
        # Create plot
        fig = go.Figure()
        
        for provider in providers:
            # Filter data for this provider
            provider_data = provider_monthly[provider_monthly['provider'] == provider]
            
            if len(provider_data) >= 3:  # Need at least 3 data points for regression
                # Prepare data for regression
                X = np.array(range(len(provider_data))).reshape(-1, 1)
                y = provider_data['cost_per_kwh'].values
                
                # Simple linear regression
                model = LinearRegression()
                model.fit(X, y)
                
                # Create prediction range including 3 months into future
                X_pred = np.array(range(len(provider_data) + 3)).reshape(-1, 1)
                y_pred = model.predict(X_pred)
                
                # Get date labels for this provider
                provider_months = list(provider_data['year_month'])
                
                # Add future months
                future_idx = len(provider_months)
                provider_future_months = future_months[future_idx:future_idx+3]
                all_provider_months = provider_months + provider_future_months
                
                # Add to plot
                fig.add_trace(go.Scatter(
                    x=provider_data['year_month'],
                    y=provider_data['cost_per_kwh'],
                    mode='markers',
                    name=f'{provider} (Actual)'
                ))
                
                fig.add_trace(go.Scatter(
                    x=all_provider_months[:len(y_pred)],
                    y=y_pred,
                    mode='lines',
                    name=f'{provider} (Trend)',
                    line=dict(dash='dash')
                ))
        
        fig.update_layout(
            title='Cost per kWh Trends by Provider',
            xaxis_title='Month',
            yaxis_title='Cost per kWh',
            legend_title='',
            hovermode="x unified"
        )
        
        return fig
        
    except Exception as e:
        print(f"Provider prediction error: {e}")
        return None


def usage_prediction(df, future_days=30):
    """
    Predict future charging usage based on past patterns.
    
    Args:
        df (DataFrame): DataFrame containing charging data
        future_days (int): Number of days to predict into the future
        
    Returns:
        tuple: (prediction DataFrame, prediction figure)
    """
    if len(df) < 10:  # Need enough data for meaningful prediction
        return None, None
    
    try:
        df = df.copy()
        df['date'] = pd.to_datetime(df['date'])
        df['energy_kwh'] = pd.to_numeric(df['energy_kwh'], errors='coerce')
        
        # Create features
        df['day_of_week'] = df['date'].dt.dayofweek
        df['month'] = df['date'].dt.month
        df['week_of_year'] = df['date'].dt.isocalendar().week
        
        # Group by date for daily usage
        daily_usage = df.groupby(df['date'].dt.date).agg({
            'energy_kwh': 'sum',
            'day_of_week': 'first',
            'month': 'first',
            'week_of_year': 'first'
        }).reset_index()
        
        # Fill in missing days with zeros
        date_range = pd.date_range(daily_usage['date'].min(), daily_usage['date'].max())
        full_range = pd.DataFrame({'date': date_range})
        daily_usage = pd.merge(full_range, daily_usage, on='date', how='left').fillna(0)
        
        # Fix features for filled days
        for i, row in daily_usage.iterrows():
            if row['day_of_week'] == 0:  # If day_of_week is 0, it means it was filled
                daily_usage.at[i, 'day_of_week'] = row['date'].dayofweek
                daily_usage.at[i, 'month'] = row['date'].month
                daily_usage.at[i, 'week_of_year'] = row['date'].isocalendar()[1]
        
        # Create training data
        X = daily_usage[['day_of_week', 'month', 'week_of_year']]
        y = daily_usage['energy_kwh']
        
        # Train a Random Forest model
        model = Pipeline([
            ('scaler', StandardScaler()),
            ('rf', RandomForestRegressor(n_estimators=50, random_state=42))
        ])
        
        model.fit(X, y)
        
        # Generate future dates
        last_date = daily_usage['date'].max()
        future_dates = pd.date_range(start=last_date + timedelta(days=1), periods=future_days)
        
        # Create features for future dates
        future_X = pd.DataFrame({
            'date': future_dates,
            'day_of_week': [d.dayofweek for d in future_dates],
            'month': [d.month for d in future_dates],
            'week_of_year': [d.isocalendar()[1] for d in future_dates]
        })
        
        # Make predictions
        X_pred = future_X[['day_of_week', 'month', 'week_of_year']]
        future_X['predicted_kwh'] = model.predict(X_pred)
        
        # Create visualization
        fig = go.Figure()
        
        # Historical data
        fig.add_trace(go.Scatter(
            x=daily_usage['date'],
            y=daily_usage['energy_kwh'],
            mode='lines+markers',
            name='Historical Usage',
            line=dict(color='blue')
        ))
        
        # Prediction
        fig.add_trace(go.Scatter(
            x=future_X['date'],
            y=future_X['predicted_kwh'],
            mode='lines+markers',
            name='Predicted Usage',
            line=dict(color='green', dash='dash')
        ))
        
        # Add 7-day moving average of historical data
        rolling_avg = daily_usage['energy_kwh'].rolling(window=7, min_periods=1).mean()
        fig.add_trace(go.Scatter(
            x=daily_usage['date'],
            y=rolling_avg,
            mode='lines',
            name='7-Day Moving Average',
            line=dict(color='red')
        ))
        
        fig.update_layout(
            title='Daily Charging Usage Prediction',
            xaxis_title='Date',
            yaxis_title='Energy (kWh)',
            legend_title='',
            hovermode="x unified"
        )
        
        return future_X, fig
        
    except Exception as e:
        print(f"Usage prediction error: {e}")
        return None, None
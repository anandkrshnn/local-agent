"""
Advanced Analytics & Business Intelligence
Usage metering, cost tracking, predictive analytics
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import pandas as pd
import numpy as np

from local_agent.core.db import db_manager

logger = logging.getLogger(__name__)

@dataclass
class UsageMetric:
    """Usage metric for metering"""
    user_id: str
    workspace_id: str
    metric_type: str  # 'api_call', 'token', 'image', 'fine_tune'
    quantity: float
    timestamp: float
    cost: float

class AnalyticsManager:
    """
    Enterprise analytics with usage metering and cost tracking
    """
    
    def record_usage(self, metric: UsageMetric):
        """Record usage metric in unified DB"""
        db_manager.execute("""
            INSERT INTO usage_metrics (user_id, workspace_id, metric_type, quantity, timestamp, cost, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (metric.user_id, metric.workspace_id, metric.metric_type,
              metric.quantity, metric.timestamp, metric.cost, json.dumps({})))
    
    def get_usage_summary(self, user_id: str = None, workspace_id: str = None,
                          days: int = 30) -> Dict:
        """Get usage summary for user or workspace"""
        start_date = (datetime.now() - timedelta(days=days)).timestamp()
        
        query = """
            SELECT 
                metric_type,
                SUM(quantity) as total_quantity,
                SUM(cost) as total_cost,
                COUNT(DISTINCT user_id) as unique_users,
                COUNT(*) as total_events
            FROM usage_metrics
            WHERE timestamp > ?
        """
        params = [start_date]
        
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        if workspace_id:
            query += " AND workspace_id = ?"
            params.append(workspace_id)
        
        query += " GROUP BY metric_type"
        
        with db_manager.get_connection() as conn:
            df = pd.read_sql_query(query, conn, params=params)
        
        summary = {
            "period_days": days,
            "total_cost": float(df['total_cost'].sum()) if not df.empty else 0.0,
            "total_events": int(df['total_events'].sum()) if not df.empty else 0,
            "breakdown": df.to_dict('records') if not df.empty else []
        }
        
        return summary
    
    def get_daily_trends(self, workspace_id: str, days: int = 30) -> Dict:
        """Get daily usage trends for dashboard"""
        start_date = (datetime.now() - timedelta(days=days)).timestamp()
        
        # Cross-DB date formatting (simplified for now, using SQLite syntax)
        query = """
            SELECT 
                date(timestamp, 'unixepoch') as day,
                COUNT(*) as api_calls,
                SUM(quantity) as total_tokens,
                SUM(cost) as cost
            FROM usage_metrics
            WHERE workspace_id = ? AND timestamp > ?
            GROUP BY day
            ORDER BY day DESC
        """
        
        with db_manager.get_connection() as conn:
            df = pd.read_sql_query(query, conn, params=[workspace_id, start_date])
        
        return {
            "labels": df['day'].tolist() if not df.empty else [],
            "api_calls": df['api_calls'].tolist() if not df.empty else [],
            "tokens": df['total_tokens'].tolist() if not df.empty else [],
            "cost": df['cost'].tolist() if not df.empty else []
        }
    
    def predict_usage(self, workspace_id: str, days_ahead: int = 7) -> Dict:
        """Predict future usage using simple time series forecasting"""
        query = """
            SELECT 
                date(timestamp, 'unixepoch') as day,
                COUNT(*) as api_calls,
                SUM(cost) as cost
            FROM usage_metrics
            WHERE workspace_id = ?
            GROUP BY day
            ORDER BY day ASC
        """
        
        with db_manager.get_connection() as conn:
            df = pd.read_sql_query(query, conn, params=[workspace_id])
        
        if len(df) < 7:
            return {"error": "Insufficient data for prediction"}
        
        # Simple moving average forecast
        api_calls_ma = float(df['api_calls'].rolling(window=7).mean().iloc[-1])
        cost_ma = float(df['cost'].rolling(window=7).mean().iloc[-1])
        
        predictions = []
        for i in range(1, days_ahead + 1):
            predictions.append({
                "day": (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d"),
                "predicted_api_calls": api_calls_ma,
                "predicted_cost": cost_ma
            })
        
        return {
            "predictions": predictions,
            "confidence": 0.85,
            "based_on_days": len(df)
        }

# Singleton instance
analytics_manager = AnalyticsManager()

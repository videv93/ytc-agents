"""
Database Models for YTC Trading System
SQLAlchemy models for PostgreSQL database
"""

from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Boolean,
    ForeignKey, JSON, DECIMAL, create_engine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()


def generate_uuid():
    """Generate UUID string"""
    return str(uuid.uuid4())


class Session(Base):
    """Trading session record"""
    __tablename__ = 'sessions'
    __table_args__ = {'schema': 'trading'}

    session_id = Column(String(36), primary_key=True, default=generate_uuid)
    start_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)

    market = Column(String(50), nullable=False)
    instrument = Column(String(50), nullable=False)

    initial_balance = Column(DECIMAL(15, 2), nullable=False)
    final_balance = Column(DECIMAL(15, 2), nullable=True)
    session_pnl = Column(DECIMAL(15, 2), default=0.0)
    session_pnl_pct = Column(Float, default=0.0)

    trades_count = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)

    status = Column(String(20), default='active')  # active, completed, emergency_stop
    stop_reason = Column(String(200), nullable=True)

    # Relationships
    trades = relationship("Trade", back_populates="session")
    agent_decisions = relationship("AgentDecision", back_populates="session")

    def __repr__(self):
        return f"<Session {self.session_id} {self.market}/{self.instrument}>"


class Trade(Base):
    """Individual trade record"""
    __tablename__ = 'trades'
    __table_args__ = {'schema': 'trading'}

    trade_id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey('trading.sessions.session_id'), nullable=False)

    setup_type = Column(String(50), nullable=False)  # pullback, 3_swing_trap, etc.
    direction = Column(String(10), nullable=False)  # long, short
    instrument = Column(String(50), nullable=False)

    # Entry
    entry_time = Column(DateTime, nullable=False)
    entry_price = Column(DECIMAL(12, 4), nullable=False)
    position_size = Column(Integer, nullable=False)
    position_size_lots = Column(Float, nullable=False)

    # Risk
    stop_loss = Column(DECIMAL(12, 4), nullable=False)
    initial_stop = Column(DECIMAL(12, 4), nullable=False)
    risk_amount = Column(DECIMAL(15, 2), nullable=False)
    risk_pct = Column(Float, nullable=False)

    # Targets
    target_1 = Column(DECIMAL(12, 4), nullable=True)
    target_2 = Column(DECIMAL(12, 4), nullable=True)

    # Exit
    exit_time = Column(DateTime, nullable=True)
    exit_price = Column(DECIMAL(12, 4), nullable=True)
    exit_reason = Column(String(50), nullable=True)  # target, stop, time, signal

    # Results
    pnl = Column(DECIMAL(15, 2), nullable=True)
    pnl_pct = Column(Float, nullable=True)
    r_multiple = Column(DECIMAL(6, 2), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    mae = Column(DECIMAL(12, 4), nullable=True)  # Maximum Adverse Excursion
    mfe = Column(DECIMAL(12, 4), nullable=True)  # Maximum Favorable Excursion

    # Metadata
    setup_quality_score = Column(Integer, nullable=True)
    execution_quality_score = Column(Integer, nullable=True)
    notes = Column(String(500), nullable=True)
    metadata = Column(JSON, nullable=True)

    # Relationships
    session = relationship("Session", back_populates="trades")

    def __repr__(self):
        return f"<Trade {self.trade_id} {self.direction} {self.setup_type}>"


class AgentDecision(Base):
    """Audit trail of agent decisions"""
    __tablename__ = 'agent_decisions'
    __table_args__ = {'schema': 'audit'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    session_id = Column(String(36), ForeignKey('trading.sessions.session_id'), nullable=True)
    agent_id = Column(String(100), nullable=False, index=True)
    decision_type = Column(String(100), nullable=False)

    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)

    execution_time_ms = Column(Integer, nullable=True)
    status = Column(String(20), default='success')  # success, failure, partial
    error_message = Column(String(500), nullable=True)

    # Relationships
    session = relationship("Session", back_populates="agent_decisions")

    def __repr__(self):
        return f"<AgentDecision {self.agent_id} {self.decision_type}>"


class MarketStructure(Base):
    """Market structure analysis results"""
    __tablename__ = 'market_structure'
    __table_args__ = {'schema': 'analytics'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    session_id = Column(String(36), nullable=True)

    instrument = Column(String(50), nullable=False)
    timeframe = Column(String(10), nullable=False)

    # Structure data
    swing_highs = Column(JSON, nullable=True)
    swing_lows = Column(JSON, nullable=True)
    support_zones = Column(JSON, nullable=True)
    resistance_zones = Column(JSON, nullable=True)

    # Analysis
    trend_direction = Column(String(20), nullable=True)  # uptrend, downtrend, ranging
    trend_strength = Column(Integer, nullable=True)  # 0-100
    structure_quality = Column(Integer, nullable=True)  # 0-100

    metadata = Column(JSON, nullable=True)

    def __repr__(self):
        return f"<MarketStructure {self.instrument} {self.timeframe}>"


class PerformanceMetrics(Base):
    """Performance metrics and statistics"""
    __tablename__ = 'performance_metrics'
    __table_args__ = {'schema': 'analytics'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    calculated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    period_type = Column(String(20), nullable=False)  # daily, weekly, monthly

    # Trade statistics
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    win_rate_pct = Column(Float, default=0.0)

    # P&L statistics
    gross_profit = Column(DECIMAL(15, 2), default=0.0)
    gross_loss = Column(DECIMAL(15, 2), default=0.0)
    net_profit = Column(DECIMAL(15, 2), default=0.0)
    profit_factor = Column(Float, default=0.0)

    # R-multiple statistics
    average_win_r = Column(Float, default=0.0)
    average_loss_r = Column(Float, default=0.0)
    expectancy_r = Column(Float, default=0.0)
    largest_win_r = Column(Float, default=0.0)
    largest_loss_r = Column(Float, default=0.0)

    # Streak statistics
    current_streak = Column(Integer, default=0)
    max_winning_streak = Column(Integer, default=0)
    max_losing_streak = Column(Integer, default=0)

    # Risk statistics
    max_drawdown_pct = Column(Float, default=0.0)
    sharpe_ratio = Column(Float, default=0.0)

    metadata = Column(JSON, nullable=True)

    def __repr__(self):
        return f"<PerformanceMetrics {self.period_type} {self.period_start}>"

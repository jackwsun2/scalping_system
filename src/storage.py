"""SQLite persistence for signals and orders."""

import json
import sqlite3
from pathlib import Path
from typing import Optional


class TradingStore:
    """Small SQLite store for audit-friendly paper/live trading runs."""

    def __init__(self, db_path: str = "data/trading.sqlite3"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    signal_type TEXT NOT NULL,
                    price REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    reason TEXT NOT NULL,
                    indicators_json TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, signal_type, timestamp, reason)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    qty INTEGER NOT NULL,
                    order_type TEXT NOT NULL,
                    limit_price REAL,
                    order_id TEXT,
                    client_order_id TEXT,
                    status TEXT NOT NULL,
                    signal_timestamp TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(client_order_id)
                )
                """
            )

    def record_signal(self, signal) -> Optional[int]:
        """Insert a signal and return its row id. Duplicate signals are ignored."""
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO signals (
                    symbol, signal_type, price, timestamp, confidence, reason, indicators_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    signal.symbol,
                    signal.signal_type.name,
                    float(signal.price),
                    str(signal.timestamp),
                    float(signal.confidence),
                    signal.reason,
                    json.dumps(signal.indicators, ensure_ascii=False, sort_keys=True),
                ),
            )
            return cursor.lastrowid or None

    def record_order(self, order, signal_timestamp=None) -> Optional[int]:
        """Insert an order and return its row id. Duplicate client ids are ignored."""
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO orders (
                    symbol, side, qty, order_type, limit_price, order_id,
                    client_order_id, status, signal_timestamp
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    order.symbol,
                    order.side,
                    int(order.qty),
                    order.type,
                    order.limit_price,
                    order.order_id,
                    order.client_order_id,
                    order.status,
                    str(signal_timestamp) if signal_timestamp is not None else None,
                ),
            )
            return cursor.lastrowid or None

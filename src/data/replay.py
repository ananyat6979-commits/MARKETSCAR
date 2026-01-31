#!/usr/bin/env python3
"""
Replay Engine - Historical Data Event Streamer
===============================================

Streams frozen baseline data as simulated live events.
Enables:
- Deterministic testing
- Demo scenario playback
- Time-travel debugging

Key features:
- Respects original timestamp ordering
- Configurable playback speed (1x, 10x, 100x)
- Event windowing (e.g., "last 14 days")
- Checkpoint/resume capability
"""

import pandas as pd
import time
from datetime import datetime, timedelta
from pathlib import Path
import json
from typing import Iterator, Optional, Dict, Any
from dataclasses import dataclass, asdict

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent  # src/data/ -> src/ -> project root
DATA_DIR = PROJECT_ROOT / 'data'
RAW_DIR = DATA_DIR / 'raw'
BASELINES_DIR = DATA_DIR / 'baselines'
MANIFEST_PATH = BASELINES_DIR / 'manifest.json'

@dataclass
class Transaction:
    """Single transaction event"""
    invoice: str
    stock_code: str
    description: str
    quantity: int
    invoice_date: datetime
    price: float
    customer_id: int
    country: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        d = asdict(self)
        d['invoice_date'] = self.invoice_date.isoformat()
        return d
    
    @property
    def revenue(self) -> float:
        """Calculate transaction revenue"""
        return self.quantity * self.price

class ReplayEngine:
    """
    Streams historical transactions as live events.
    """
    
    def __init__(
        self,
        csv_path: Path,
        manifest_path: Path = MANIFEST_PATH,
        verify_hash: bool = True
    ):
        """
        Initialize replay engine.
        
        Args:
            csv_path: Path to baseline CSV
            manifest_path: Path to manifest for verification
            verify_hash: If True, verify data integrity before replay
        """
        self.csv_path = csv_path
        self.manifest_path = manifest_path
        
        # Verify baseline integrity
        if verify_hash:
            self._verify_integrity()
        
        # Load data
        print(f"Loading baseline data from {csv_path}...")
        self.df = pd.read_csv(csv_path, parse_dates=['InvoiceDate'])
        self.df = self.df.sort_values('InvoiceDate').reset_index(drop=True)
        
        print(f"Loaded {len(self.df):,} transactions")
        print(f"Date range: {self.df['InvoiceDate'].min()} to {self.df['InvoiceDate'].max()}")
        
        # Playback state
        self.current_index = 0
        self.playback_start_time = None
        self.data_start_time = self.df['InvoiceDate'].iloc[0]
        self.data_end_time = self.df['InvoiceDate'].iloc[-1]
        
    def _verify_integrity(self):
        """Verify baseline hash matches manifest"""
        import sys
        import hashlib
        
        # Load manifest
        if not self.manifest_path.exists():
            raise FileNotFoundError(f"Manifest not found: {self.manifest_path}")
        
        with open(self.manifest_path, 'r') as f:
            manifest = json.load(f)
        
        expected_hash = manifest['file']['hash']
        
        # Compute actual hash
        hash_obj = hashlib.sha256()
        with open(self.csv_path, 'rb') as f:
            while chunk := f.read(8192):
                hash_obj.update(chunk)
        
        actual_hash = hash_obj.hexdigest()
        
        if actual_hash != expected_hash:
            raise ValueError(
                f"Baseline hash mismatch!\n"
                f"Expected: {expected_hash}\n"
                f"Actual: {actual_hash}\n"
                f"BASELINE TAMPERING DETECTED"
            )
        
        print(f"✓ Baseline integrity verified")
    
    def reset(self):
        """Reset playback to beginning"""
        self.current_index = 0
        self.playback_start_time = None
    
    def stream(
        self,
        speed_multiplier: float = 1.0,
        max_events: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        realtime: bool = False
    ) -> Iterator[Transaction]:
        """
        Stream transactions as events.
        
        Args:
            speed_multiplier: Playback speed (1.0 = realtime, 10.0 = 10x faster)
            max_events: Maximum number of events to stream (None = all)
            start_date: Filter to events after this date
            end_date: Filter to events before this date
            realtime: If True, respect inter-event timing; if False, stream continuously
        
        Yields:
            Transaction objects
        """
        # Filter by date range if specified
        df = self.df
        
        if start_date:
            df = df[df['InvoiceDate'] >= start_date]
        
        if end_date:
            df = df[df['InvoiceDate'] <= end_date]
        
        if len(df) == 0:
            print("No transactions in specified date range")
            return
        
        # Reset index after filtering
        df = df.reset_index(drop=True)
        
        print(f"Streaming {len(df):,} transactions at {speed_multiplier}x speed")
        
        events_streamed = 0
        self.playback_start_time = time.time()
        prev_event_time = None
        
        for idx, row in df.iterrows():
            # Create transaction
            txn = Transaction(
                invoice=row['Invoice'],
                stock_code=row['StockCode'],
                description=row['Description'],
                quantity=int(row['Quantity']),
                invoice_date=row['InvoiceDate'],
                price=float(row['Price']),
                customer_id=int(row['Customer ID']),
                country=row['Country']
            )
            
            # Handle timing (if realtime mode)
            if realtime and prev_event_time is not None:
                # Calculate time delta in original data
                time_delta = (txn.invoice_date - prev_event_time).total_seconds()
                
                # Scale by speed multiplier
                sleep_duration = time_delta / speed_multiplier
                
                # Sleep if positive delay
                if sleep_duration > 0:
                    time.sleep(min(sleep_duration, 1.0))  # Cap at 1 second per event
            
            prev_event_time = txn.invoice_date
            
            yield txn
            
            events_streamed += 1
            
            # Check max events limit
            if max_events and events_streamed >= max_events:
                print(f"Reached max_events limit: {max_events}")
                break
        
        print(f"Stream complete: {events_streamed:,} events")
    
    def get_window(
        self,
        end_date: datetime,
        window_days: int = 14
    ) -> pd.DataFrame:
        """
        Get a time window of data (for baseline comparison).
        
        Args:
            end_date: End of window
            window_days: Number of days to look back
        
        Returns:
            DataFrame of transactions in window
        """
        start_date = end_date - timedelta(days=window_days)
        
        mask = (
            (self.df['InvoiceDate'] >= start_date) &
            (self.df['InvoiceDate'] <= end_date)
        )
        
        return self.df[mask].copy()
    
    def inject_scenario(
        self,
        scenario_type: str,
        base_date: datetime,
        params: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """
        Inject synthetic anomaly scenarios for testing.
        
        Args:
            scenario_type: Type of scenario ('adversarial_spoof', 'flash_crash', 'normal')
            base_date: When to inject scenario
            params: Scenario-specific parameters
        
        Returns:
            DataFrame of synthetic transactions
        """
        params = params or {}
        
        if scenario_type == 'adversarial_spoof':
            # Simulate coordinated price manipulation
            n_transactions = params.get('n_transactions', 50)
            price_spike = params.get('price_spike', 1.25)  # 25% increase
            
            # Pick random SKUs
            sample_skus = self.df['StockCode'].sample(5, random_state=42).tolist()
            
            synthetic_txns = []
            for i in range(n_transactions):
                sku = sample_skus[i % len(sample_skus)]
                base_price = self.df[self.df['StockCode'] == sku]['Price'].mean()
                
                synthetic_txns.append({
                    'Invoice': f'SPOOF{i:05d}',
                    'StockCode': sku,
                    'Description': f'SYNTHETIC {sku}',
                    'Quantity': 1,
                    'InvoiceDate': base_date + timedelta(seconds=i * 0.04),  # Clustered timestamps
                    'Price': base_price * price_spike,
                    'Customer ID': 99999,  # Suspicious customer
                    'Country': 'SYNTHETIC'
                })
            
            return pd.DataFrame(synthetic_txns)
        
        elif scenario_type == 'flash_crash':
            # Simulate sudden price collapse
            n_transactions = params.get('n_transactions', 100)
            price_drop = params.get('price_drop', 0.4)  # 60% drop
            
            sample_skus = self.df['StockCode'].sample(20, random_state=42).tolist()
            
            synthetic_txns = []
            for i in range(n_transactions):
                sku = sample_skus[i % len(sample_skus)]
                base_price = self.df[self.df['StockCode'] == sku]['Price'].mean()
                
                synthetic_txns.append({
                    'Invoice': f'CRASH{i:05d}',
                    'StockCode': sku,
                    'Description': f'SYNTHETIC {sku}',
                    'Quantity': 1,
                    'InvoiceDate': base_date + timedelta(seconds=i * 0.1),
                    'Price': base_price * price_drop,
                    'Customer ID': 99998,
                    'Country': 'SYNTHETIC'
                })
            
            return pd.DataFrame(synthetic_txns)
        
        else:
            raise ValueError(f"Unknown scenario type: {scenario_type}")

def main():
    """Demo replay engine"""
    
    csv_path = RAW_DIR / 'online_retail_II.csv'
    
    # Initialize engine
    engine = ReplayEngine(csv_path, verify_hash=True)
    
    print("\n" + "="*60)
    print("REPLAY ENGINE DEMO")
    print("="*60)
    
    # Demo 1: Stream first 10 transactions
    print("\nDemo 1: Stream first 10 transactions (no timing)")
    print("-" * 60)
    
    count = 0
    for txn in engine.stream(max_events=10, realtime=False):
        print(f"{txn.invoice_date} | {txn.stock_code:8s} | £{txn.price:6.2f} x {txn.quantity:2d} = £{txn.revenue:7.2f}")
        count += 1
    
    # Demo 2: Get 14-day window
    print("\nDemo 2: Get 14-day window ending 2010-01-01")
    print("-" * 60)
    
    window_end = datetime(2010, 1, 1)
    window_df = engine.get_window(window_end, window_days=14)
    print(f"Window contains {len(window_df):,} transactions")
    print(f"Revenue: £{window_df['Price'].sum():,.2f}")
    
    # Demo 3: Inject adversarial scenario
    print("\nDemo 3: Inject adversarial spoof scenario")
    print("-" * 60)
    
    spoof_df = engine.inject_scenario(
        'adversarial_spoof',
        base_date=datetime(2010, 6, 1, 14, 30),
        params={'n_transactions': 20, 'price_spike': 1.4}
    )
    
    print(f"Generated {len(spoof_df)} spoofed transactions")
    print("\nSample:")
    print(spoof_df.head())
    
    print("\n" + "="*60)
    print("✓ Replay engine operational")
    print("="*60)

if __name__ == '__main__':
    main()

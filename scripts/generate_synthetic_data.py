#!/usr/bin/env python3
"""
Synthetic UCI Online Retail II Data Generator
==============================================

IMPORTANT: This is a DEVELOPMENT SUBSTITUTE for the real UCI dataset.
Production deployments MUST use the actual UCI Online Retail II dataset from:
https://archive.ics.uci.edu/ml/machine-learning-databases/00502/online_retail_II.xlsx

Schema matches UCI Online Retail II exactly:
- Invoice: Transaction ID
- StockCode: Product SKU
- Description: Product name
- Quantity: Units purchased
- InvoiceDate: Timestamp
- Price: Unit price
- Customer ID: Customer identifier
- Country: Customer country

This generator produces DETERMINISTIC output via fixed random seed.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import hashlib
import json

# FROZEN CONFIGURATION
RANDOM_SEED = 42
NUM_TRANSACTIONS = 50000
NUM_SKUS = 500
NUM_CUSTOMERS = 2000
START_DATE = datetime(2009, 12, 1)
END_DATE = datetime(2010, 12, 9)

# Fix all randomness
np.random.seed(RANDOM_SEED)

def generate_sku_codes(n_skus):
    """Generate realistic SKU codes (5-6 character alphanumeric)"""
    skus = []
    for i in range(n_skus):
        # Format: 5-digit numeric or alphanumeric
        if i % 3 == 0:
            skus.append(f"{i:05d}")
        else:
            skus.append(f"{np.random.choice(list('ABCDEFGHIJKLMNOPQRSTUVWXYZ'))}{i:04d}")
    return skus

def generate_descriptions(sku_codes):
    """Generate product descriptions"""
    categories = [
        "VINTAGE", "METAL", "WOODEN", "CERAMIC", "GLASS",
        "PAPER", "FABRIC", "RETRO", "JUMBO", "MINI"
    ]
    items = [
        "SIGN", "BOX", "HOLDER", "HEART", "LANTERN",
        "BUNTING", "CANDLE", "FRAME", "STORAGE", "DECORATION"
    ]
    colors = [
        "RED", "BLUE", "GREEN", "WHITE", "BLACK",
        "PINK", "CREAM", "IVORY", "SILVER", "GOLD"
    ]
    
    descriptions = {}
    for sku in sku_codes:
        cat = np.random.choice(categories)
        item = np.random.choice(items)
        color = np.random.choice(colors) if np.random.random() > 0.3 else ""
        desc = f"{cat} {color} {item}".strip()
        descriptions[sku] = desc
    
    return descriptions

def generate_baseline_prices(sku_codes):
    """Generate baseline price distribution (log-normal, realistic retail)"""
    # Prices range from £0.25 to £100, most between £1-£10
    prices = {}
    for sku in sku_codes:
        base_price = np.random.lognormal(mean=1.5, sigma=0.8)
        # Round to nearest 0.05
        price = round(base_price * 20) / 20
        price = max(0.25, min(100.0, price))
        prices[sku] = price
    return prices

def generate_transactions(n_transactions, sku_codes, baseline_prices, start_date, end_date):
    """Generate transaction records"""
    
    descriptions = generate_descriptions(sku_codes)
    
    # Create transaction data
    data = []
    invoice_counter = 100000
    
    # Generate timestamps (more activity during business hours, weekdays)
    total_seconds = int((end_date - start_date).total_seconds())
    
    for i in range(n_transactions):
        # Random timestamp with business hour bias
        random_seconds = np.random.randint(0, total_seconds)
        invoice_date = start_date + timedelta(seconds=random_seconds)
        
        # Bias toward business hours (9am - 6pm)
        hour = invoice_date.hour
        if hour < 9 or hour > 18:
            if np.random.random() > 0.3:  # 70% rejection for off-hours
                continue
        
        # Bias toward weekdays
        if invoice_date.weekday() >= 5:  # Weekend
            if np.random.random() > 0.4:  # 60% rejection for weekends
                continue
        
        invoice_id = f"C{invoice_counter}"
        invoice_counter += 1
        
        # Each invoice can have 1-5 line items
        n_items = np.random.choice([1, 2, 3, 4, 5], p=[0.6, 0.2, 0.1, 0.07, 0.03])
        
        # Select SKUs for this invoice (Zipf distribution - some SKUs very popular)
        zipf_weights = np.random.zipf(1.5, len(sku_codes))
        zipf_probs = zipf_weights / zipf_weights.sum()
        selected_skus = np.random.choice(
            sku_codes, 
            size=n_items, 
            replace=False,
            p=zipf_probs
        )
        
        customer_id = np.random.randint(10000, 10000 + NUM_CUSTOMERS)
        country = np.random.choice(
            ["United Kingdom", "Germany", "France", "Spain", "Netherlands", 
             "Belgium", "Switzerland", "Portugal", "Australia", "Japan"],
            p=[0.70, 0.08, 0.06, 0.04, 0.03, 0.02, 0.02, 0.02, 0.02, 0.01]
        )
        
        for sku in selected_skus:
            quantity = np.random.choice(
                [1, 2, 3, 4, 6, 12, 24],
                p=[0.50, 0.20, 0.12, 0.08, 0.05, 0.03, 0.02]
            )
            
            # Price with small variance (±5% from baseline)
            base_price = baseline_prices[sku]
            price_variance = np.random.uniform(-0.05, 0.05)
            price = round(base_price * (1 + price_variance), 2)
            
            data.append({
                'Invoice': invoice_id,
                'StockCode': sku,
                'Description': descriptions[sku],
                'Quantity': quantity,
                'InvoiceDate': invoice_date,
                'Price': price,
                'Customer ID': customer_id,
                'Country': country
            })
    
    return pd.DataFrame(data)

def main():
    print("Generating synthetic UCI-compatible dataset...")
    print(f"Random seed: {RANDOM_SEED}")
    print(f"Target transactions: {NUM_TRANSACTIONS}")
    
    # Generate data
    sku_codes = generate_sku_codes(NUM_SKUS)
    baseline_prices = generate_baseline_prices(sku_codes)
    
    df = generate_transactions(
        NUM_TRANSACTIONS,
        sku_codes,
        baseline_prices,
        START_DATE,
        END_DATE
    )
    
    # Sort by date (like real dataset)
    df = df.sort_values('InvoiceDate').reset_index(drop=True)
    
    print(f"Generated {len(df)} transaction records")
    print(f"Date range: {df['InvoiceDate'].min()} to {df['InvoiceDate'].max()}")
    print(f"Unique SKUs: {df['StockCode'].nunique()}")
    print(f"Unique customers: {df['Customer ID'].nunique()}")
    
    # Save as CSV (easier to work with than Excel for demo)
    output_path = '../data/raw/online_retail_II.csv'
    df.to_csv(output_path, index=False)
    print(f"Saved to: {output_path}")
    
    # Generate metadata
    metadata = {
        'generator': 'generate_synthetic_data.py',
        'random_seed': RANDOM_SEED,
        'generated_at': datetime.now().isoformat(),
        'num_records': len(df),
        'num_skus': df['StockCode'].nunique(),
        'num_customers': df['Customer ID'].nunique(),
        'date_range': {
            'start': df['InvoiceDate'].min().isoformat(),
            'end': df['InvoiceDate'].max().isoformat()
        },
        'schema': list(df.columns),
        'note': 'SYNTHETIC DATA - Production must use real UCI Online Retail II dataset'
    }
    
    with open('../data/raw/metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print("\nSample records:")
    print(df.head(10))
    
    print("\nPrice distribution:")
    print(df['Price'].describe())
    
    print("\nQuantity distribution:")
    print(df['Quantity'].describe())

if __name__ == '__main__':
    main()

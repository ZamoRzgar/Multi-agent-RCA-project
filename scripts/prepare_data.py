"""
Prepare train/val/test splits from loghub datasets.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.data_loader import LoghubDataLoader
import pandas as pd

def prepare_hdfs():
    """Prepare HDFS dataset splits."""
    print("\n" + "="*60)
    print("Preparing HDFS Dataset")
    print("="*60)
    
    loader = LoghubDataLoader(loghub_path="loghub")
    df = loader.load_dataset("HDFS", use_structured=True)
    
    # Split dataset
    train_df, val_df, test_df = loader.split_dataset(
        df,
        train_ratio=0.7,
        val_ratio=0.15,
        test_ratio=0.15,
        shuffle=True,
        random_state=42
    )
    
    # Save splits
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    train_df.to_csv(output_dir / "hdfs_train.csv", index=False)
    val_df.to_csv(output_dir / "hdfs_val.csv", index=False)
    test_df.to_csv(output_dir / "hdfs_test.csv", index=False)
    
    print(f"✓ Saved HDFS splits:")
    print(f"  - Train: {len(train_df)} logs → data/processed/hdfs_train.csv")
    print(f"  - Val:   {len(val_df)} logs → data/processed/hdfs_val.csv")
    print(f"  - Test:  {len(test_df)} logs → data/processed/hdfs_test.csv")
    
    return train_df, val_df, test_df

def prepare_bgl():
    """Prepare BGL dataset splits."""
    print("\n" + "="*60)
    print("Preparing BGL Dataset")
    print("="*60)
    
    loader = LoghubDataLoader(loghub_path="loghub")
    df = loader.load_dataset("BGL", use_structured=True)
    
    # Split dataset
    train_df, val_df, test_df = loader.split_dataset(
        df,
        train_ratio=0.7,
        val_ratio=0.15,
        test_ratio=0.15,
        shuffle=True,
        random_state=42
    )
    
    # Save splits
    output_dir = Path("data/processed")
    
    train_df.to_csv(output_dir / "bgl_train.csv", index=False)
    val_df.to_csv(output_dir / "bgl_val.csv", index=False)
    test_df.to_csv(output_dir / "bgl_test.csv", index=False)
    
    print(f"✓ Saved BGL splits:")
    print(f"  - Train: {len(train_df)} logs → data/processed/bgl_train.csv")
    print(f"  - Val:   {len(val_df)} logs → data/processed/bgl_val.csv")
    print(f"  - Test:  {len(test_df)} logs → data/processed/bgl_test.csv")
    
    return train_df, val_df, test_df

def prepare_hadoop():
    """Prepare Hadoop dataset splits."""
    print("\n" + "="*60)
    print("Preparing Hadoop Dataset")
    print("="*60)
    
    loader = LoghubDataLoader(loghub_path="loghub")
    df = loader.load_dataset("Hadoop", use_structured=True)
    
    # Split dataset
    train_df, val_df, test_df = loader.split_dataset(
        df,
        train_ratio=0.7,
        val_ratio=0.15,
        test_ratio=0.15,
        shuffle=True,
        random_state=42
    )
    
    # Save splits
    output_dir = Path("data/processed")
    
    train_df.to_csv(output_dir / "hadoop_train.csv", index=False)
    val_df.to_csv(output_dir / "hadoop_val.csv", index=False)
    test_df.to_csv(output_dir / "hadoop_test.csv", index=False)
    
    print(f"✓ Saved Hadoop splits:")
    print(f"  - Train: {len(train_df)} logs → data/processed/hadoop_train.csv")
    print(f"  - Val:   {len(val_df)} logs → data/processed/hadoop_val.csv")
    print(f"  - Test:  {len(test_df)} logs → data/processed/hadoop_test.csv")
    
    return train_df, val_df, test_df

def prepare_combined_for_kg():
    """Prepare combined dataset for KG construction."""
    print("\n" + "="*60)
    print("Preparing Combined Dataset for KG")
    print("="*60)
    
    loader = LoghubDataLoader(loghub_path="loghub")
    
    # Combine training data from all datasets
    combined = loader.prepare_for_kg(["HDFS", "BGL", "Hadoop"])
    
    # Save combined dataset
    output_dir = Path("data/processed")
    combined.to_csv(output_dir / "combined_for_kg.csv", index=False)
    
    print(f"✓ Saved combined dataset: {len(combined)} logs")
    print(f"  → data/processed/combined_for_kg.csv")
    
    return combined

def main():
    """Prepare all datasets."""
    print("="*60)
    print("Data Preparation Pipeline")
    print("="*60)
    
    # Prepare individual datasets
    hdfs_train, hdfs_val, hdfs_test = prepare_hdfs()
    bgl_train, bgl_val, bgl_test = prepare_bgl()
    hadoop_train, hadoop_val, hadoop_test = prepare_hadoop()
    
    # Prepare combined dataset for KG
    combined = prepare_combined_for_kg()
    
    print("\n" + "="*60)
    print("Data Preparation Complete!")
    print("="*60)
    print("\nSummary:")
    print(f"  HDFS:   {len(hdfs_train)} train, {len(hdfs_val)} val, {len(hdfs_test)} test")
    print(f"  BGL:    {len(bgl_train)} train, {len(bgl_val)} val, {len(bgl_test)} test")
    print(f"  Hadoop: {len(hadoop_train)} train, {len(hadoop_val)} val, {len(hadoop_test)} test")
    print(f"  Combined for KG: {len(combined)} logs")
    print("\nAll files saved to: data/processed/")
    print("\nNext: Start implementing agent logic")

if __name__ == "__main__":
    main()

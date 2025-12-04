"""
Explore loghub datasets and understand their structure.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.data_loader import LoghubDataLoader, DatasetStatistics
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def explore_hdfs():
    """Explore HDFS dataset."""
    print("\n" + "="*60)
    print("HDFS Dataset Analysis")
    print("="*60)
    
    loader = LoghubDataLoader(loghub_path="loghub")
    df = loader.load_dataset("HDFS", use_structured=True)
    
    # Basic statistics
    stats = DatasetStatistics.analyze_dataset(df)
    DatasetStatistics.print_statistics(stats)
    
    # Component distribution
    print("\nComponent Distribution:")
    print(df["Component"].value_counts())
    
    # Event template distribution
    print("\nTop 10 Event Templates:")
    print(df["EventTemplate"].value_counts().head(10))
    
    # Sample logs
    print("\nSample Logs:")
    for i in range(5):
        case = loader.extract_log_case(df, i)
        print(f"\n{i+1}. [{case['level']}] {case['component']}")
        print(f"   {case['raw_log'][:100]}...")
    
    return df

def explore_bgl():
    """Explore BGL dataset (has failure labels)."""
    print("\n" + "="*60)
    print("BGL Dataset Analysis")
    print("="*60)
    
    loader = LoghubDataLoader(loghub_path="loghub")
    df = loader.load_dataset("BGL", use_structured=True)
    
    # Basic statistics
    stats = DatasetStatistics.analyze_dataset(df)
    DatasetStatistics.print_statistics(stats)
    
    # Get failure cases
    failures = loader.get_failure_cases("BGL", max_cases=50)
    print(f"\nFound {len(failures)} failure cases")
    
    # Show sample failures
    print("\nSample Failure Cases:")
    for i, failure in enumerate(failures[:3]):
        print(f"\n{i+1}. {failure['raw_log'][:150]}...")
    
    return df

def explore_hadoop():
    """Explore Hadoop dataset."""
    print("\n" + "="*60)
    print("Hadoop Dataset Analysis")
    print("="*60)
    
    loader = LoghubDataLoader(loghub_path="loghub")
    df = loader.load_dataset("Hadoop", use_structured=True)
    
    # Basic statistics
    stats = DatasetStatistics.analyze_dataset(df)
    DatasetStatistics.print_statistics(stats)
    
    return df

def analyze_templates():
    """Analyze log templates across datasets."""
    print("\n" + "="*60)
    print("Template Analysis")
    print("="*60)
    
    loader = LoghubDataLoader(loghub_path="loghub")
    
    for dataset in ["HDFS", "BGL", "Hadoop"]:
        try:
            templates = loader.load_templates(dataset)
            print(f"\n{dataset}: {len(templates)} unique templates")
            if not templates.empty:
                print(templates.head())
        except Exception as e:
            print(f"Could not load templates for {dataset}: {e}")

def compare_datasets():
    """Compare statistics across datasets."""
    print("\n" + "="*60)
    print("Dataset Comparison")
    print("="*60)
    
    loader = LoghubDataLoader(loghub_path="loghub")
    
    datasets = ["HDFS", "BGL", "Hadoop"]
    comparison = []
    
    for name in datasets:
        try:
            df = loader.load_dataset(name, use_structured=True)
            stats = DatasetStatistics.analyze_dataset(df)
            comparison.append({
                "Dataset": name,
                "Total Logs": stats["total_logs"],
                "Unique Components": stats["unique_components"],
                "Unique Events": stats["unique_events"],
                "Unique Templates": stats["unique_templates"]
            })
        except Exception as e:
            print(f"Error loading {name}: {e}")
    
    comparison_df = pd.DataFrame(comparison)
    print("\n", comparison_df.to_string(index=False))
    
    return comparison_df

def main():
    """Run all explorations."""
    print("="*60)
    print("Loghub Data Exploration")
    print("="*60)
    
    # Explore individual datasets
    hdfs_df = explore_hdfs()
    bgl_df = explore_bgl()
    hadoop_df = explore_hadoop()
    
    # Analyze templates
    analyze_templates()
    
    # Compare datasets
    comparison = compare_datasets()
    
    print("\n" + "="*60)
    print("Exploration Complete!")
    print("="*60)
    print("\nKey Findings:")
    print("1. HDFS: Good for distributed file system failures")
    print("2. BGL: Has labeled failure cases (alerts)")
    print("3. Hadoop: MapReduce job failures")
    print("\nNext: Prepare train/val/test splits")

if __name__ == "__main__":
    main()

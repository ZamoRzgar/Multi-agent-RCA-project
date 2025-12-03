"""
Data Loader: Load and preprocess loghub datasets.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from loguru import logger


class LoghubDataLoader:
    """
    Loads and preprocesses loghub datasets for RCA experiments.
    """
    
    def __init__(self, loghub_path: str = "loghub"):
        """
        Initialize data loader.
        
        Args:
            loghub_path: Path to loghub directory
        """
        self.loghub_path = Path(loghub_path)
        logger.info(f"Initialized LoghubDataLoader: {self.loghub_path}")
    
    def load_dataset(
        self,
        dataset_name: str,
        use_structured: bool = True
    ) -> pd.DataFrame:
        """
        Load a loghub dataset.
        
        Args:
            dataset_name: Dataset name (e.g., 'HDFS', 'BGL', 'Hadoop')
            use_structured: Use pre-parsed structured CSV if available
            
        Returns:
            DataFrame with log data
        """
        dataset_path = self.loghub_path / dataset_name
        
        if not dataset_path.exists():
            raise ValueError(f"Dataset not found: {dataset_path}")
        
        if use_structured:
            # Try to load structured CSV
            structured_file = dataset_path / f"{dataset_name}_2k.log_structured.csv"
            if structured_file.exists():
                logger.info(f"Loading structured data: {structured_file}")
                df = pd.read_csv(structured_file)
                return df
        
        # Fallback to raw logs
        raw_file = dataset_path / f"{dataset_name}_2k.log"
        if raw_file.exists():
            logger.info(f"Loading raw logs: {raw_file}")
            with open(raw_file, 'r') as f:
                lines = f.readlines()
            
            df = pd.DataFrame({'raw_log': lines})
            return df
        
        raise ValueError(f"No data files found in {dataset_path}")
    
    def load_templates(self, dataset_name: str) -> pd.DataFrame:
        """
        Load log templates for a dataset.
        
        Args:
            dataset_name: Dataset name
            
        Returns:
            DataFrame with templates
        """
        template_file = self.loghub_path / dataset_name / f"{dataset_name}_2k.log_templates.csv"
        
        if template_file.exists():
            logger.info(f"Loading templates: {template_file}")
            return pd.read_csv(template_file)
        
        return pd.DataFrame()
    
    def split_dataset(
        self,
        df: pd.DataFrame,
        train_ratio: float = 0.7,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        shuffle: bool = True,
        random_state: int = 42
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Split dataset into train/val/test sets.
        
        Args:
            df: Input DataFrame
            train_ratio: Training set ratio
            val_ratio: Validation set ratio
            test_ratio: Test set ratio
            shuffle: Whether to shuffle data
            random_state: Random seed
            
        Returns:
            Tuple of (train_df, val_df, test_df)
        """
        assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-6
        
        if shuffle:
            df = df.sample(frac=1, random_state=random_state).reset_index(drop=True)
        
        n = len(df)
        train_end = int(n * train_ratio)
        val_end = train_end + int(n * val_ratio)
        
        train_df = df[:train_end]
        val_df = df[train_end:val_end]
        test_df = df[val_end:]
        
        logger.info(f"Split: train={len(train_df)}, val={len(val_df)}, test={len(test_df)}")
        
        return train_df, val_df, test_df
    
    def extract_log_case(
        self,
        df: pd.DataFrame,
        index: int
    ) -> Dict[str, Any]:
        """
        Extract a single log case for RCA.
        
        Args:
            df: DataFrame with log data
            index: Row index
            
        Returns:
            Dictionary with log case information
        """
        row = df.iloc[index]
        
        case = {
            "index": index,
            "raw_log": row.get("Content", row.get("raw_log", "")),
            "timestamp": f"{row.get('Date', '')} {row.get('Time', '')}",
            "level": row.get("Level", ""),
            "component": row.get("Component", ""),
            "event_id": row.get("EventId", ""),
            "event_template": row.get("EventTemplate", ""),
        }
        
        return case
    
    def get_failure_cases(
        self,
        dataset_name: str,
        max_cases: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get failure/anomaly cases from labeled datasets.
        
        Args:
            dataset_name: Dataset name (HDFS, BGL, etc.)
            max_cases: Maximum number of cases to return
            
        Returns:
            List of failure case dictionaries
        """
        df = self.load_dataset(dataset_name)
        
        # For BGL: filter alert messages (not starting with "-")
        if dataset_name == "BGL":
            # BGL format: first column is alert category
            df = df[df.iloc[:, 0] != "-"]
        
        # For HDFS: would need anomaly_label.csv (not in 2k sample)
        # For now, return sample cases
        
        cases = []
        for i in range(min(max_cases, len(df))):
            case = self.extract_log_case(df, i)
            cases.append(case)
        
        logger.info(f"Extracted {len(cases)} cases from {dataset_name}")
        return cases
    
    def prepare_for_kg(
        self,
        dataset_names: List[str]
    ) -> pd.DataFrame:
        """
        Prepare multiple datasets for KG construction.
        
        Args:
            dataset_names: List of dataset names
            
        Returns:
            Combined DataFrame for KG building
        """
        all_data = []
        
        for name in dataset_names:
            try:
                df = self.load_dataset(name)
                df['dataset'] = name
                all_data.append(df)
                logger.info(f"Loaded {len(df)} logs from {name}")
            except Exception as e:
                logger.warning(f"Failed to load {name}: {e}")
        
        if not all_data:
            raise ValueError("No datasets loaded")
        
        combined = pd.concat(all_data, ignore_index=True)
        logger.info(f"Combined {len(combined)} logs from {len(all_data)} datasets")
        
        return combined


class DatasetStatistics:
    """
    Compute statistics for loghub datasets.
    """
    
    @staticmethod
    def analyze_dataset(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze dataset statistics.
        
        Args:
            df: DataFrame with log data
            
        Returns:
            Dictionary with statistics
        """
        stats = {
            "total_logs": len(df),
            "unique_components": df["Component"].nunique() if "Component" in df.columns else 0,
            "unique_events": df["EventId"].nunique() if "EventId" in df.columns else 0,
            "unique_templates": df["EventTemplate"].nunique() if "EventTemplate" in df.columns else 0,
            "log_levels": df["Level"].value_counts().to_dict() if "Level" in df.columns else {},
        }
        
        return stats
    
    @staticmethod
    def print_statistics(stats: Dict[str, Any]):
        """Print dataset statistics."""
        print("\n=== Dataset Statistics ===")
        print(f"Total Logs: {stats['total_logs']:,}")
        print(f"Unique Components: {stats['unique_components']}")
        print(f"Unique Events: {stats['unique_events']}")
        print(f"Unique Templates: {stats['unique_templates']}")
        print(f"\nLog Levels:")
        for level, count in stats.get('log_levels', {}).items():
            print(f"  {level}: {count:,}")
        print("=" * 30)

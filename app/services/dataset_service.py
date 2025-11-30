import os
import logging
import pandas as pd
import json
from typing import List, Dict, Optional
from dvc.repo import Repo
from app.config import settings

logger = logging.getLogger(__name__)

class DatasetService:
    def __init__(self):
        self.datasets_dir = settings.datasets_dir
        os.makedirs(self.datasets_dir, exist_ok=True)
        try:
            self.dvc_repo = Repo(self.datasets_dir)
        except Exception as e:
            logger.warning(f"Could not initialize DVC repo: {e}")
            self.dvc_repo = None

    def list_datasets(self) -> List[Dict[str, str]]:
        datasets = []
        if not os.path.exists(self.datasets_dir):
            return datasets

        for filename in os.listdir(self.datasets_dir):
            filepath = os.path.join(self.datasets_dir, filename)
            if os.path.isfile(filepath) and (filename.endswith('.csv') or filename.endswith('.json')):
                size = os.path.getsize(filepath)
                datasets.append({
                    "name": filename,
                    "size": size,
                    "path": filepath
                })
        logger.info(f"Listed {len(datasets)} datasets")
        return datasets

    def load_dataset(self, filename: str) -> Optional[pd.DataFrame]:
        filepath = os.path.join(self.datasets_dir, filename)
        if not os.path.exists(filepath):
            logger.error(f"Dataset {filename} not found")
            return None

        try:
            if filename.endswith('.csv'):
                df = pd.read_csv(filepath)
            elif filename.endswith('.json'):
                df = pd.read_json(filepath)
            else:
                logger.error(f"Unsupported file format for {filename}")
                return None
            logger.info(f"Loaded dataset {filename}")
            return df
        except Exception as e:
            logger.error(f"Error loading dataset {filename}: {e}")
            return None

    def save_dataset(self, filename: str, data: pd.DataFrame) -> bool:
        filepath = os.path.join(self.datasets_dir, filename)
        try:
            if filename.endswith('.csv'):
                data.to_csv(filepath, index=False)
            elif filename.endswith('.json'):
                data.to_json(filepath, orient='records', indent=2)
            else:
                logger.error(f"Unsupported file format for {filename}")
                return False

            if self.dvc_repo:
                self.dvc_repo.add(filepath)
                self.dvc_repo.commit(f"Add dataset {filename}")
                logger.info(f"Saved and committed dataset {filename} to DVC")
            return True
        except Exception as e:
            logger.error(f"Error saving dataset {filename}: {e}")
            return False

    def delete_dataset(self, filename: str) -> bool:
        filepath = os.path.join(self.datasets_dir, filename)
        if not os.path.exists(filepath):
            logger.error(f"Dataset {filename} not found")
            return False

        try:
            if self.dvc_repo:
                self.dvc_repo.remove(filepath)
            os.remove(filepath)
            logger.info(f"Deleted dataset {filename}")
            return True
        except Exception as e:
            logger.error(f"Error deleting dataset {filename}: {e}")
            return False

    def get_dvc_datasets(self) -> List[str]:
        if not self.dvc_repo:
            return []
        try:
            datasets = []
            for root, dirs, files in os.walk(self.datasets_dir):
                for file in files:
                    if file.endswith('.csv') or file.endswith('.json'):
                        rel_path = os.path.relpath(os.path.join(root, file), self.datasets_dir)
                        datasets.append(rel_path)
            return datasets
        except Exception as e:
            logger.error(f"Error getting DVC datasets: {e}")
            return []


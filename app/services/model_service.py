import os
import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, List
from app.models import LinearRegressionModel, RandomForestModel, BaseMLModel
from app.services.clearml_service import ClearMLService
from app.services.dataset_service import DatasetService
from app.config import settings

logger = logging.getLogger(__name__)

class ModelService:
    _model_classes = {
        "LinearRegression": LinearRegressionModel,
        "RandomForest": RandomForestModel
    }

    def __init__(self):
        self.models: Dict[str, BaseMLModel] = {}
        self.clearml_service = ClearMLService()
        self.dataset_service = DatasetService()
        os.makedirs(settings.models_dir, exist_ok=True)

    def get_available_model_classes(self) -> List[str]:
        return list(self._model_classes.keys())

    def train_model(self, model_name: str, model_class: str, dataset_name: str, 
                   hyperparameters: Dict[str, Any], target_column: str = "target") -> bool:
        try:
            if model_class not in self._model_classes:
                logger.error(f"Unknown model class: {model_class}")
                return False

            df = self.dataset_service.load_dataset(dataset_name)
            if df is None:
                logger.error(f"Could not load dataset {dataset_name}")
                return False

            if target_column not in df.columns:
                logger.error(f"Target column {target_column} not found in dataset")
                return False

            X = df.drop(columns=[target_column]).values
            y = df[target_column].values

            model_instance = self._model_classes[model_class](hyperparameters)
            task = self.clearml_service.create_experiment(model_name, model_class, hyperparameters)
            
            model_instance.train(X, y)
            self.models[model_name] = model_instance

            self.clearml_service.save_model(task, model_instance.model, model_name, model_class)
            if task is not None:
                try:
                    task.close()
                except Exception as e:
                    logger.warning(f"Error closing ClearML task: {e}")
            
            logger.info(f"Trained model {model_name} of class {model_class}")
            return True
        except Exception as e:
            logger.error(f"Error training model {model_name}: {e}", exc_info=True)
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False

    def predict(self, model_name: str, data: np.ndarray) -> Optional[np.ndarray]:
        if model_name not in self.models:
            logger.error(f"Model {model_name} not found")
            return None

        try:
            predictions = self.models[model_name].predict(data)
            logger.info(f"Made predictions with model {model_name}")
            return predictions
        except Exception as e:
            logger.error(f"Error making predictions with model {model_name}: {e}")
            return None

    def retrain_model(self, model_name: str, model_class: str, dataset_name: str,
                     hyperparameters: Dict[str, Any], target_column: str = "target") -> bool:
        return self.train_model(model_name, model_class, dataset_name, hyperparameters, target_column)

    def delete_model(self, model_name: str) -> bool:
        if model_name in self.models:
            del self.models[model_name]
        
        success = self.clearml_service.delete_model(model_name)
        logger.info(f"Deleted model {model_name}")
        return success

    def list_models(self) -> List[Dict[str, Any]]:
        result = []
        
        clearml_models = self.clearml_service.list_models()
        clearml_model_names = {m["name"] for m in clearml_models}
        
        for model_info in clearml_models:
            result.append({
                "name": model_info["name"],
                "id": model_info["id"],
                "created": model_info["created"],
                "loaded": model_info["name"] in self.models
            })
        
        for model_name in self.models.keys():
            if model_name not in clearml_model_names:
                result.append({
                    "name": model_name,
                    "id": "local",
                    "created": "N/A",
                    "loaded": True
                })
        
        return result

    def load_model_from_clearml(self, model_name: str) -> bool:
        if model_name in self.models:
            logger.info(f"Model {model_name} is already loaded")
            return True
        
        try:
            model = self.clearml_service.load_model(model_name)
            if model is None:
                return False

            model_instance = BaseMLModel({})
            model_instance.model = model
            model_instance.is_trained = True
            self.models[model_name] = model_instance
            logger.info(f"Loaded model {model_name} from ClearML")
            return True
        except Exception as e:
            logger.error(f"Error loading model {model_name} from ClearML: {e}")
            return False


import os
import logging
from typing import Dict, Any, Optional
import joblib
from clearml import Task, Model, OutputModel
from app.config import settings

logger = logging.getLogger(__name__)

class ClearMLService:
    def __init__(self):
        self._initialize_clearml()

    def _initialize_clearml(self):
        os.environ["CLEARML_API_HOST"] = settings.clearml_api_host
        os.environ["CLEARML_WEB_HOST"] = settings.clearml_web_host
        os.environ["CLEARML_FILES_HOST"] = settings.clearml_files_host

    def create_experiment(self, model_name: str, model_class: str, hyperparameters: Dict[str, Any]) -> Optional[Task]:
        try:
            task = Task.init(
                project_name="MLOps-HW1",
                task_name=f"{model_class}_{model_name}",
                tags=[model_class, model_name]
            )
            task.connect(hyperparameters, name="hyperparameters")
            logger.info(f"Created ClearML experiment for model {model_name}")
            return task
        except Exception as e:
            logger.warning(f"Could not create ClearML experiment: {e}. Continuing without ClearML.")
            return None

    def save_model(self, task: Optional[Task], model, model_name: str, model_class: str) -> str:
        model_path = f"{settings.models_dir}/{model_name}.pkl"
        os.makedirs(settings.models_dir, exist_ok=True)
        joblib.dump(model, model_path)

        if task is not None:
            try:
                output_model = OutputModel(task=task, name=model_name, framework="scikit-learn")
                output_model.update_weights(model_path)
                output_model.set_labels({"model_class": model_class, "model_name": model_name})
                logger.info(f"Saved model {model_name} to ClearML")
            except Exception as e:
                logger.warning(f"Could not save model to ClearML: {e}. Model saved locally.")
        else:
            logger.info(f"Saved model {model_name} locally (ClearML not available)")
        return model_path

    def load_model(self, model_name: str) -> Optional[Any]:
        try:
            models = Model.query_models(project_name="MLOps-HW1", only_published=False)
            if not models:
                logger.warning(f"No models found in ClearML")
                return None
            
            matching_models = [m for m in models if m.name == model_name]
            if not matching_models:
                logger.warning(f"Model {model_name} not found in ClearML")
                return None

            model_obj = matching_models[0]
            model_path = model_obj.get_local_copy()
            model = joblib.load(model_path)
            logger.info(f"Loaded model {model_name} from ClearML")
            return model
        except Exception as e:
            logger.error(f"Error loading model {model_name} from ClearML: {e}")
            return None

    def list_models(self) -> list:
        try:
            models = Model.query_models(project_name="MLOps-HW1", only_published=False)
            return [{"name": m.name, "id": m.id, "created": str(m.created)} for m in models]
        except Exception as e:
            logger.error(f"Error listing models from ClearML: {e}")
            return []

    def delete_model(self, model_name: str) -> bool:
        try:
            models = Model.query_models(project_name="MLOps-HW1", only_published=False)
            if not models:
                return False
            
            matching_models = [m for m in models if m.name == model_name]
            if not matching_models:
                return False
            
            matching_models[0].delete()
            logger.info(f"Deleted model {model_name} from ClearML")
            return True
        except Exception as e:
            logger.error(f"Error deleting model {model_name} from ClearML: {e}")
            return False


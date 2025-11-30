from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import numpy as np
import logging
import pandas as pd
from app.services.model_service import ModelService
from app.services.dataset_service import DatasetService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MLOps HW1 API",
    description="REST API for ML model training and inference",
    version="1.0.0"
)

model_service = ModelService()
dataset_service = DatasetService()

class TrainRequest(BaseModel):
    model_name: str
    model_class: str
    dataset_name: str
    hyperparameters: Dict[str, Any]
    target_column: str = "target"

class PredictRequest(BaseModel):
    model_name: str
    data: List[List[float]]

class RetrainRequest(BaseModel):
    model_name: str
    model_class: str
    dataset_name: str
    hyperparameters: Dict[str, Any]
    target_column: str = "target"

@app.get("/")
async def root():
    return {"message": "MLOps HW1 API"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/api/v1/models/classes")
async def get_model_classes():
    classes = model_service.get_available_model_classes()
    return {"model_classes": classes}

@app.post("/api/v1/models/train")
async def train_model(request: TrainRequest):
    try:
        success = model_service.train_model(
            request.model_name,
            request.model_class,
            request.dataset_name,
            request.hyperparameters,
            request.target_column
        )
        if not success:
            raise HTTPException(
                status_code=400, 
                detail="Failed to train model. Check logs for details."
            )
        return {"message": f"Model {request.model_name} trained successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in train_model endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@app.post("/api/v1/models/predict")
async def predict(request: PredictRequest):
    try:
        data = np.array(request.data)
        predictions = model_service.predict(request.model_name, data)
        if predictions is None:
            raise HTTPException(status_code=404, detail="Model not found or prediction failed")
        return {"predictions": predictions.tolist()}
    except ValueError as e:
        logger.error(f"Value error in predict: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in predict endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

@app.post("/api/v1/models/retrain")
async def retrain_model(request: RetrainRequest):
    success = model_service.retrain_model(
        request.model_name,
        request.model_class,
        request.dataset_name,
        request.hyperparameters,
        request.target_column
    )
    if not success:
        raise HTTPException(status_code=400, detail="Failed to retrain model")
    return {"message": f"Model {request.model_name} retrained successfully"}

@app.delete("/api/v1/models/{model_name}")
async def delete_model(model_name: str):
    success = model_service.delete_model(model_name)
    if not success:
        raise HTTPException(status_code=404, detail="Model not found")
    return {"message": f"Model {model_name} deleted successfully"}

@app.get("/api/v1/models")
async def list_models():
    models = model_service.list_models()
    return {"models": models}

@app.get("/api/v1/datasets")
async def list_datasets():
    datasets = dataset_service.list_datasets()
    return {"datasets": datasets}

@app.post("/api/v1/datasets/upload")
async def upload_dataset(file: UploadFile = File(...)):
    try:
        import io
        contents = await file.read()
        file_obj = io.BytesIO(contents)
        
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file_obj)
        elif file.filename.endswith('.json'):
            df = pd.read_json(file_obj)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")
        
        success = dataset_service.save_dataset(file.filename, df)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save dataset")
        return {"message": f"Dataset {file.filename} uploaded successfully"}
    except Exception as e:
        logger.error(f"Error uploading dataset: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v1/datasets/{dataset_name}")
async def delete_dataset(dataset_name: str):
    success = dataset_service.delete_dataset(dataset_name)
    if not success:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return {"message": f"Dataset {dataset_name} deleted successfully"}

@app.post("/api/v1/models/{model_name}/load")
async def load_model(model_name: str):
    success = model_service.load_model_from_clearml(model_name)
    if not success:
        raise HTTPException(status_code=404, detail="Model not found in ClearML")
    return {"message": f"Model {model_name} loaded successfully"}


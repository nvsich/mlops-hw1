import streamlit as st
import pandas as pd
import json
import requests
import os
from typing import Dict, Any

st.set_page_config(page_title="MLOps HW1 Dashboard", layout="wide")

API_BASE_URL = os.getenv("API_BASE_URL", "http://mlops-service:8000")

def get_model_classes():
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/models/classes")
        if response.status_code == 200:
            return response.json().get("model_classes", [])
    except Exception as e:
        st.error(f"Error fetching model classes: {e}")
    return []

def list_models():
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/models")
        if response.status_code == 200:
            return response.json().get("models", [])
    except Exception as e:
        st.error(f"Error fetching models: {e}")
    return []

def list_datasets():
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/datasets")
        if response.status_code == 200:
            return response.json().get("datasets", [])
    except Exception as e:
        st.error(f"Error fetching datasets: {e}")
    return []

def train_model(model_name: str, model_class: str, dataset_name: str, 
                hyperparameters: Dict[str, Any], target_column: str):
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/models/train",
            json={
                "model_name": model_name,
                "model_class": model_class,
                "dataset_name": dataset_name,
                "hyperparameters": hyperparameters,
                "target_column": target_column
            }
        )
        return response.status_code == 200, response.json()
    except Exception as e:
        return False, {"error": str(e)}

def predict(model_name: str, data: list):
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/models/predict",
            json={
                "model_name": model_name,
                "data": data
            }
        )
        if response.status_code == 200:
            return True, response.json().get("predictions", [])
        return False, response.json()
    except Exception as e:
        return False, {"error": str(e)}

def delete_model(model_name: str):
    try:
        response = requests.delete(f"{API_BASE_URL}/api/v1/models/{model_name}")
        return response.status_code == 200
    except Exception as e:
        st.error(f"Error deleting model: {e}")
        return False

def delete_dataset(dataset_name: str):
    try:
        response = requests.delete(f"{API_BASE_URL}/api/v1/datasets/{dataset_name}")
        return response.status_code == 200
    except Exception as e:
        st.error(f"Error deleting dataset: {e}")
        return False

def upload_dataset(file, filename: str):
    try:
        file.seek(0)
        file_content = file.read()
        files = {"file": (filename, file_content, file.type if hasattr(file, 'type') else "application/octet-stream")}
        response = requests.post(f"{API_BASE_URL}/api/v1/datasets/upload", files=files)
        file.seek(0)
        return response.status_code == 200
    except Exception as e:
        st.error(f"Error uploading dataset: {e}")
        return False

def load_model_from_clearml(model_name: str):
    try:
        response = requests.post(f"{API_BASE_URL}/api/v1/models/{model_name}/load")
        return response.status_code == 200
    except Exception as e:
        st.error(f"Error loading model: {e}")
        return False

tab1, tab2, tab3 = st.tabs(["Datasets", "Training", "Inference"])

with tab1:
    st.header("Dataset Management")
    
    st.subheader("Upload Dataset")
    uploaded_file = st.file_uploader("Choose a CSV or JSON file", type=["csv", "json"])
    if uploaded_file is not None:
        if st.button("Upload"):
            if upload_dataset(uploaded_file, uploaded_file.name):
                st.success(f"Dataset {uploaded_file.name} uploaded successfully")
            else:
                st.error("Failed to upload dataset")
    
    st.subheader("Available Datasets")
    datasets = list_datasets()
    if datasets:
        df = pd.DataFrame(datasets)
        st.dataframe(df)
        
        selected_dataset = st.selectbox("Select dataset to delete", [""] + [d["name"] for d in datasets])
        if selected_dataset and st.button("Delete Dataset"):
            if delete_dataset(selected_dataset):
                st.success(f"Dataset {selected_dataset} deleted successfully")
                st.rerun()
    else:
        st.info("No datasets available")

with tab2:
    st.header("Model Training")
    
    model_classes = get_model_classes()
    if not model_classes:
        st.error("Could not fetch model classes")
    else:
        model_class = st.selectbox("Select Model Class", model_classes)
        model_name = st.text_input("Model Name")
        datasets = list_datasets()
        dataset_names = [d["name"] for d in datasets] if datasets else []
        dataset_name = st.selectbox("Select Dataset", dataset_names) if dataset_names else None
        
        if dataset_name:
            st.subheader("Hyperparameters (JSON)")
            default_hyperparameters = {
                "LinearRegression": {"fit_intercept": True, "copy_X": True},
                "RandomForest": {"n_estimators": 100, "max_depth": None, "random_state": 42}
            }
            default_json = json.dumps(default_hyperparameters.get(model_class, {}), indent=2)
            hyperparameters_json = st.text_area("Hyperparameters JSON", value=default_json, height=200)
            
            target_column = st.text_input("Target Column", value="target")
            
            if st.button("Train Model"):
                try:
                    hyperparameters = json.loads(hyperparameters_json)
                    success, response = train_model(model_name, model_class, dataset_name, 
                                                   hyperparameters, target_column)
                    if success:
                        st.success(response.get("message", "Model trained successfully"))
                    else:
                        st.error(response.get("message", "Failed to train model"))
                except json.JSONDecodeError:
                    st.error("Invalid JSON format for hyperparameters")
                except Exception as e:
                    st.error(f"Error: {e}")
    
    st.subheader("Trained Models")
    models = list_models()
    if models:
        df = pd.DataFrame(models)
        st.dataframe(df)
        
        selected_model = st.selectbox("Select model to load from ClearML (optional)", 
                                    [""] + [m["name"] for m in models])
        if selected_model and st.button("Load Model"):
            if load_model_from_clearml(selected_model):
                st.success(f"Model {selected_model} loaded successfully")
                st.rerun()
            else:
                st.warning(f"Model {selected_model} is already loaded or not found in ClearML. Local models are automatically available for inference.")
        
        selected_model_delete = st.selectbox("Select model to delete", 
                                           [""] + [m["name"] for m in models])
        if selected_model_delete and st.button("Delete Model"):
            if delete_model(selected_model_delete):
                st.success(f"Model {selected_model_delete} deleted successfully")
                st.rerun()
    else:
        st.info("No models available")

with tab3:
    st.header("Model Inference")
    
    models = list_models()
    if not models:
        st.info("No models available for inference")
    else:
        loaded_models = [m for m in models if m.get("loaded", False)]
        if not loaded_models:
            st.warning("No loaded models available. Models are automatically loaded after training.")
            st.info("If you need to load a model from ClearML, use the 'Load Model' button in the Training tab.")
        else:
            selected_model = st.selectbox("Select Model", [m["name"] for m in loaded_models])
            
            st.subheader("Input Data")
            st.info("Note: The model was trained on 3 features (feature1, feature2, feature3). Please provide 3 features for prediction.")
            input_method = st.radio("Input Method", ["Manual Entry", "CSV Upload"])
            
            if input_method == "Manual Entry":
                num_features = st.number_input("Number of Features", min_value=1, value=3)
                num_samples = st.number_input("Number of Samples", min_value=1, value=1)
                
                data = []
                for i in range(num_samples):
                    st.write(f"Sample {i+1}")
                    sample = []
                    for j in range(num_features):
                        val = st.number_input(f"Feature {j+1}", key=f"sample_{i}_feature_{j}")
                        sample.append(val)
                    data.append(sample)
            else:
                uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])
                if uploaded_file is not None:
                    df = pd.read_csv(uploaded_file)
                    st.dataframe(df)
                    data = df.values.tolist()
                else:
                    data = []
            
            if st.button("Predict") and data:
                success, result = predict(selected_model, data)
                if success:
                    st.subheader("Predictions")
                    st.write(result)
                    predictions_df = pd.DataFrame({"predictions": result})
                    st.dataframe(predictions_df)
                else:
                    error_msg = result.get('error', 'Unknown error') if isinstance(result, dict) else str(result)
                    st.error(f"Prediction failed: {error_msg}")
                    if "features" in error_msg.lower():
                        st.info("Make sure the number of features in your input matches the number of features the model was trained on (3 features).")


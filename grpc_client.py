import grpc
import json
import numpy as np
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
try:
    from app.api import grpc_api_pb2
    from app.api import grpc_api_pb2_grpc
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "grpc_tools.protoc", "-I.", "--python_out=.", "--grpc_python_out=.", "app/api/grpc_api.proto"])
    from app.api import grpc_api_pb2
    from app.api import grpc_api_pb2_grpc

def main():
    channel = grpc.insecure_channel('localhost:50051')
    stub = grpc_api_pb2_grpc.MLServiceStub(channel)

    print("Testing gRPC API")
    
    print("\n1. Health check:")
    health_response = stub.Health(grpc_api_pb2.HealthRequest())
    print(f"Status: {health_response.status}")

    print("\n2. Get model classes:")
    classes_response = stub.GetModelClasses(grpc_api_pb2.GetModelClassesRequest())
    print(f"Available classes: {list(classes_response.model_classes)}")

    print("\n3. List datasets:")
    datasets_response = stub.ListDatasets(grpc_api_pb2.ListDatasetsRequest())
    print(f"Datasets: {[d.name for d in datasets_response.datasets]}")

    print("\n4. List models:")
    models_response = stub.ListModels(grpc_api_pb2.ListModelsRequest())
    print(f"Models: {[m.name for m in models_response.models]}")

    print("\n5. Train model (example):")
    hyperparameters = {"n_estimators": 100, "max_depth": 5, "random_state": 42}
    train_request = grpc_api_pb2.TrainModelRequest(
        model_name="test_model",
        model_class="RandomForest",
        dataset_name="test_dataset.csv",
        hyperparameters_json=json.dumps(hyperparameters),
        target_column="target"
    )
    try:
        train_response = stub.TrainModel(train_request)
        print(f"Success: {train_response.success}, Message: {train_response.message}")
    except Exception as e:
        print(f"Error: {e}")

    print("\n6. Predict (example):")
    predict_request = grpc_api_pb2.PredictRequest(
        model_name="test_model",
        data=[
            grpc_api_pb2.PredictDataPoint(features=[1.0, 2.0, 3.0])
        ]
    )
    try:
        predict_response = stub.Predict(predict_request)
        print(f"Predictions: {list(predict_response.predictions)}")
    except Exception as e:
        print(f"Error: {e}")

    channel.close()

if __name__ == '__main__':
    main()


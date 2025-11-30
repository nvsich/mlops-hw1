import logging
import json
import numpy as np
from concurrent import futures
import grpc
import sys
import os

try:
    from app.api import grpc_api_pb2
    from app.api import grpc_api_pb2_grpc
except ImportError:
    import subprocess
    result = subprocess.run(
        [sys.executable, "-m", "grpc_tools.protoc", "-I.", "--python_out=.", "--grpc_python_out=.", "app/api/grpc_api.proto"],
        cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    )
    if result.returncode == 0:
        from app.api import grpc_api_pb2
        from app.api import grpc_api_pb2_grpc
    else:
        raise ImportError("Could not generate gRPC code")

from app.services.model_service import ModelService
from app.services.dataset_service import DatasetService
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MLServiceServicer(grpc_api_pb2_grpc.MLServiceServicer):
    def __init__(self):
        self.model_service = ModelService()
        self.dataset_service = DatasetService()

    def Health(self, request, context):
        return grpc_api_pb2.HealthResponse(status="healthy")

    def GetModelClasses(self, request, context):
        classes = self.model_service.get_available_model_classes()
        return grpc_api_pb2.GetModelClassesResponse(model_classes=classes)

    def TrainModel(self, request, context):
        try:
            hyperparameters = json.loads(request.hyperparameters_json)
            success = self.model_service.train_model(
                request.model_name,
                request.model_class,
                request.dataset_name,
                hyperparameters,
                request.target_column
            )
            if success:
                return grpc_api_pb2.TrainModelResponse(
                    success=True,
                    message=f"Model {request.model_name} trained successfully"
                )
            else:
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                return grpc_api_pb2.TrainModelResponse(
                    success=False,
                    message="Failed to train model"
                )
        except Exception as e:
            logger.error(f"Error in TrainModel: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            return grpc_api_pb2.TrainModelResponse(
                success=False,
                message=str(e)
            )

    def Predict(self, request, context):
        try:
            data = np.array([[point.features[i] for i in range(len(point.features))] 
                            for point in request.data])
            predictions = self.model_service.predict(request.model_name, data)
            if predictions is None:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                return grpc_api_pb2.PredictResponse()
            return grpc_api_pb2.PredictResponse(predictions=predictions.tolist())
        except Exception as e:
            logger.error(f"Error in Predict: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            return grpc_api_pb2.PredictResponse()

    def RetrainModel(self, request, context):
        try:
            hyperparameters = json.loads(request.hyperparameters_json)
            success = self.model_service.retrain_model(
                request.model_name,
                request.model_class,
                request.dataset_name,
                hyperparameters,
                request.target_column
            )
            if success:
                return grpc_api_pb2.RetrainModelResponse(
                    success=True,
                    message=f"Model {request.model_name} retrained successfully"
                )
            else:
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                return grpc_api_pb2.RetrainModelResponse(
                    success=False,
                    message="Failed to retrain model"
                )
        except Exception as e:
            logger.error(f"Error in RetrainModel: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            return grpc_api_pb2.RetrainModelResponse(
                success=False,
                message=str(e)
            )

    def DeleteModel(self, request, context):
        try:
            success = self.model_service.delete_model(request.model_name)
            if success:
                return grpc_api_pb2.DeleteModelResponse(
                    success=True,
                    message=f"Model {request.model_name} deleted successfully"
                )
            else:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                return grpc_api_pb2.DeleteModelResponse(
                    success=False,
                    message="Model not found"
                )
        except Exception as e:
            logger.error(f"Error in DeleteModel: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            return grpc_api_pb2.DeleteModelResponse(
                success=False,
                message=str(e)
            )

    def ListModels(self, request, context):
        try:
            models = self.model_service.list_models()
            model_infos = [
                grpc_api_pb2.ModelInfo(
                    name=m["name"],
                    id=m["id"],
                    created=m["created"],
                    loaded=m["loaded"]
                )
                for m in models
            ]
            return grpc_api_pb2.ListModelsResponse(models=model_infos)
        except Exception as e:
            logger.error(f"Error in ListModels: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            return grpc_api_pb2.ListModelsResponse()

    def ListDatasets(self, request, context):
        try:
            datasets = self.dataset_service.list_datasets()
            dataset_infos = [
                grpc_api_pb2.DatasetInfo(
                    name=d["name"],
                    size=d["size"],
                    path=d["path"]
                )
                for d in datasets
            ]
            return grpc_api_pb2.ListDatasetsResponse(datasets=dataset_infos)
        except Exception as e:
            logger.error(f"Error in ListDatasets: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            return grpc_api_pb2.ListDatasetsResponse()

    def LoadModel(self, request, context):
        try:
            success = self.model_service.load_model_from_clearml(request.model_name)
            if success:
                return grpc_api_pb2.LoadModelResponse(
                    success=True,
                    message=f"Model {request.model_name} loaded successfully"
                )
            else:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                return grpc_api_pb2.LoadModelResponse(
                    success=False,
                    message="Model not found in ClearML"
                )
        except Exception as e:
            logger.error(f"Error in LoadModel: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            return grpc_api_pb2.LoadModelResponse(
                success=False,
                message=str(e)
            )

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    grpc_api_pb2_grpc.add_MLServiceServicer_to_server(MLServiceServicer(), server)
    listen_addr = f'[::]:{settings.grpc_port}'
    server.add_insecure_port(listen_addr)
    server.start()
    logger.info(f"gRPC server started on {listen_addr}")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()


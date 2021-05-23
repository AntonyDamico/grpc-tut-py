from concurrent import futures
import logging
import grpc

from route_guide_pb2 import Feature, Point
import route_guide_pb2_grpc
import resources


def get_feature(feature_db, point: Point) -> Feature:
    for feature in feature_db:
        if feature.location == point:
            return feature
    return None


class RouteGuideServicer(route_guide_pb2_grpc.RouteGuideServicer):

    def __init__(self):
        self.db = resources.read_route_guide_database()

    def GetFeature(self, request, context) -> Feature:
        feature = get_feature(self.db, request)
        if feature is None:
            return Feature(name="", location=request)
        else:
            return feature


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    route_guide_pb2_grpc.add_RouteGuideServicer_to_server(
        RouteGuideServicer(), server
    )
    server.add_insecure_port('[::]:50051')
    server.start()
    print('server started')
    server.wait_for_termination()


if __name__ == '__main__':
    logging.basicConfig()
    serve()

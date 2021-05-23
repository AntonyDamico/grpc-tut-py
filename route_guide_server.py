import math
from concurrent import futures
import logging
import time

import grpc

from route_guide_pb2 import Feature, Point, RouteSummary
import route_guide_pb2_grpc
import resources


def get_feature(feature_db, point: Point) -> Feature:
    for feature in feature_db:
        if feature.location == point:
            return feature
    return None


def get_distance(start, end):
    """Distance between two points."""
    coord_factor = 10000000.0
    lat_1 = start.latitude / coord_factor
    lat_2 = end.latitude / coord_factor
    lon_1 = start.longitude / coord_factor
    lon_2 = end.longitude / coord_factor
    lat_rad_1 = math.radians(lat_1)
    lat_rad_2 = math.radians(lat_2)
    delta_lat_rad = math.radians(lat_2 - lat_1)
    delta_lon_rad = math.radians(lon_2 - lon_1)

    # Formula is based on http://mathforum.org/library/drmath/view/51879.html
    a = (pow(math.sin(delta_lat_rad / 2), 2) +
         (math.cos(lat_rad_1) * math.cos(lat_rad_2) *
          pow(math.sin(delta_lon_rad / 2), 2)))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    r = 6371000
    # metres
    return r * c


class RouteGuideServicer(route_guide_pb2_grpc.RouteGuideServicer):

    def __init__(self):
        self.db = resources.read_route_guide_database()

    def GetFeature(self, request, context) -> Feature:
        feature = get_feature(self.db, request)
        if feature is None:
            return Feature(name="", location=request)
        else:
            return feature

    def ListFeatures(self, request, context):
        left = min(request.lo.longitude, request.hi.longitude)
        right = max(request.lo.longitude, request.hi.longitude)
        top = max(request.lo.latitude, request.hi.latitude)
        bottom = min(request.lo.latitude, request.hi.latitude)
        for feature in self.db:
            if (left <= feature.location.longitude <= right and
                    bottom <= feature.location.latitude <= top):
                yield feature
                time.sleep(0.5)

    def RecordRoute(self, request_iterator, context):
        point_count = 0
        feature_count = 0
        distance = 0.0
        prev_point = None

        start_time = time.time()
        for point in request_iterator:
            point_count += 1
            if get_feature(self.db, point):
                feature_count += 1
            if prev_point:
                distance += get_distance(prev_point, point)
            prev_point = point

        elapsed_time = time.time() - start_time
        return RouteSummary(
            point_count=point_count,
            feature_count=feature_count,
            distance=int(distance),
            elapsed_time=int(elapsed_time))


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

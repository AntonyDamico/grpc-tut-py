import json
from typing import List
from route_guide_pb2 import Feature, Point


def read_route_guide_database() -> List[Feature]:
    feature_list = []
    with open("db.json") as route_guide_db_file:
        for item in json.load(route_guide_db_file):
            feature = Feature(
                name=item["name"],
                location=Point(
                    latitude=item["location"]["latitude"],
                    longitude=item["location"]["longitude"]))
            feature_list.append(feature)
    return feature_list

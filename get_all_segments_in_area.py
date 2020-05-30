"""
this code is inspired by the formulas in the following link : https://www.movable-type.co.uk/scripts/latlong.html
code for the distance : https://www.geeksforgeeks.org/program-distance-two-points-earth/
"""
import requests
from time import time
import pandas as pd
import json
from math import radians, cos, sin, asin, sqrt, atan2, degrees


class Point:
    def __init__(self, latitude, longitude):
        self.latitude = latitude
        self.longitude = longitude

    def distance(self, to):
        """"
        return value is in kilometres
        """
        lon1 = radians(self.longitude)
        lon2 = radians(to.longitude)
        lat1 = radians(self.latitude)
        lat2 = radians(to.latitude)
        # Haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))
        # Radius of earth in kilometers. Use 3956 for miles
        r = 6371
        return c * r

    def angular_distance(self, to):
        # maybe result in degres not radian
        # Radius of earth in kilometers. Use 3956 for miles
        r = 6371
        return self.distance(to) / r

    def intermediate_point(self, to, f):
        """
        :param to:
        :param f: fraction along the axis between the two points
        :return:
        """
        delta = self.angular_distance(to)
        a = sin((1 - f) * delta) / sin(delta)
        b = sin(f * delta) / sin(delta)
        x = a * cos(radians(self.latitude)) * cos(radians(self.longitude)) + b * cos(radians(to.latitude)) * cos(
            radians(to.longitude))
        y = a * cos(radians(self.latitude)) * sin(radians(self.longitude)) + b * cos(radians(to.latitude)) * sin(
            radians(to.longitude))
        z = a * sin(radians(self.latitude)) + b * sin(radians(to.latitude))
        return Point(degrees(atan2(z, sqrt(x ** 2 + y ** 2))), degrees(atan2(y, x)))


def json_to_excel_formatted(r, json_file='segment_explore_le_chesnay.json'):
    # with open(json_file, 'w+') as outfile:
    #     json.dump(r.json(), outfile)
    # df = pd.read_json(json_file)
    df = pd.read_json(r.json())
    formatted_df = pd.DataFrame()
    for field in df.at[0, 'segments'].keys():
        formatted_df[field] = pd.Series(segment[field] for segment in df['segments'])
    return formatted_df


def get_top_ten_segments(bounds):
    # bounds should be of the form :  [southwest corner latitutde, southwest corner longitude, northeast corner latitude, northeast corner longitude]
    url = "https://www.strava.com/api/v3/segments/explore"
    # find the article on how to remotely get the access token, each one is valid only for a certain amount of time
    access_token = 'access_token=7e88d046c8e68756f156e94b6b2c9b35be9c9e63'
    r = requests.get(
        url + '?' + access_token + '&' + 'bounds={}'.format(bounds))
    # return json_to_excel_formatted(r) # returns dataframe with segment fields ( id, name, type ...) as a column and corresponding segment info in the rows
    return r.json()[
        'segments']  # return dict containing info on all found segments : r.json = { segments: {{id:.., name:..}, {id:.., name:..}}}


def get_all_segments_rec(ne, sw, segment_url, token):
    # s = str(segment_url + '?' + token + '&' + 'bounds={},{},{},{}'.format(sw.latitude, sw.longitude,
    #                                                                       ne.latitude, ne.longitude))
    # print(s)
    r = requests.get(
        segment_url + '?' + token + '&' + 'bounds={},{},{},{}'.format(sw.latitude, sw.longitude,
                                                                      ne.latitude, ne.longitude))
    # print(r.json()['segments'])
    if len(r.json()['segments']) < 10:
        pass
        # strava only returns at most 10 segments per request.
        # put json retrieved segments in a common file between all recursives calls.
    else:
        # compute the two other corners poitns
        nw = Point(ne.latitude, sw.longitude)
        se = Point(sw.latitude, ne.longitude)


        nw_ne = nw.intermediate_point(ne, 0.55)
        nw_sw = nw.intermediate_point(sw, 0.55)

        se_sw = se.intermediate_point(sw, 0.55)
        se_ne = se.intermediate_point(ne, 0.55)

        get_all_segments_rec(nw_ne, nw_sw, segment_url, token)
        get_all_segments_rec(se_ne, se_sw, segment_url, token)
        get_all_segments_rec(ne, Point(nw_sw.latitude, se_sw.longitude), segment_url, token)
        get_all_segments_rec(Point(se_ne.latitude, nw_ne.longitude), sw, segment_url, token)


def get_all_segments(ne_point, sw_point):
    #it is working but i can't do more than 100 requests per 15 minutes.
    segment_url = "https://www.strava.com/api/v3/segments/explore"
    token = 'access_token=7e88d046c8e68756f156e94b6b2c9b35be9c9e63'
    get_all_segments_rec(ne_point, sw_point, segment_url, token)


def main():
    t1 = time()
    get_all_segments(Point(48.842590, 2.194751), Point(48.779203, 2.042557))
    t2 = time()
    print(t2 - t1)
    df = get_top_ten_segments([48.842590, 2.194751, 48.779203, 2.042557])
    print(df)

# -*- coding: utf-8 -*-
"""
Created on Wed Apr 22 15:24:29 2020

@author: meiro
"""
import requests
import time

class get_coordinates:
    def __init__(self, postal_code):
        # define variables based on API requirements
        self.postal_code = postal_code
        page = 1
        results = []

        while True:
            try:
                response = requests.get(
                'http://developers.onemap.sg/commonapi/search?searchVal={0}&returnGeom=Y&getAddrDetails=Y&pageNum={1}'
                .format(postal_code, page)).json()
            except requests.exceptions.ConnectionError as e:
                print('Fetching {} failed. Retrying in 2 sec'.format(postal_code))
                time.sleep(2)
                continue

            results = response['results']

            if response['totalNumPages'] > page:
                page = page + 1
            else:
                break
        return results
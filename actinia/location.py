#!/usr/bin/env python
# -*- coding: utf-8 -*-
#######
# acintia-python-client is a python client for actinia - an open source REST
# API for scalable, distributed, high performance processing of geographical
# data that uses GRASS GIS for computational tasks.
#
# Copyright (c) 2022 mundialis GmbH & Co. KG
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
#######

__license__ = "GPLv3"
__author__ = "Anika Weinmann"
__copyright__ = "Copyright 2022, mundialis GmbH & Co. KG"
__maintainer__ = "Anika Weinmann"

import json
import requests
import os
from datetime import datetime

from actinia.region import Region
from actinia.mapset import Mapset
from actinia.job import Job


class Location():

    def __init__(self, name, actinia, auth):
        self.name = name
        self.projection = None
        self.region = None
        self.__actinia = actinia
        self.__auth = auth
        self.mapsets = None

    def __request_info(self):
        """
        Requests location information
        """
        if self.__actinia.user is None:
            raise Exception("Authentication is not set.")

        url = f"{self.__actinia.url}/locations/{self.name}/info"
        resp = requests.get(url, auth=(self.__auth))
        if resp.status_code != 200:
            raise Exception(f"Error {resp.status_code}: {resp.text}")

        proc_res = json.loads(resp.text)["process_results"]
        self.projection = proc_res["projection"]
        self.region = Region(**proc_res["region"])

    def get_info(self):
        """
        Return location information
        """
        if self.projection is None or self.region is None:
            self.__request_info()
        return {"projection": self.projection, "region": self.region}

    def __request_mapsets(self):
        """
        Requests the mapsets in the given location.

        :return: A list of the mapset names
        """
        url = f"{self.__actinia.url}/locations/{self.name}/mapsets"
        resp = requests.get(url, auth=self.__auth)
        if resp.status_code != 200:
            raise Exception(f"Error {resp.status_code}: {resp.text}")

        mapset_names = json.loads(resp.text)["process_results"]
        mapsets = {
            mname: Mapset(mname, self.__actinia, self.__auth)
            for mname in mapset_names
        }
        self.mapsets = mapsets

    def get_mapsets(self):
        """
        Return location information
        """
        if self.mapsets is None:
            self.__request_mapsets()
        return self.mapsets

    # def create_mapset(self, name, epsgcode):
    #     """
    #     Creates a location with a specified projection.
    #     """
    #     url = f"{self.url}/locations/{name}"
    #     # TODO
    #     # resp = requests.post(url, auth=(self.__auth))

# * /locations/{location_name}/processing_async_export - POST (ephemeral database)
# * (/locations/{location_name}/processing_export - POST (ephemeral database))
    def create_processing_export_job(self, pc, name=None):
        """
        Creates a processing_export job with a given PC.
        """
        # set name
        now = datetime.now()
        if name is None:
            orig_name = "unkonwn_job"
            name = f"job_{now.strftime('%Y%d%m_%H%M%S')}"
        else:
            orig_name = name
            name += f"_{now.strftime('%Y%d%m_%H%M%S')}"
        # set endpoint in url
        url = f"{self.__actinia.url}/locations/{self.name}/" \
            "processing_async_export"
        # make POST request
        postkwargs = dict()
        postkwargs['headers'] = self.__actinia.headers
        postkwargs['auth'] = self.__auth
        if isinstance(pc, str):
            if os.path.isfile(pc):
                with open(pc, "r") as pc_file:
                    postkwargs['data'] = pc_file.read()
            else:
                postkwargs['data'] = pc
        elif isinstance(pc, dict):
            postkwargs['data'] = json.dumps(pc)
        else:
            raise Exception("Given process chain has no valid type.")

        try:
            actiniaResp = requests.post(url, **postkwargs)
        except requests.exceptions.ConnectionError as e:
            raise e
        # create a job
        resp = json.loads(actiniaResp.text)
        job = Job(orig_name, self.__actinia, self.__auth, **resp)
        self.__actinia.jobs[name] = job
        return job

# TODO:
# * /locations/{location_name} - POST + DELETE
# * /locations/{location_name}/info - GET
# * /locations/{location_name}/mapsets - GET
# * /locations/{location_name}/process_chain_validation_async - POST
# * /locations/{location_name}/process_chain_validation_sync - POST
# * /locations/{location_name}/processing_async_export - POST (ephemeral database)
# * (/locations/{location_name}/processing_export - POST (ephemeral database))
# * (/locations/{location_name}/processing_async_export_gcs - POST)
# * (/locations/{location_name}/processing_async_export_s3 - POST)

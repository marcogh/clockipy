#!/usr/bin/env python3

import os

# import sys
import logging
import pytz
import requests

from sys import argv
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class Clock:
    def __init__(self):
        self.get_options()
        self.initialize()

    def get_options(self) -> None:
        self._api_key = os.environ.get("API_KEY")
        self._datetime_json_format = os.environ.get("DATETIME_JSON_FORMAT")
        self._base_url = os.environ.get("CLOCKIFY_BASE_URL")
        self._timezone = os.environ.get("TIMEZONE")
        self._userid = os.environ.get("USERID")

    def initialize(self) -> None:
        self._tz = pytz.timezone(self._timezone)
        self._headers = {"X-Api-Key": self._api_key}

    def get_workspaces(self):
        return requests.get(
            f"{self._base_url}/workspaces", headers=self._headers
        ).json()

    def get_clients(self, workspace_id):
        return requests.get(
            f"{self._base_url}/workspaces/{workspace_id}/clients", headers=self._headers
        ).json()

    def get_projects(self, workspace_id, archived=False):
        return requests.get(
            f"{self._base_url}/workspaces/{workspace_id}/projects",
            params={archived: archived},
            headers=self._headers,
        ).json()

    def get_time_entries(self, workspace_id, project_id, year, month, archived=False):
        # payload = {'archived': archived}.update(self.get_time_boundaries())
        payload = self.get_time_boundaries(year, month)
        payload["project"] = project_id
        payload["page-size"] = 200,
        payload["archived"] = archived,
        logger.debug(f'payload: {payload}')
        response = requests.get(
            f"{self._base_url}/workspaces/{workspace_id}/user/{self._userid}/time-entries",
            headers=self._headers,
            params=payload,
        ).json()
        logger.debug(response)
        return response

    def get_time_boundaries(self, year, month):
        endyear = year + month//12                                                                                                
        endmonth = (month % 12) + 1
        start = datetime(year, month, 1, 0,0,0)
        end = datetime(endyear, endmonth, 1,0,0,0)
        bound = {
            "start": datetime.astimezone(start, self._tz).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "end": datetime.astimezone(end, self._tz).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        }
        logger.debug(f"time boundaries: {bound}")
        return bound

    def print_time_entry(self, start, end, duration):
        assert (start.date() == end.date()) 
        print(
            f"{datetime.astimezone(start, self._tz).strftime('%Y-%m-%d')}\t"  # date
            f"{datetime.astimezone(start, self._tz).strftime('%H:%M')}\t"  # start
            f"{datetime.astimezone(end, self._tz).strftime('%H:%M')}\t"  # end
            f"{'%d:%02d' % (duration.seconds/3600, duration.seconds%3600/60)}"  # duration
        )

    def run(self, year, month):
        self._workspaces = self.get_workspaces()
        for workspace in self._workspaces:
            # workspace_name = workspace.get('name')
            workspace_id = workspace.get("id")
            # print(f"{workspace_name} => {workspace_id}")

            # clients = self.get_clients(workspace_id)
            # for client in clients:
            #   print(f"Client {client.get('name')}:")

            projects = self.get_projects(workspace_id)
            for project in projects:
                project_total = timedelta()
                project_id = project.get("id")
                project_name = project.get("name")
                print(f"\nProject {project_name}\tid: {project_id}")

                time_entries = self.get_time_entries(workspace_id, project_id, year, month)
                # print(f"Time entries:\n {time_entries}")
                # print(f"{project}")
                for time_entry in time_entries:
                    # print(f'Time entry: {time_entry}')
                    try:
                        start = datetime.strptime(
                            time_entry.get("timeInterval").get("start"),
                            "%Y-%m-%dT%H:%M:%S%z",
                        )
                        end = datetime.strptime(
                            time_entry.get("timeInterval").get("end"), "%Y-%m-%dT%H:%M:%S%z"
                        )
                    except TypeError:
                        print(f"Failed parsing {time_entry}")
                        exit
                    duration = end - start
                    self.print_time_entry(start, end, duration)
                    project_total += duration

                print(
                    f"Project total:\t\t\t{project_total.days*24 + project_total.seconds/3600}"
                )


if __name__ == "__main__":
    clock = Clock()
    lastmonth = datetime.now() - relativedelta(months=1)
    print('running with year {}, month {}'.format(lastmonth.year, lastmonth.month))
    clock.run(lastmonth.year, lastmonth.month)

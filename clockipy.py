#!/usr/bin/env python3

import os
# import sys
import pytz
import requests
from datetime import datetime, timedelta


class Clock:
    def __init__(self):
        self.get_options()
        self.initialize()

    def get_options(self) -> None:
        self._api_key = os.environ.get('API_KEY')
        self._datetime_json_format = os.environ.get('DATETIME_JSON_FORMAT')
        self._base_url = os.environ.get('CLOCKIFY_BASE_URL')
        self._timezone = os.environ.get('TIMEZONE')
        self._userid = os.environ.get('USERID')

    def initialize(self) -> None:
        self._tz = pytz.timezone(self._timezone)
        self._headers = {'X-Api-Key': self._api_key}

    def get_workspaces(self):
        return requests.get(f'{self._base_url}/workspaces', headers=self._headers).json()

    def get_clients(self, workspace_id):
        return requests.get(f'{self._base_url}/workspaces/{workspace_id}/clients', headers=self._headers).json()

    def get_projects(self, workspace_id, archived=False):
        return requests.get(
            f'{self._base_url}/workspaces/{workspace_id}/projects',
            params={archived: archived},
            headers=self._headers
        ).json()

    def get_time_entries(self, workspace_id, project_id, archived=False):
        # payload = {'archived': archived}.update(self.get_time_boundaries())
        payload = self.get_time_boundaries()
        payload['project'] = project_id
        return requests.get(
            f"{self._base_url}/workspaces/{workspace_id}/user/{self._userid}/time-entries",
            headers=self._headers,
            params=payload
        ).json()

    @staticmethod
    def get_time_boundaries():
        return ({
            'start': "2020-02-01T00:00:00.000Z",
            'end': "2020-03-01T00:00:00.000Z"
        })

    def run(self, year, month):
        self._workspaces = self.get_workspaces()
        for workspace in self._workspaces:
            # workspace_name = workspace.get('name')
            workspace_id = workspace.get('id')
            # print(f"{workspace_name} => {workspace_id}")

            # clients = self.get_clients(workspace_id)
            # for client in clients:
                # print(f"Client {client.get('name')}:")

            projects = self.get_projects(workspace_id)
            for project in projects:
                project_total = timedelta()
                project_id = project.get('id')
                project_name = project.get('name')
                print(f"Project {project_name} with id: {project_id}")

                time_entries = self.get_time_entries(workspace_id, project_id)
                # print(f"{project}")
                for time_entry in time_entries:
                    # print(f'Time entry: {time_entry}')
                    start = datetime.strptime(time_entry.get('timeInterval').get('start'), "%Y-%m-%dT%H:%M:%S%z")
                    end = datetime.strptime(time_entry.get('timeInterval').get('end'), "%Y-%m-%dT%H:%M:%S%z")
                    duration = end - start
                    print(f"{datetime.astimezone(start, self._tz).strftime('%Y-%m-%d %H:%M')} "
                          f"{datetime.astimezone(end, self._tz).strftime('%Y-%m-%d %H:%M')} "
                          f"{duration}")
                    project_total += duration

                print(f'Project total: {project_total.days*24 + project_total.seconds/3600}')


if __name__ == '__main__':
    clock = Clock()
    clock.run(year=2020, month=2)

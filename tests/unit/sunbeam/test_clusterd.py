# Copyright (c) 2023 Canonical Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from unittest.mock import MagicMock

import pytest
from requests.exceptions import HTTPError

from sunbeam.clusterd.cluster import ClusterService
import sunbeam.clusterd.service as service
from sunbeam.commands.clusterd import (
    ClusterAddNodeStep,
    ClusterJoinNodeStep,
    ClusterInitStep,
    ClusterListNodeStep,
)
from sunbeam.jobs.common import ResultType


class TestClusterdSteps:
    """Unit tests for sunbeam clusterd steps."""

    def test_init_step(self, mocker, snap):
        mocker.patch.object(service, "Snap", return_value=snap)
        init_step = ClusterInitStep()
        init_step.client = MagicMock()
        result = init_step.run()
        assert result.result_type == ResultType.COMPLETED
        init_step.client.cluster.bootstrap.assert_called_once()

    def test_add_node_step(self, mocker, snap):
        mocker.patch.object(service, "Snap", return_value=snap)
        add_node_step = ClusterAddNodeStep(name="node-1")
        add_node_step.client = MagicMock()
        result = add_node_step.run()
        assert result.result_type == ResultType.COMPLETED
        add_node_step.client.cluster.add_node.assert_called_once_with(name="node-1")

    def test_join_node_step(self, mocker, snap):
        mocker.patch.object(service, "Snap", return_value=snap)
        join_node_step = ClusterJoinNodeStep(token="TESTTOKEN", role="control")
        join_node_step.client = MagicMock()
        result = join_node_step.run()
        assert result.result_type == ResultType.COMPLETED
        join_node_step.client.cluster.join_node.assert_called_once()

    def test_list_node_step(self, mocker, snap):
        mocker.patch.object(service, "Snap", return_value=snap)
        list_node_step = ClusterListNodeStep()
        list_node_step.client = MagicMock()
        result = list_node_step.run()
        assert result.result_type == ResultType.COMPLETED
        list_node_step.client.cluster.get_cluster_members.assert_called_once()


class TestClusterService:
    """Unit tests for ClusterService."""

    def _mock_response(
        self, status=200, content="MOCKCONTENT", json_data=None, raise_for_status=None
    ):
        mock_resp = MagicMock()
        mock_resp.status_code = status
        mock_resp.content = content

        if json_data:
            mock_resp.json.return_value = json_data

        if raise_for_status:
            mock_resp.raise_for_status.side_effect = raise_for_status

        return mock_resp

    def test_bootstrap(self, mocker, snap):
        json_data = {
            "type": "sync",
            "status": "Success",
            "status_code": 200,
            "operation": "",
            "error_code": 0,
            "error": "",
            "metadata": {},
        }
        mock_response = self._mock_response(
            status=200,
            json_data=json_data,
        )

        mock_session = MagicMock()
        mock_session.request.return_value = mock_response
        mocker.patch.object(service, "Snap", return_value=snap)

        cs = ClusterService(mock_session)
        cs.bootstrap("node-1", "10.10.1.10:7000")

    def test_bootstrap_when_node_already_exists(self, mocker, snap):
        json_data = {
            "type": "error",
            "status": "",
            "status_code": 0,
            "operation": "",
            "error_code": 500,
            "error": "Failed to initialize local remote entry: "
            'A remote with name "node-1" already exists',
            "metadata": None,
        }
        mock_response = self._mock_response(
            status=500,
            json_data=json_data,
            raise_for_status=HTTPError("Internal Error"),
        )

        mock_session = MagicMock()
        mock_session.request.return_value = mock_response
        mocker.patch.object(service, "Snap", return_value=snap)

        cs = ClusterService(mock_session)
        # with pytest.raises(service.HTTPError):
        with pytest.raises(service.NodeAlreadyExistsException):
            cs.bootstrap("node-1", "10.10.1.10:7000")

    def test_add_node(self, mocker, snap):
        json_data = {
            "type": "sync",
            "status": "Success",
            "status_code": 200,
            "operation": "",
            "error_code": 0,
            "error": "",
            "metadata": "TESTTOKEN",
        }
        mock_response = self._mock_response(
            status=200,
            json_data=json_data,
        )

        mock_session = MagicMock()
        mock_session.request.return_value = mock_response
        mocker.patch.object(service, "Snap", return_value=snap)

        cs = ClusterService(mock_session)
        token = cs.add_node("node-2")
        assert token == "TESTTOKEN"

    def test_add_node_when_node_already_exists(self, mocker, snap):
        json_data = {
            "type": "error",
            "status": "",
            "status_code": 0,
            "operation": "",
            "error_code": 500,
            "error": "UNIQUE constraint failed: internal_token_records.name",
            "metadata": None,
        }
        mock_response = self._mock_response(
            status=500,
            json_data=json_data,
            raise_for_status=HTTPError("Internal Error"),
        )

        mock_session = MagicMock()
        mock_session.request.return_value = mock_response
        mocker.patch.object(service, "Snap", return_value=snap)

        cs = ClusterService(mock_session)
        with pytest.raises(service.TokenAlreadyGeneratedException):
            cs.add_node("node-2")

    def test_join_node(self, mocker, snap):
        json_data = {
            "type": "sync",
            "status": "Success",
            "status_code": 200,
            "operation": "",
            "error_code": 0,
            "error": "",
            "metadata": {},
        }
        mock_response = self._mock_response(
            status=200,
            json_data=json_data,
        )

        mock_session = MagicMock()
        mock_session.request.return_value = mock_response
        mocker.patch.object(service, "Snap", return_value=snap)

        cs = ClusterService(mock_session)
        cs.join_node("node-2", "10.10.1.11:7000", "TESTTOKEN", "control")

    def test_join_node_with_wrong_token(self, mocker, snap):
        json_data = {
            "type": "error",
            "status": "",
            "status_code": 0,
            "operation": "",
            "error_code": 500,
            "error": "Failed to join cluster with the given join token",
            "metadata": {},
        }
        mock_response = self._mock_response(
            status=500,
            json_data=json_data,
            raise_for_status=HTTPError("Internal Error"),
        )

        mock_session = MagicMock()
        mock_session.request.return_value = mock_response
        mocker.patch.object(service, "Snap", return_value=snap)

        cs = ClusterService(mock_session)
        with pytest.raises(service.NodeJoinException):
            cs.join_node("node-2", "10.10.1.11:7000", "TESTTOKEN", "token")

    def test_join_node_when_node_already_joined(self, mocker, snap):
        json_data = {
            "type": "error",
            "status": "",
            "status_code": 0,
            "operation": "",
            "error_code": 500,
            "error": "Failed to initialize local remote entry: "
            'A remote with name "node-2" already exists',
            "metadata": None,
        }
        mock_response = self._mock_response(
            status=500,
            json_data=json_data,
            raise_for_status=HTTPError("Internal Error"),
        )

        mock_session = MagicMock()
        mock_session.request.return_value = mock_response
        mocker.patch.object(service, "Snap", return_value=snap)

        cs = ClusterService(mock_session)
        with pytest.raises(service.NodeAlreadyExistsException):
            cs.join_node("node-2", "10.10.1.11:7000", "TESTTOKEN", "control")

    def test_get_cluster_members(self, mocker, snap):
        json_data = {
            "type": "sync",
            "status": "Success",
            "status_code": 200,
            "operation": "",
            "error_code": 0,
            "error": "",
            "metadata": [
                {
                    "name": "node-1",
                    "address": "10.10.1.10:7000",
                    "certificate": "FAKECERT",
                    "role": "PENDING",
                    "schema_version": 1,
                    "last_heartbeat": "0001-01-01T00:00:00Z",
                    "status": "ONLINE",
                    "secret": "",
                }
            ],
        }
        mock_response = self._mock_response(
            status=200,
            json_data=json_data,
        )

        mock_session = MagicMock()
        mock_session.request.return_value = mock_response
        mocker.patch.object(service, "Snap", return_value=snap)

        cs = ClusterService(mock_session)
        members = cs.get_cluster_members()
        members_from_call = [m.get("name") for m in members]
        members_from_mock = [m.get("name") for m in json_data.get("metadata")]
        assert members_from_mock == members_from_call

    def test_get_cluster_members_when_cluster_not_initialised(self, mocker, snap):
        json_data = {
            "type": "error",
            "status": "",
            "status_code": 0,
            "operation": "",
            "error_code": 500,
            "error": "Daemon not yet initialized",
            "metadata": None,
        }
        mock_response = self._mock_response(
            status=500,
            json_data=json_data,
            raise_for_status=HTTPError("Internal Error"),
        )

        mock_session = MagicMock()
        mock_session.request.return_value = mock_response
        mocker.patch.object(service, "Snap", return_value=snap)

        cs = ClusterService(mock_session)
        with pytest.raises(service.ClusterServiceUnavailableException):
            cs.get_cluster_members()

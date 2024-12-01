import time

import pytest
from infra.api_client import Apiclient
from infra.utils import generate_data, run_service, wait_until_service_up, close_service, user_auth
from config import ConfigTests

base_url = ConfigTests().base_url
is_delete_container = ConfigTests().is_delete_container

@pytest.fixture
def data():
    return generate_data

class TestSanity:

    clientOne = Apiclient(base_url=base_url, headers={"Authorization": "Basic " + user_auth()})
    clientTwo = Apiclient(base_url=base_url, headers={"Authorization": "Basic " + user_auth(user="test2",password="test456")})

    @pytest.fixture(scope="class", autouse=True)
    def class_setup_teardown(self):
        run_service()
        try:
            wait_until_service_up(base_url)
        except TimeoutError:
            close_service(is_delete_container)
            raise Exception(" setup failed")
        yield
        close_service(is_delete_container)

    def test_tenant_segregation(self,data):

        response_post_ing = self.clientOne.send_post(post_fix="/integrations",json=data("integration")).assert_status(201)
        print("response - ", response_post_ing.json())

        asset = data("asset")
        asset["integration_id"] = response_post_ing.json()["id"]
        response_post_asset = self.clientOne.send_post(post_fix="/assets", json=asset).assert_status(201)
        print("response - ", response_post_asset.json())
        response_get_asset = self.clientOne.send_get(post_fix="/assets",  params={"integrationId": asset.get("integration_id")}).assert_status(200)
        print("response - ", response_get_asset.json())

        assert len(response_get_asset.json()) == 1
        assert response_post_asset.json()["id"] ==  response_get_asset.json()[0]["id"]
        assert response_post_asset.json()["integration_id"] == response_get_asset.json()[0]["integration_id"]

        self.clientTwo.send_get(post_fix="/assets"+response_post_asset.json()["id"]).assert_status(404)
        self.clientTwo.send_get(post_fix="/integrations"+response_post_ing.json()["id"]).assert_status(404)

    def test_pagination(self,data):
        ids = []
        for i in range(10):
            response_post_ing = self.clientOne.send_post(post_fix="/integrations",json=data("integration")).assert_status(201)
            ids.append(response_post_ing.json()["id"])

        for i in range(5):#got internal error for page request
            response_get_ing = self.clientOne.send_get(post_fix="/integrations", params={"page":i,"limit":2}).assert_status(200)
            assert  len(response_get_ing) == 2
            for item in response_get_ing:
                assert  item["id"] in response_get_ing

    @pytest.mark.parametrize("bad_value", [
    1,None,-1
    ])
    def test_create_ing_bad_req(self, data,bad_value):
        body = data("integration")
        body["name"] = bad_value# got internal error instad of 400 on None value
        self.clientTwo.send_post(post_fix="/integrations", json=body).assert_status(400)

    @pytest.mark.parametrize("bad_value", [
    1,None,-1
    ])
    def test_create_asset(self, data,bad_value):
        body = data("integration")
        body["name"] = bad_value# got 201 in None value should have got 400
        self.clientTwo.send_post(post_fix="/assets", json=body).assert_status(400)


class TestLoad:
    client = Apiclient(base_url=base_url, headers={"Authorization": "Basic " + user_auth()})
    @pytest.fixture(scope="class", autouse=True)
    def class_setup_teardown(self):
        run_service()
        try:
            wait_until_service_up(base_url)
        except TimeoutError:
            close_service(is_delete_container)
            raise Exception(" setup failed")
        yield
        close_service(is_delete_container)

    def test_loadtest(self,data):
        start_time = time.time()
        for i in range(1000):
            self.client.send_post(post_fix="/assets", json=data("asset")).assert_status(201)
        end_time = time.time()
        execution_time = end_time - start_time
        assert execution_time < 60



class TestCRUD:
    client = Apiclient(base_url=base_url, headers={"Authorization": "Basic " + user_auth()})
    @pytest.fixture(scope="class", autouse=True)
    def class_setup_teardown(self):
        run_service()
        try:
            wait_until_service_up(base_url)
        except TimeoutError:
            close_service(is_delete_container)
            raise Exception(" setup failed")
        yield
        close_service(is_delete_container)

    def test_create_ing(self, data):

        response_post_ing = self.client.send_post(post_fix="/integrations", json=data("integration")).assert_status(201)
        response_get_ing = self.client.send_get(post_fix="/integrations", params={"id": response_post_ing.json()["id"]} ).assert_status(200)

        assert len(response_get_ing.json()) == 1
        assert response_post_ing.json()["id"] == response_get_ing.json()[0]["id"]

    def test_create_asset(self, data):

        response_post_assets = self.client.send_post(post_fix="/assets", json=data("asset")).assert_status(201)
        response_get_asset = self.client.send_get(post_fix="/assets/" + response_post_assets.json()["id"]).assert_status(200)

        assert response_post_assets.json()["id"] == response_get_asset.json()["id"]

    def test_delete_ing(self, data):

        response_post_ing = self.client.send_post(post_fix="/integrations", json=data("integration")).assert_status(201)
        response_get_ing = self.client.send_get(post_fix="/integrations/"+response_post_ing.json()["id"],).assert_status(200)

        assert response_post_ing.json()["id"] == response_get_ing.json()["id"]

        response_delete_ing = self.client.send_delete(post_fix="/integrations/" + response_post_ing.json()["id"]).assert_status(200)

        self.client.send_get(post_fix="/integrations/" + response_post_ing.json()["id"]).assert_status(404)


    def test_delete_asset(self, data):

        response_post_assets = self.client.send_post(post_fix="/assets", json=data("asset")).assert_status(201)
        response_get_asset = self.client.send_get(post_fix="/assets/"+ response_post_assets.json()["id"]).assert_status(200)

        assert response_post_assets.json()["id"] == response_get_asset.json()["id"]

        self.client.send_delete(post_fix="/assets/" + response_post_assets.json()["id"]).assert_status(204)
        self.client.send_get(post_fix="/assets/" + response_post_assets.json()["id"]).assert_status(404)


    def test_patch_ing(self, data):

        response_post_ing = self.client.send_post(post_fix="/integrations", json=data("integration")).assert_status(201)
        response_get_ing = self.client.send_get(post_fix="/integrations/" + response_post_ing.json()["id"]).assert_status(200)
        assert response_post_ing.json()["id"] == response_get_ing.json()["id"]

        patch_json = {"name":" new name", "id": response_post_ing.json()["id"]}
        #bug integrations id not found return 404 page not found
        response_patch_ing = self.client.send_put(post_fix="/integrations", json=patch_json).assert_status(200)

        response_get_ing = self.client.send_get(post_fix="/integrations/"+ response_post_ing.json()["id"]).assert_status(200)
        assert patch_json["name"] == response_get_ing.json()["name"]

    def test_patch_asset(self, data):

        response_post_assets = self.client.send_post(post_fix="/assets", json=data("asset")).assert_status(201)
        response_get_asset = self.client.send_get(post_fix="/assets/" + response_post_assets.json()["id"]).assert_status(200)

        assert response_post_assets.json()["id"] == response_get_asset.json()["id"]

        patch_json =  response_post_assets.json()
        patch_json["name"] = "new name"
        self.client.send_patch(post_fix="/assets", json=patch_json).assert_status(200)

        response_get_assets = self.client.send_get(post_fix="/assets/" + response_post_assets.json()["id"]).assert_status(200)
        assert patch_json["name"] == response_get_assets.json()["name"]


class TestFunctionality:
    client = Apiclient(base_url=base_url, headers={"Authorization": "Basic " + user_auth()})
    @pytest.fixture(scope="class", autouse=True)
    def class_setup_teardown(self):
        run_service()
        try:
            wait_until_service_up(base_url)
        except TimeoutError:
            close_service(is_delete_container)
            raise Exception(" setup failed")
        yield
        close_service(is_delete_container)

    def test_happy_flow(self,data):

        response_post_ing = self.client.send_post(post_fix="/integrations",json=data("integration")).assert_status(201)

        asset = data("asset")
        asset["integration_id"] = response_post_ing.json()["id"]
        response_post_asset = self.client.send_post(post_fix="/assets", json=asset).assert_status(201)
        response_get_asset = self.client.send_get(post_fix="/assets",  params={"integrationId": asset.get("integration_id")}).assert_status(200)

        assert len(response_get_asset.json()) == 1
        assert response_post_asset.json()["id"] ==  response_get_asset.json()[0]["id"]
        assert response_post_asset.json()["integration_id"] == response_get_asset.json()[0]["integration_id"]

    def test_happy_flow_patch_asset(self, data):

        response_post_ing = self.client.send_post(post_fix="/integrations", json=data("integration")).assert_status(201)
        asset = data("asset")
        asset["integration_id"] = response_post_ing.json()["id"]
        response_post_asset = self.client.send_post(post_fix="/assets", json=asset).assert_status(201)

        asset["name"] =" new name"
        asset["description"] = " new description"
        asset["id"] = response_post_asset.json()["id"]# patch asset return 500 when no id
        response_patch_asset = self.client.send_patch(post_fix="/assets", json=asset).assert_status(200)
        response_get_asset = self.client.send_get(post_fix="/assets",params={"integrationId": asset.get("integration_id")}).assert_status(200)

        assert len(response_get_asset.json()) == 1
        assert response_patch_asset.json()["id"] == response_get_asset.json()[0]["id"]
        assert response_patch_asset.json()["integration_id"] == response_get_asset.json()[0]["integration_id"]
        assert response_patch_asset.json()["name"] == response_get_asset.json()[0]["name"]
        assert response_patch_asset.json()["description"] == response_get_asset.json()[0]["description"]

    def test_delete_asset(self,data):

        response_post_ing = self.client.send_post(post_fix="/integrations",json=data("integration")).assert_status(201)
        asset = data("asset")
        asset["integration_id"] = response_post_ing.json()["id"]
        response_post_asset = self.client.send_post(post_fix="/assets", json=asset).assert_status(201)

        response_get_asset = self.client.send_get(post_fix="/assets",  params={"integrationId": asset.get("integration_id")}).assert_status(200)
        assert len(response_get_asset.json()) == 1
        assert response_post_asset.json()["id"] ==  response_get_asset.json()[0]["id"]
        assert response_post_asset.json()["integration_id"] == response_get_asset.json()[0]["integration_id"]

        self.client.send_delete(post_fix="/assets/" + response_post_asset.json()["id"]).assert_status(204)

        response_get_asset = self.client.send_get(post_fix="/assets",  params={"integrationId": asset.get("integration_id")}).assert_status(200)
        assert len(response_get_asset.json()) == 0

        response_get_integrations = self.client.send_get(post_fix="/integrations",  params={"id": asset.get("integration_id")}).assert_status(200)
        assert len(response_get_integrations.json()) == 1

    def test_delete_ing(self,data):

        response_post_ing = self.client.send_post(post_fix="/integrations",json=data("integration")).assert_status(201)
        asset = data("asset")
        asset["integration_id"] = response_post_ing.json()["id"]
        response_post_asset = self.client.send_post(post_fix="/assets", json=asset).assert_status(201)

        response_get_asset = self.client.send_get(post_fix="/assets",  params={"integrationId": asset.get("integration_id")}).assert_status(200)
        assert len(response_get_asset.json()) == 1
        assert response_post_asset.json()["id"] ==  response_get_asset.json()[0]["id"]
        assert response_post_asset.json()["integration_id"] == response_get_asset.json()[0]["integration_id"]

        self.client.send_delete(post_fix="/integrations/"+ asset.get("integration_id")).assert_status(200)


        response_get_asset = self.client.send_get(post_fix="/assets",  params={"integrationId": asset.get("integration_id")}).assert_status(200)
        assert len(response_get_asset.json()) == 1# get assets returns more than one given the id while there is more then one assets
        assert None == response_get_asset.json()[0]["integration_id"]





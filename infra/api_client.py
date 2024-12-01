import requests



class AssertResponse:
    def __init__(self,response):
        self.response = response

    @property
    def json(self):
        return self.response.json

    def assert_status(self, status_code):
        assert self.response.status_code == status_code ," expected status code  " + str(status_code) + " but got" + str(self.response.status_code) + " response " + self.response.text
        return self


class Apiclient:

    def __init__(self, base_url, headers):
        self.base_url = base_url
        self.headers = headers

    def send_post(self,post_fix, json):
        response = requests.post(self.base_url + post_fix, json=json, headers=self.headers)
        return AssertResponse(response)

    def send_get(self,post_fix, params = None):
        response =  requests.get(self.base_url + post_fix, params=params, headers=self.headers)
        return AssertResponse(response)

    def send_patch(self,post_fix, json):
        response =  requests.patch(self.base_url + post_fix, json=json, headers=self.headers)
        return AssertResponse(response)

    def send_put(self,post_fix,json,params = None):
        response =  requests.put(self.base_url + post_fix, json=json,params=params, headers=self.headers)
        return AssertResponse(response)

    def send_delete(self,post_fix, params = None):
        response =  requests.delete(self.base_url + post_fix, params=params, headers=self.headers)
        return AssertResponse(response)


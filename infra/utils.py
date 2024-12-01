import requests
import base64
import docker
import time
import random
import string

client = docker.from_env()
container_id = None

def generate_random_string(length):
  letters_and_digits = string.ascii_letters + string.digits
  result_str = ''.join(random.choice(letters_and_digits) for i in range(length))

  return result_str

def wait_until_service_up(base_url):
    retries = 5
    while retries > 0:
        try:
            time.sleep(0.2)
            requests.get(url=base_url+"/swagger",timeout=1)
            return
        except Exception:
            retries -= 1

    raise  TimeoutError(" fail to connect to service ")

def run_service():
    global container_id
    container = client.containers.run(
        image='test/infralightio/test-integration-api:latest',
        detach=True,
        ports = {f"{8080}/tcp": 8080}
    )
    container_id = container.id

def close_service(is_delete_container):
    container_stop = client.containers.get(container_id)
    container_stop.stop()
    if is_delete_container:
        container_stop.remove(force=True)

def user_auth(user="test1", password="test123" ):
    text = user + ":" + password
    encoded_bytes = base64.b64encode(text.encode('utf-8'))
    encoded_string = encoded_bytes.decode('utf-8')

    return encoded_string

def generate_data(resouce_name):
    resouce_dic = \
    {"asset":
    {
      "description": generate_random_string(10),
      "integration_id":None,
      "name": generate_random_string(10)

    },"integration":{
        "id": generate_random_string(10),
        "name": generate_random_string(10),
        "tenant_id": "string",
        "type":generate_random_string(10)
    }}

    return resouce_dic[resouce_name]

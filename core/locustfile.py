from locust import HttpUser, task, between

class MyUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def get_products(self):
        self.client.get("http://127.0.0.1:8000/api/product/get_random_product/")
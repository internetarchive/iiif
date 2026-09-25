
import requests
from urllib3.util import Retry
from requests.adapters import HTTPAdapter

class TimeoutHTTPAdapter(HTTPAdapter):
    def __init__(self, *args, timeout=5, **kwargs):
        self.timeout = timeout
        super().__init__(*args, **kwargs)

    def send(self, request, **kwargs):
        if kwargs.get('timeout') is None:
            kwargs['timeout'] = self.timeout
        return super().send(request, **kwargs)

def timeout_session(timeout=1, retry=1):
    session = requests.Session()
    retries = Retry(
        total=retry,
        backoff_factor=0.1,
        status_forcelist=[502, 503, 504],
    )
    adapter = TimeoutHTTPAdapter(max_retries=retries,timeout=timeout)
    
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    return session
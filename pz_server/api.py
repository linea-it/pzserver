import requests
import json
from urllib.parse import urljoin


class PzServerApi:

    _token = None
    _base_api_url = None
    _enviroments = {
        "localhost": "http://localhost/api/",
        "pz-dev": "https://pz-server-dev.linea.org.br/api/",
        "pz": "https://pz-server.linea.org.br/api/",
    }


    def __init__(self, token, host="pz"):
        """ Initializes the Pz Server API.

        Args:
            token (str): token to access the API.
            host (str, optional): host key. Defaults to "pz".
        """

        self._base_api_url = self._enviroments[host]
        self._token = token


    @staticmethod
    def safe_list_get(l, idx, default):
        """ Gets a value from a list if it exists. Otherwise returns the default.

        Args:
            l (list): list to get the value from.
            idx (int): index of the value to get.
            default: default value to return if the value doesn't exist.

        Returns:
            value of the list by index.
        """
        try:
            return l[idx]
        except IndexError:
            return default


    def _get_request(self, url, params=None):
        """ Get a record from the API.

        Args:
            url (str): url to get
            params (dict, optional): params to get. Defaults to None.

        Returns:
            dict: data of the request.
        """

        try:
            r = requests.get(
                url,
                params=params,
                headers=dict({
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "Authorization": "Token {}".format(self._token),
                }),
            )

            if r.status_code == 200:
                return r.json()

            elif r.status_code == 403:
                # Não enviou as credenciais de usuario
                message = json.loads(str(r.text))["detail"]
                status = r.status_code
                return dict({
                    "success": False, "message": message, "status_code": status,
                })

            elif r.status_code == 404:
                # Mensagem de erro pra Not Found.
                message = r.text
                status = r.status_code
                return dict({
                    "success": False, "message": message, "status_code": status,
                })
            else:
                return dict({"success": False, "status_code": r.status_code,})

        except requests.exceptions.HTTPError as errh:
            message = "Http Error: {}".format(errh)
            return dict({"success": False, "message": message,})

        except requests.exceptions.ConnectionError as errc:
            message = "Connection Error: {}".format(errc)
            return dict({"success": False, "message": message,})

        except requests.exceptions.Timeout as errt:
            message = "Timeout Error: {}".format(errt)
            return dict({"success": False, "message": message,})

        except requests.exceptions.RequestException as err:
            message = "Request Error: {}".format(err)
            return dict({"success": False, "message": message,})


    def _post_request(self, url, payload):
        """ Posts a record to the API.

        Args:
            url (str): url to post.
            payload (str): payload to post.

        Returns:
            dict: data of the request.
        """

        try:
            r = requests.post(
                url,
                data=json.dumps(payload),
                headers=dict({
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "Authorization": "Token {}".format(self._token),
                }),
            )

            if r.status_code == 200:
                return r.json()

            elif r.status_code == 403:
                # Não enviou as credenciais de usuario
                message = json.loads(str(r.text))["detail"]
                status = r.status_code
                return dict({
                    "success": False, "message": message, "status_code": status,
                })

            elif r.status_code == 404:
                # Mensagem de erro pra Not Found.
                message = r.text
                status = r.status_code
                return dict({
                    "success": False, "message": message, "status_code": status,
                })
            else:
                return dict({"success": False, "status_code": r.status_code,})

        except requests.exceptions.HTTPError as errh:
            message = "Http Error: {}".format(errh)
            return dict({"success": False, "message": message,})

        except requests.exceptions.ConnectionError as errc:
            message = "Connection Error: {}".format(errc)
            return dict({"success": False, "message": message,})

        except requests.exceptions.Timeout as errt:
            message = "Timeout Error: {}".format(errt)
            return dict({"success": False, "message": message,})

        except requests.exceptions.RequestException as err:
            message = "Request Error: {}".format(err)
            return dict({"success": False, "message": message,})


    def _delete_request(self, url):
        """ Remove a record from the API.

        Args:
            url (str): url to delete with the record id.

        Returns:
            dict: status and message of the request.
        """
        
        try:
            r = requests.delete(
                url,
                headers=dict({
                    "Accept": "application/json",
                    "Authorization": "Token {}".format(self._token),
                }),
            )

            if r.status_code == 204:
                return True
            elif r.status_code == 400:
                return dict({
                    "success": False,
                    "message": "The server failed to perform the operation.",
                    "status_code": r.status_code,
                })
            elif r.status_code == 403:
                # Não enviou as credenciais de usuario
                message = json.loads(str(r.text))["detail"]
                status = r.status_code
                return dict({
                    "success": False, "message": message, "status_code": status,
                })
            elif r.status_code == 404:
                # Mensagem de erro pra Not Found.
                message = json.loads(str(r.text))["detail"]
                status = r.status_code
                return dict({
                    "success": False, "message": message, "status_code": status,
                })
            else:
                return dict({"success": False, "status_code": r.status_code,})

        except requests.exceptions.HTTPError as errh:
            message = "Http Error: {}".format(errh)
            return dict({"success": False, "message": message,})

        except requests.exceptions.ConnectionError as errc:
            message = "Connection Error: {}".format(errc)
            return dict({"success": False, "message": message,})

        except requests.exceptions.Timeout as errt:
            message = "Timeout Error: {}".format(errt)
            return dict({"success": False, "message": message,})

        except requests.exceptions.RequestException as err:
            message = "Request Error: {}".format(err)
            return dict({"success": False, "message": message,})


    def get_entities(self):
        """ Gets all entities from the API.

        Returns:
            list: entities list
        """

        resp = self._get_request(self._base_api_url)

        if "success" in resp and resp["success"] is False:
            return resp

        return list(resp.keys())


    def get_all(self, entity):
        """ Returns a list with all records of the entity.

        Args:
            entity (str): entity name  e.g. "releases", "products", "product-types"

        Returns:
            list: list of records 
        """

        resp = self._get_request(f"{self._base_api_url}{entity}/")

        if "success" in resp and resp["success"] is False:
            return resp

        return resp.get("results", []) 


    def get(self, entity, _id):
        """ Gets a record from the entity.

        Args:
            entity (str): entity name  e.g. "releases", "products", "product-types"
            _id (int): record id

        Returns:
            dict: record data
        """

        return self._get_request(f"{self._base_api_url}{entity}/{_id}/")
        
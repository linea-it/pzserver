"""
Classes to communicate with the Pz Server app
"""

import json

import requests


# pylint: disable=R0904
class PzRequests:
    """
    Responsible for managing all requests to the Pz Server app.
    """

    _token = None
    _base_api_url = None
    _filter_options = {}
    _mapping_filters = {
        "product_type": "product_type_name",
        "product_type__or": "product_type_name__or",
        "release": "release_name",
        "release__or": "release_name__or",
    }
    _enviroments = {
        "localhost": "http://localhost/api/",
        "pz-dev": "https://pzserver-dev.linea.org.br/api/",
        "pz": "https://pzserver.linea.org.br/api/",
    }

    def __init__(self, token, host="pz"):
        """
        Initializes communication with the Pz Server app.

        Args:
            token (str): token to access the API.
            host (str, optional): host key. Defaults to "pz".
        """

        if host in self._enviroments:
            self._base_api_url = self._enviroments[host]
        else:
            self._base_api_url = host

        self._token = token
        self._check_token()

    @staticmethod
    def safe_list_get(_list, idx, default) -> list:
        """
        Gets a value from a list if it exists. Otherwise returns the default.

        Args:
            _list (list): list to get the value from.
            idx (int): index of the value to get.
            default: default value to return if the value doesn't exist.

        Returns:
            value of the list by index.
        """

        try:
            return _list[idx]
        except IndexError:
            return default

    def _check_filters(self, entity, filters):
        """
        Checks if the filters are valid for an entity.

        Args:
            entity (str): entity name  e.g. "releases", "products", "product-types"
            filters (list): selected filters
        """

        filter_opt = self._filter_options.get(entity, None)

        if not filter_opt:
            filter_opt = self.options(entity)
            self._filter_options[entity] = filter_opt

        api_params = []

        # adds the filter_classes as acceptable attributes on the endpoint
        # for filtering entries.
        for filter_class in filter_opt.get("filter_classes", []):
            api_params.append(filter_class["name"])

        # adds the filterset_fields as acceptable attributes on the endpoint
        # for filtering entries.
        for filter_name in filter_opt.get("filterset", []):
            api_params.append(filter_name)

        # add search with acceptable parameters if configured.
        if "search" in filter_opt:
            api_params.append("search")

        for uitem in filters:
            item = self._mapping_filters.get(uitem, uitem)
            if not item in api_params:
                lib_params = self.__reverse_filters(api_params)
                raise ValueError(
                    "Invalid filter key was detected.\n"
                    "Valid filter keys are:\n  - {}".format("\n  - ".join(lib_params))
                )

    def __reverse_filters(self, api_params) -> list:
        """
        Reverts filter mapping

        Args:
            api_params (list): available filters

        Returns:
            list: filters matching
        """

        def check_filter(filter_name):
            """
            Check filter name

            Args:
                filter_name (str): filter name

            Returns:
                list: filter names
            """

            for key, value in self._mapping_filters.items():
                if filter_name == value:
                    return key
            return filter_name

        return list(set(map(check_filter, api_params)))

    def _check_response(self, api_response) -> dict:
        """
        Checks for possible HTTP errors in the response.

        Args:
            api_response (request.Response): Response object

        Returns:
            dict: response content.
        """
        status_code = api_response.status_code

        data = {
            "status_code": status_code,
            "message": str(),
            "data": str(),
            "response_object": api_response,
        }

        if 200 <= status_code < 300:
            content_type = api_response.headers.get("content-type", "")
            data.update({"success": True, "message": "Request completed"})
            if status_code != 204 and content_type.strip().startswith(
                "application/json"
            ):
                data.update({"data": api_response.json()})
        else:
            msg = api_response.text
            # msg = txt.get("detail", txt)
            # msg = txt.get("error", msg)
            data.update({"success": False, "message": msg})

        return data

    def _send_request(
        self,
        prerequest,
        stream=False,
        timeout=None,
        verify=True,
        cert=None,
        proxies=None,
    ) -> dict:
        """
        Sends PreparedRequest object.

        Args:
            prerequest (requests.PreparedRequest): PreparedRequest object
            stream (optional): Whether to stream the request content.
            timeout (float or tuple) (optional): How long to wait for the
                server to send data before giving up, as a float, or a
                (connect timeout, read timeout) tuple.
            verify (optional): Either a boolean, in which case it controls
                whether we verify the servers TLS certificate, or a string,
                in which case it must be a path to a CA bundle to use
            cert (optional): Any user-provided SSL certificate to be trusted.
            proxies (optional): The proxies dictionary to apply to the request.

        Returns:
            dict: response content
        """

        # Response example:
        # {
        #     "status_code": int,
        #     "message": str,
        #     "data": str,
        #     "success": bool,
        #     "response_object": request.Response
        # }

        data = {
            "success": False,
            "message": "",
            "response_object": None,
        }

        try:
            api_session = requests.Session()
            api_response = api_session.send(
                prerequest,
                stream=stream,
                timeout=timeout,
                verify=verify,
                cert=cert,
                proxies=proxies,
            )
            data.update(self._check_response(api_response))
        except requests.exceptions.HTTPError as errh:
            message = f"Http Error: {errh}"
            data.update(
                {
                    "success": False,
                    "message": message,
                }
            )
        except requests.exceptions.ConnectionError as errc:
            message = f"Connection Error: {errc}"
            data.update(
                {
                    "success": False,
                    "message": message,
                }
            )
        except requests.exceptions.Timeout as errt:
            message = f"Timeout Error: {errt}"
            data.update(
                {
                    "success": False,
                    "message": message,
                }
            )
        except requests.exceptions.RequestException as err:
            message = f"Request Error: {err}"
            data.update(
                {
                    "success": False,
                    "message": message,
                }
            )

        return data

    def _get_request(self, url, params=None) -> dict:
        """
        Get a record from the API.

        Args:
            url (str): url to get
            params (dict, optional): params to get. Defaults to None.

        Returns:
            dict: data of the request.
        """

        req = requests.Request(
            "GET",
            url,
            params=params,
            headers=dict(
                {
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "Authorization": f"Token {self._token}",
                }
            ),
        )
        return self._send_request(req.prepare())

    def _options_request(self, url) -> dict:
        """
        Returns the options and settings for a given endpoint.

        Args:
            url (str): url to get
            params (dict, optional): params to get. Defaults to None.

        Returns:
            dict: data of the request.
        """
        req = requests.Request(
            "OPTIONS",
            url,
            headers=dict(
                {
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "Authorization": f"Token {self._token}",
                }
            ),
        )
        return self._send_request(req.prepare())

    def _check_token(self):
        """
        Checks if the token is valid, otherwise stops class
        initialization.

        """

        cntxt = self._get_request(self._base_api_url)

        if not cntxt.get("success", True):
            stcode = cntxt.get("status_code")
            msg = cntxt.get("message", "Unforeseen error")
            raise requests.exceptions.RequestException(f"Status code {stcode}: {msg}")

    def _download_request(self, url, save_in="."):
        """
        Download a record from the API.

        Args:
            url (str): url to get
            save_in (str): location where the file will be saved
        """

        req = requests.Request(
            "GET",
            url,
            headers=dict(
                {
                    "Authorization": f"Token {self._token}",
                }
            ),
        )
        data = self._send_request(req.prepare(), stream=True)

        if data.get("success", False):
            resp_obj = data.get("response_object", None)
            filename = resp_obj.headers.get("Content-Disposition", "")
            filename = filename.split("filename=")[1]
            filename = f"{save_in}/{filename}"

            with open(filename, "wb") as filedown:
                for chunk in resp_obj.iter_content(chunk_size=128):
                    filedown.write(chunk)

            data.update({"message": filename})
            return data

        return data

    def _patch_request(self, url, data) -> dict:
        """
        Patchs a record to the API.

        Args:
            url (str): url to patch.
            data (str): data to patch.

        Returns:
            dict: data of the request.
        """

        req = requests.Request(
            "PATCH",
            url,
            # data=json.dumps(data),
            data=data,
            headers=dict(
                {
                    # "Accept": "application/json",
                    # "Content-Type": "application/json",
                    "Authorization": f"Token {self._token}",
                }
            ),
        )

        return self._send_request(req.prepare())

    def _upload_request(self, url, payload, upload_files=None) -> dict:
        """
        Posts a record to the API.

        Args:
            url (str): url to post.
            payload (str): payload to post.

        Returns:
            dict: data of the request.
        """

        files = {}

        if upload_files:
            for key, value in upload_files.items():
                files[key] = open(value, "rb")  # pylint: disable=consider-using-with

        req = requests.Request(
            "POST",
            url,
            data=payload,
            files=files,
            headers=dict(
                {
                    "Authorization": f"Token {self._token}",
                }
            ),
        )
        return self._send_request(req.prepare())

    def _post_request(self, url, payload) -> dict:
        """
        Posts a record to the API.

        Args:
            url (str): url to post.
            payload (str): payload to post.

        Returns:
            dict: data of the request.
        """

        req = requests.Request(
            "POST",
            url,
            data=json.dumps(payload),
            headers=dict(
                {
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "Authorization": f"Token {self._token}",
                }
            ),
        )
        return self._send_request(req.prepare())

    def _delete_request(self, url) -> dict:
        """
        Remove a record from the API.

        Args:
            url (str): url to delete with the record id.

        Returns:
            dict: status and message of the request.
        """

        req = requests.Request(
            "DELETE",
            url,
            headers=dict(
                {
                    "Accept": "application/json",
                    "Authorization": f"Token {self._token}",
                }
            ),
        )
        resp = self._send_request(req.prepare())

        if resp.get("status_code") == 400:
            return dict(
                {
                    "success": False,
                    "message": "The server failed to perform the operation.",
                    "status_code": 400,
                }
            )

        return resp

    def get_entities(self) -> list:
        """
        Gets all entities from the API.

        Returns:
            list: entities list
        """

        resp = self._get_request(self._base_api_url)

        if "success" in resp and resp["success"] is False:
            raise requests.exceptions.RequestException(resp["message"])

        return list(resp.keys())

    def get_all(self, entity, ordering=None) -> list:
        """
        Returns a list with all records of the entity.

        Args:
            entity (str): entity name  e.g. "releases", "products", "product-types"
            ordering (None or str): column name to be ordered

        Returns:
            list: list of records
        """

        uri = f"{self._base_api_url}{entity}/"

        if ordering:
            uri += f"?ordering={ordering}"

        resp = self._get_request(uri)

        if "success" in resp and resp["success"] is False:
            raise requests.exceptions.RequestException(resp["message"])

        return resp.get("data").get("results")

    def get(self, entity, _id) -> dict:
        """
        Gets a record from the entity.

        Args:
            entity (str): entity name  e.g. "releases", "products", "product-types"
            _id (int): record id

        Returns:
            dict: record metadata
        """

        data = self._get_request(f"{self._base_api_url}{entity}/{_id}/")

        if "success" in data and data["success"] is False:
            raise requests.exceptions.RequestException(data["message"])

        return data.get("data")

    def get_by_name(self, entity, name) -> dict:
        """
        Gets a record from the entity by name.

        Args:
            entity (str): entity name  e.g. "releases", "products", "product-types"
            _id (int): record id

        Returns:
            dict: record metadata
        """

        data = self.get_by_attribute(entity, "name", name)

        nobj = data.get("count")
        if nobj > 1:
            raise requests.exceptions.RequestException(
                f"The return should be unique [return = {nobj} objects]"
            )

        result = data.get("results")
        return result[0] if result else None

    def get_by_attribute(self, entity, attribute, value) -> dict:
        """
        Gets a record from the entity by some attribute.

        Args:
            entity (str): entity name  e.g. "releases", "products", "product-types"
            attribute (str): entity field
            value (str): entity field value

        Returns:
            dict: record metadata
        """

        data = self._get_request(f"{self._base_api_url}{entity}/?{attribute}={value}")

        if "success" in data and data["success"] is False:
            raise requests.exceptions.RequestException(data["message"])

        return data.get("data")

    def options(self, entity) -> dict:
        """
        Gets options (filters, search and ordering) from the entity.

        Args:
            entity (str): entity name  e.g. "releases", "products", "product-types"

        Returns:
            dict: options metadata (filters, search and ordering).
        """

        opt = self._options_request(f"{self._base_api_url}{entity}/")
        if "success" in opt and opt["success"] is False:
            raise requests.exceptions.RequestException(opt["message"])

        return opt.get("data")

    def download_main_file(self, _id, save_in="."):
        """
        Gets the contents uploaded by the user for a given record.

        Args:
            _id (int): record id
            save_in (str): location where the file will be saved

        Returns:
            dict: record data
        """

        return self._download_request(
            f"{self._base_api_url}products/{_id}/download_main_file/", save_in
        )

    def get_product_files(self, product_id) -> list:
        """
        Gets all files from a product.

        Args:
            product_id (int): product id

        Returns:
            list: list of files
        """

        data = self._get_request(
            f"{self._base_api_url}product-files/?product_id={product_id}"
        )

        if "success" in data and data["success"] is False:
            raise requests.exceptions.RequestException(data["message"])

        return data.get("data").get("results")

    def delete_product_file(self, file_id) -> None:
        """
        Deletes a file from a product.

        Args:
            file_id (int): file id
        """

        data = self._delete_request(f"{self._base_api_url}product-files/{file_id}/")

        if "success" in data and data["success"] is False:
            raise requests.exceptions.RequestException(data["message"])

        return data.get("data")

    def delete_product(self, product_id) -> None:
        """
        Deletes a product.

        Args:
            product_id (int): product id
        """

        data = self._delete_request(f"{self._base_api_url}products/{product_id}/")

        if "success" in data and data["success"] is False:
            raise requests.exceptions.RequestException(data["message"])

        return data.get("data")

    def get_main_file_info(self, _id, column_association=True) -> dict:
        """
        Returns information about the main product file.

        Args:
            _id (int): record id

        Returns:
            dict: record data
        """

        resp = self._get_request(
            f"{self._base_api_url}products/{_id}/main_file_info/",
        )

        if "success" in resp and resp["success"] is False:
            raise requests.exceptions.RequestException(resp["message"])

        data = resp.get("data").get("main_file")

        if column_association:
            assoc = self._get_request(
                f"{self._base_api_url}product-contents/?product={_id}",
            )
            if assoc.get("success", False):
                data["columns_association"] = assoc.get("data").get("results")

        return data

    def download_product(self, _id, save_in="."):
        """
        Downloads the product to local

        Args:
            _id (int): record id
            save_in (str): location where the file will be saved

        Returns:
            dict: record data
        """

        return self._download_request(
            f"{self._base_api_url}products/{_id}/download/", save_in
        )

    def start_process(self, data):
        """
        Start process in Pz Server

        Args:
            data (dict): data process

        Returns:
            dict: record data
        """

        process = self._post_request(f"{self._base_api_url}processes/", payload=data)

        if "success" in process and process["success"] is False:
            raise requests.exceptions.RequestException(process["message"])

        return process.get("data")

    def stop_process(self, process_id):
        """
        Stop process in Pz Server

        Args:
            process_id (int): process ID
        """

        data = self._get_request(f"{self._base_api_url}processes/{process_id}/stop/")

        if "success" in data and data["success"] is False:
            raise requests.exceptions.RequestException(data["message"])

        return data.get("data")

    def upload_basic_info(
        self, name, product_type, release=None, pz_code=None, description=None
    ):
        """
        Upload product with basic informations

        Args:
            name (str):
            product_type (int):
            release (int):
            pz_code (str):
            description (str):

        Returns:
            dict: record data
        """

        if product_type:
            prodtype_obj = self.get_by_name("product-types", product_type)
            if not prodtype_obj:
                raise ValueError(f"Product type not found: {product_type}")
            product_type = prodtype_obj.get("id")

        if release:
            release_obj = self.get_by_name("releases", release)
            if not release_obj:
                raise ValueError(f"Release not found: {release}")
            release = release_obj.get("id")

        upload_data = {
            "display_name": name,
            "product_type": product_type,
            "release": release,
            "official_product": False,
            "pz_code": pz_code,
            "description": description,
            "status": 0,  # status 0 is registering
        }

        upload = self._post_request(
            f"{self._base_api_url}products/", payload=upload_data
        )

        if "success" in upload and upload["success"] is False:
            raise requests.exceptions.RequestException(upload["message"])

        return upload.get("data")

    def upload_file(self, product_id, filepath, role, mimetype=None):
        """Upload file

        Args:
            product_id (int): product id
            filepath (str): filepath
            role (str): file role
            mimetype (str, optional): file mimetype. Defaults to None.
        """

        file_roles = {
            "main": 0,
            "description": 1,
            "auxiliary": 2,
        }

        upload_file_data = {
            "product": product_id,
            "role": file_roles.get(role),
            "type": mimetype,
        }

        files = {"file": filepath}

        upload = self._upload_request(
            f"{self._base_api_url}product-files/",
            payload=upload_file_data,
            upload_files=files,
        )

        if "success" in upload and upload["success"] is False:
            raise requests.exceptions.RequestException(upload["message"])

        return upload.get("data")

    def registry_upload(self, product_id):
        """Registry upload

        Args:
            id (int): product id
        """
        data = self._get_request(f"{self._base_api_url}products/{product_id}/registry/")

        if "success" in data and data["success"] is False:
            raise requests.exceptions.RequestException(data["message"])

        return data.get("data")

    def update_upload_column(self, id_attr, data):
        """Update upload column

        Args:
            id_attr (int): attribute id
            data (dict): attribute that will be updated
        """

        update = self._patch_request(
            f"{self._base_api_url}product-contents/{id_attr}/", data=data
        )

        if "success" in update and update["success"] is False:
            raise requests.exceptions.RequestException(update["message"])

        return update.get("data")

    def finish_upload(self, product_id):
        """Finish upload

        Args:
            product_id (int): product id
        """
        data = {"status": 1}

        update = self._patch_request(
            f"{self._base_api_url}products/{product_id}/", data=data
        )

        if "success" in update and update["success"] is False:
            raise requests.exceptions.RequestException(update["message"])

        return update.get("data")

    def update_product_description(self, product_id, description):
        """Update product description

        Args:
            product_id (int): product id
            description (str): description
        """

        data = {"description": description}

        update = self._patch_request(
            f"{self._base_api_url}products/{product_id}/", data=data
        )

        if "success" in update and update["success"] is False:
            raise requests.exceptions.RequestException(update["message"])

        return update.get("data")

    def get_products(self, filters=None, status=1) -> list:
        """
        Returns list of products according to a filter

        Args:
            filters (dict): products filter   ex: {'release': 'LSST'}
            status (int): products status (1 is viewing only completed products)

        Returns:
            list: list of records
        """

        url = f"{self._base_api_url}/products/?"

        if status:
            url += f"status={str(status)}"

        if filters:
            self._check_filters("products", filters)
            for key, value in filters.items():
                value = (
                    list(map(str, value)) if isinstance(value, list) else [str(value)]
                )
                key = self._mapping_filters.get(key, key)
                url += f"&{key}={','.join(value)}"

        resp = self._get_request(url)

        if "success" in resp and resp["success"] is False:
            raise requests.exceptions.RequestException(resp["message"])

        return resp.get("data").get("results")

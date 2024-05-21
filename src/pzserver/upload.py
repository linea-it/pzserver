""" 
Classes responsible for managing user interaction 
"""

import dataclasses
from typing import Optional

from .communicate import PzRequests

FONTCOLORERR = "\033[38;2;255;0;0m"
FONTCOLOREND = "\033[0m"


@dataclasses.dataclass
class Upload:
    """_summary_
    """
    name: str
    product_type: str
    main_file: str
    release: Optional[str] = None
    pz_code: Optional[str] = None
    auxiliary_files: Optional[list] = []
    description: Optional[str] = None


class PzUpload:
    """
    Responsible for managing user interactions with upload.
    """

    def __init__(self, upload: Upload, token: Optional[str]=None,
                 host: Optional[str]="pz"):
        """
        PzUpload class constructor

        Args:
            upload (Upload)
            token (str): user's token generated on the PZ Server website
            host (str): "pz" (production) or
                        "pz-dev" (test environment) or
                        "localhost" (dev environment) or
                        "api url"
        """

        if token is None:
            raise ValueError(
                f"{FONTCOLORERR}Please provide a valid token.{FONTCOLOREND}"
            )

        self._token = token
        self.api = PzRequests(self._token, host)
        self.upload = upload
        self.__save_basic_info()

        self.__save_upload_files()

    def add_columns_association(self):
        """_summary_
        """
        pass

    def __save_basic_info(self):
        """_summary_
        """
        self.api.upload_basic_info(
            self.upload.name,
            self.upload.product_type,
            self.upload.release,
            self.upload.pz_code,
            self.upload.description
        )

    def __save_upload_files(self):
        """_summary_
        """
        pass

    def save(self):
        """_summary_
        """
        pass

import logging
import os
from typing import Protocol

import boto3
from botocore import exceptions as botocore_exceptions
from jinja2 import Environment, FileSystemLoader

from reshal_api.config import get_config

logger = logging.getLogger(__name__)

config = get_config()


class EmailError(Exception):
    ...


class TemplatesService:
    TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")

    def __init__(self, templates_dir: str | None = None) -> None:
        if templates_dir is None:
            templates_dir = TemplatesService.TEMPLATES_DIR

        self.templates_path = templates_dir
        self.environment = Environment(loader=FileSystemLoader(self.templates_path))

    def create_reservation_successfull_content(
        self,
        first_name: str,
        facility_name: str,
        start_time: str,
        end_time: str,
        price: str,
    ) -> str:
        template = self.environment.get_template("reservation_created.html")
        rendered_string = template.render(
            {
                "first_name": first_name,
                "facility_name": facility_name,
                "start_time": start_time,
                "end_time": end_time,
                "price": price,
            }
        )

        return rendered_string


class EmailService(Protocol):
    def send_email(self, to: str, subject: str, content: str) -> None:
        ...


class SESEmailService:
    sender: str = "admin@bartoszmagiera.dev"

    def __init__(self, access_key: str, secret_key: str) -> None:
        self.client = boto3.client(
            "ses",
            region_name=config.AWS_REGION,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )

    def send_email(self, to: str, subject: str, content: str) -> None:
        send_kwargs = {
            "Source": self.sender,
            "Destination": {"ToAddresses": [to]},
            "Message": {
                "Subject": {"Data": subject},
                "Body": {"Html": {"Charset": "UTF-8", "Data": content}},
            },
        }
        if not config.ENVIRONMENT.is_production or to not in config.EMAIL_WHITELIST:
            logger.info(f"Would sent an email {send_kwargs=}")
            return None

        try:
            response = self.client.send_email(**send_kwargs)
            logger.info(f"Sent email {response['MessageId']}")
        except botocore_exceptions.ClientError as e:
            logger.error(f"Error while sending an email {send_kwargs=}")
            raise EmailError() from e

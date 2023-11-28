from typing import Annotated

from fastapi import Depends

from reshal_api.config import get_config

from .service import EmailService as EmailService_
from .service import SESEmailService
from .service import TemplatesService as TemplatesService_

config = get_config()


def get_email_service() -> EmailService_:
    return SESEmailService(config.AWS_ACCESS_KEY, config.AWS_SECRET_KEY)


def get_templates_service() -> TemplatesService_:
    return TemplatesService_()


EmailService = Annotated[EmailService_, Depends(get_email_service)]
TemplatesService = Annotated[TemplatesService_, Depends(get_templates_service)]

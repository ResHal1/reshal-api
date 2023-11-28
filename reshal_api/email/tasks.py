from datetime import datetime
from decimal import Decimal

from .service import EmailService, TemplatesService


def send_reservation_confirmation(
    email_service: EmailService,
    templates_service: TemplatesService,
    to: str,
    first_name: str,
    facility_name: str,
    start_time: datetime,
    end_time: datetime,
    price: Decimal,
) -> None:
    content = templates_service.create_reservation_successfull_content(
        first_name=first_name,
        facility_name=facility_name,
        start_time=start_time.strftime("%Y-%m-%d %H:%M"),
        end_time=end_time.strftime("%Y-%m-%d %H:%M"),
        price="${:,.2f}".format(price),
    )
    subject = "Reshal: Reservation created"
    email_service.send_email(to=to, subject=subject, content=content)

"""Email sending utilities for notifications."""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from wedding_api.config import settings
from wedding_api.utils.email_translations import get_translation

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SMTP."""

    def __init__(self) -> None:
        """Initialize email service."""
        self.enabled = settings.email_enabled
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_username = settings.smtp_username
        self.smtp_password = settings.smtp_password
        self.smtp_use_tls = settings.smtp_use_tls
        self.from_address = settings.email_from_address
        self.from_name = settings.email_from_name

    def _create_message(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: str | None = None,
    ) -> MIMEMultipart:
        """Create email message."""
        msg = MIMEMultipart("alternative")
        msg["From"] = f"{self.from_name} <{self.from_address}>"
        msg["To"] = to_email
        msg["Subject"] = subject

        if text_body:
            msg.attach(MIMEText(text_body, "plain"))

        msg.attach(MIMEText(html_body, "html"))

        return msg

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: str | None = None,
    ) -> bool:
        """Send an email."""
        if not self.enabled:
            logger.info("Email disabled; not sending")
            return True

        if not self.smtp_username or not self.smtp_password:
            logger.warning("Email credentials not configured")
            return False

        try:
            msg = self._create_message(to_email, subject, html_body, text_body)

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_use_tls:
                    server.starttls()

                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

            logger.info("Email sent successfully")
            return True

        except smtplib.SMTPAuthenticationError:
            logger.error("SMTP authentication failed. Check credentials.")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error sending email: {type(e).__name__}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending email: {type(e).__name__}")
            return False

    async def send_rsvp_confirmation(
        self,
        guest_email: str | None,
        guest_name: str,
        confirmation_number: str,
        attending: bool,
        rsvp_details: dict[str, Any],
        language: str = "en",
    ) -> bool:
        """Send RSVP confirmation email to guest."""
        subject = get_translation("rsvp_confirmed" if attending else "rsvp_received", language)

        html_body = self._generate_rsvp_confirmation_html(
            guest_name=guest_name,
            confirmation_number=confirmation_number,
            attending=attending,
            rsvp_details=rsvp_details,
            language=language,
        )

        text_body = self._generate_rsvp_confirmation_text(
            guest_name=guest_name,
            confirmation_number=confirmation_number,
            attending=attending,
            rsvp_details=rsvp_details,
            language=language,
        )

        if not guest_email:
            logger.info("No guest email provided; skipping confirmation email")
            return True
        return await self.send_email(guest_email, subject, html_body, text_body)

    async def send_admin_notification(
        self,
        guest_name: str,
        attending: bool,
        rsvp_details: dict[str, Any],
    ) -> bool:
        """
        Send the admin a short notice about a new RSVP.

        Mailboxes are kept for years and pass through other providers, so the notice says only who answered and
        how many are coming. Contact details, dietary needs and messages stay in the admin panel.
        """
        if not settings.admin_email:
            logger.warning("Admin email not configured")
            return False

        status = "ATTENDING" if attending else "NOT ATTENDING"
        subject = f"New RSVP: {guest_name} - {status}"

        html_body = self._generate_admin_notification_html(guest_name=guest_name, attending=attending, rsvp_details=rsvp_details)
        text_body = self._generate_admin_notification_text(guest_name=guest_name, attending=attending, rsvp_details=rsvp_details)

        return await self.send_email(settings.admin_email, subject, html_body, text_body)

    def _generate_rsvp_confirmation_html(
        self,
        guest_name: str,
        confirmation_number: str,
        attending: bool,
        rsvp_details: dict[str, Any],
        language: str = "en",
    ) -> str:
        """Generate HTML for RSVP confirmation email."""
        status_color = "#4CAF50" if attending else "#9E9E9E"
        status_text = get_translation("excited_celebrate" if attending else "will_miss_you", language)
        status_label = get_translation("attending" if attending else "not_attending", language)

        plus_one_html = ""
        if attending and rsvp_details.get("plus_one"):
            plus_one_html = f"""
            <tr>
                <td style="padding: 8px 0;">
                    <strong>{get_translation("plus_one", language)}:</strong> {get_translation("yes", language)}
                </td>
            </tr>
            """

        dietary_html = ""
        if attending and rsvp_details.get("dietary_restrictions"):
            dietary_html = f"""
            <tr>
                <td style="padding: 8px 0;">
                    <strong>{get_translation("dietary_restrictions", language)}:</strong> {rsvp_details["dietary_restrictions"]}
                </td>
            </tr>
            """

        message_html = ""
        if rsvp_details.get("message"):
            message_html = f"""
            <tr>
                <td style="padding: 8px 0;">
                    <strong>{get_translation("your_message", language)}:</strong><br>
                    <em>{rsvp_details["message"]}</em>
                </td>
            </tr>
            """

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f5f5f5;">
            <table cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color: #f5f5f5; padding: 40px 20px;">
                <tr>
                    <td align="center">
                        <table cellpadding="0" cellspacing="0" border="0" width="600" style="background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                            <!-- Header -->
                            <tr>
                                <td style="padding: 40px 40px 20px; text-align: center; background-color: {status_color}; border-radius: 8px 8px 0 0;">
                                    <h1 style="margin: 0; color: #ffffff; font-size: 28px;">{get_translation("rsvp_confirmed", language)}</h1>
                                </td>
                            </tr>

                            <!-- Content -->
                            <tr>
                                <td style="padding: 40px;">
                                    <p style="font-size: 16px; line-height: 1.6; color: #333333; margin: 0 0 20px;">
                                        {get_translation("dear", language)} {guest_name},
                                    </p>

                                    <p style="font-size: 16px; line-height: 1.6; color: #333333; margin: 0 0 20px;">
                                        {get_translation("thank_you_rsvp", language)} {status_text}
                                    </p>

                                    <!-- RSVP Details -->
                                    <table cellpadding="0" cellspacing="0" border="0" width="100%" style="margin: 30px 0; border: 1px solid #e0e0e0; border-radius: 4px;">
                                        <tr>
                                            <td style="padding: 20px; background-color: #fafafa;">
                                                <table cellpadding="0" cellspacing="0" border="0" width="100%">
                                                    <tr>
                                                        <td style="padding: 8px 0;">
                                                            <strong>{get_translation("confirmation_number", language)}:</strong> {confirmation_number}
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <td style="padding: 8px 0;">
                                                            <strong>{get_translation("status", language)}:</strong> <span style="color: {status_color};">{status_label}</span>
                                                        </td>
                                                    </tr>
                                                    {plus_one_html}
                                                    {dietary_html}
                                                    {message_html}
                                                </table>
                                            </td>
                                        </tr>
                                    </table>

                                    <p style="font-size: 16px; line-height: 1.6; color: #333333; margin: 20px 0 0;">
                                        {get_translation("changes_contact", language)}
                                    </p>

                                    <p style="font-size: 16px; line-height: 1.6; color: #333333; margin: 20px 0 0;">
                                        {get_translation("with_love", language)},<br>
                                        {get_translation("wedding_team", language)}
                                    </p>
                                </td>
                            </tr>

                            <!-- Footer -->
                            <tr>
                                <td style="padding: 20px 40px; background-color: #f5f5f5; border-radius: 0 0 8px 8px; text-align: center;">
                                    <p style="margin: 0; font-size: 12px; color: #888888;">
                                        {get_translation("automated_email", language)}
                                    </p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """

    def _generate_rsvp_confirmation_text(
        self,
        guest_name: str,
        confirmation_number: str,
        attending: bool,
        rsvp_details: dict[str, Any],
        language: str = "en",
    ) -> str:
        """Generate plain text for RSVP confirmation email."""
        status = get_translation("attending" if attending else "not_attending", language)
        status_message = get_translation("excited_celebrate" if attending else "will_miss_you", language)

        text = f"""
{get_translation("rsvp_confirmed", language)}

{get_translation("dear", language)} {guest_name},

{get_translation("thank_you_rsvp", language)} {status_message}

{get_translation("rsvp_details", language)}:
--------------
{get_translation("confirmation_number", language)}: {confirmation_number}
{get_translation("status", language)}: {status}
"""

        if attending and rsvp_details.get("plus_one"):
            text += f"{get_translation('plus_one', language)}: {get_translation('yes', language)}\n"

        if attending and rsvp_details.get("dietary_restrictions"):
            text += f"{get_translation('dietary_restrictions', language)}: {rsvp_details['dietary_restrictions']}\n"

        if rsvp_details.get("message"):
            text += f"\n{get_translation('your_message', language)}:\n{rsvp_details['message']}\n"

        text += f"""
{get_translation("changes_contact", language)}

{get_translation("with_love", language)},
{get_translation("wedding_team", language)}

---
{get_translation("automated_email", language)}
"""
        return text

    @staticmethod
    def _admin_panel_url() -> str:
        return f"{settings.frontend_url.rstrip('/')}/admin"

    @staticmethod
    def _admin_summary_lines(attending: bool, rsvp_details: dict[str, Any]) -> list[str]:
        """The only RSVP details an admin notice carries: whether they come, and with how many."""
        lines = [f"Status: {'ATTENDING' if attending else 'NOT ATTENDING'}"]
        if attending and rsvp_details.get("plus_one"):
            lines.append("Plus One: Yes")
        if attending and rsvp_details.get("children_count"):
            lines.append(f"Children: {int(rsvp_details['children_count'])}")
        return lines

    def _generate_admin_notification_html(
        self,
        guest_name: str,
        attending: bool,
        rsvp_details: dict[str, Any],
    ) -> str:
        """Generate HTML for admin notification email."""
        rows = "".join(f"""<tr><td style="padding: 8px 0;">{line}</td></tr>""" for line in [f"<strong>Guest Name:</strong> {guest_name}", *self._admin_summary_lines(attending, rsvp_details)])
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f5f5f5;">
            <table cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color: #f5f5f5; padding: 40px 20px;">
                <tr>
                    <td align="center">
                        <table cellpadding="0" cellspacing="0" border="0" width="600" style="background-color: #ffffff; border-radius: 8px;">
                            <tr>
                                <td style="padding: 30px 40px; text-align: center; background-color: #2196F3; border-radius: 8px 8px 0 0;">
                                    <h1 style="margin: 0; color: #ffffff; font-size: 24px;">New RSVP Received</h1>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 40px; font-size: 16px; line-height: 1.6; color: #333333;">
                                    <table cellpadding="0" cellspacing="0" border="0" width="100%">{rows}</table>
                                    <p style="font-size: 14px; color: #666666; margin: 20px 0 0;">
                                        Contact details, dietary needs and messages are in the
                                        <a href="{self._admin_panel_url()}" style="color: #2196F3;">admin panel</a>.
                                    </p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """

    def _generate_admin_notification_text(
        self,
        guest_name: str,
        attending: bool,
        rsvp_details: dict[str, Any],
    ) -> str:
        """Generate plain text for admin notification email."""
        summary = "\n".join(self._admin_summary_lines(attending, rsvp_details))
        return (
            f"NEW RSVP RECEIVED\n\nGuest: {guest_name}\n{summary}\n\n"
            f"Contact details, dietary needs and messages are in the admin panel: {self._admin_panel_url()}\n"
            "\n---\nWedding Planner Admin Notification"
        )


# Global email service instance
email_service = EmailService()

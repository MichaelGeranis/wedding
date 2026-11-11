"""CSV export and import utilities for guest lists and RSVPs."""

import csv
import io
from dataclasses import dataclass
from datetime import datetime

from wedding_api.models.invited_guest import InvitedGuestResponse
from wedding_api.models.rsvp import RSVPResponse


@dataclass
class CSVImportRow:
    """Represents a row from CSV import."""

    name: str
    phone: str
    notes: str | None = None
    invitation_sent: bool = False
    rsvp_received: bool = False


@dataclass
class CSVImportResult:
    """Result of CSV import operation."""

    success_count: int
    error_count: int
    errors: list[dict[str, str]]
    skipped_count: int


def parse_invited_guests_csv(csv_content: str) -> tuple[list[CSVImportRow], list[dict[str, str]]]:
    """
    Parse CSV content and return list of rows to import.

    Expected CSV columns (case-insensitive):
    - Guest Name or Name (required)
    - Phone (required)
    - Notes (optional)
    - Invitation Sent (optional, Yes/No/True/False)
    - RSVP Received (optional, Yes/No/True/False)

    Returns tuple of (valid_rows, errors)
    """
    rows: list[CSVImportRow] = []
    errors: list[dict[str, str]] = []

    try:
        reader = csv.DictReader(io.StringIO(csv_content))

        # Normalize header names (case-insensitive)
        if reader.fieldnames is None:
            return [], [{"row": "0", "error": "CSV file is empty or has no headers"}]

        # Map of normalized names to actual column names
        header_map: dict[str, str] = {}
        for field in reader.fieldnames:
            normalized = field.lower().strip().replace(" ", "_")
            header_map[normalized] = field

        # Check required columns
        name_col = header_map.get("guest_name") or header_map.get("name")
        phone_col = header_map.get("phone")

        if not name_col:
            return [], [{"row": "0", "error": "Missing required column: 'Guest Name' or 'Name'"}]
        if not phone_col:
            return [], [{"row": "0", "error": "Missing required column: 'Phone'"}]

        # Optional columns
        notes_col = header_map.get("notes")
        invitation_sent_col = header_map.get("invitation_sent")
        rsvp_received_col = header_map.get("rsvp_received")

        for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
            try:
                name = row.get(name_col, "").strip()
                phone = row.get(phone_col, "").strip()

                if not name:
                    errors.append({"row": str(row_num), "error": "Missing guest name"})
                    continue
                if not phone:
                    errors.append({"row": str(row_num), "error": f"Missing phone for '{name}'"})
                    continue

                # Parse optional fields
                notes = row.get(notes_col, "").strip() if notes_col else None
                if not notes:
                    notes = None

                invitation_sent = False
                if invitation_sent_col:
                    val = row.get(invitation_sent_col, "").strip().lower()
                    invitation_sent = val in ("yes", "true", "1")

                rsvp_received = False
                if rsvp_received_col:
                    val = row.get(rsvp_received_col, "").strip().lower()
                    rsvp_received = val in ("yes", "true", "1")

                rows.append(
                    CSVImportRow(
                        name=name,
                        phone=phone,
                        notes=notes,
                        invitation_sent=invitation_sent,
                        rsvp_received=rsvp_received,
                    )
                )
            except Exception as e:
                errors.append({"row": str(row_num), "error": str(e)})

    except csv.Error as e:
        return [], [{"row": "0", "error": f"Invalid CSV format: {e}"}]

    return rows, errors


def generate_rsvp_csv(rsvps: list[RSVPResponse]) -> str:
    """Generate CSV content from list of RSVPs."""
    output = io.StringIO()
    writer = csv.writer(output)

    headers = [
        "Guest Name",
        "Email",
        "Phone",
        "Attending",
        "Plus One",
        "Dietary Restrictions",
        "Message",
        "Confirmation Number",
        "Submitted At",
    ]
    writer.writerow(headers)

    for rsvp in rsvps:
        row = [
            rsvp.guest_name,
            rsvp.email,
            rsvp.phone or "",
            "Yes" if rsvp.attending else "No",
            "Yes" if rsvp.plus_one else "No",
            rsvp.dietary_restrictions or "",
            rsvp.message or "",
            rsvp.confirmation_number,
            rsvp.created_at.strftime("%Y-%m-%d %H:%M:%S") if rsvp.created_at else "",
        ]
        writer.writerow(row)

    csv_content = output.getvalue()
    output.close()

    return csv_content


def generate_guest_summary_csv(stats: dict[str, int], rsvps: list[RSVPResponse]) -> str:
    """Generate a summary CSV with statistics and guest list."""
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Wedding RSVP Summary"])
    writer.writerow(["Generated At", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
    writer.writerow([])

    writer.writerow(["Statistics"])
    writer.writerow(["Total RSVPs", stats.get("total", 0)])
    writer.writerow(["Attending", stats.get("attending", 0)])
    writer.writerow(["Not Attending", stats.get("not_attending", 0)])
    writer.writerow(["Plus Ones", stats.get("plus_ones", 0)])
    writer.writerow([])

    writer.writerow(["Guest List"])
    headers = [
        "Guest Name",
        "Email",
        "Phone",
        "Attending",
        "Plus One",
        "Dietary Restrictions",
        "Confirmation Number",
        "Submitted At",
    ]
    writer.writerow(headers)

    for rsvp in rsvps:
        row = [
            rsvp.guest_name,
            rsvp.email,
            rsvp.phone or "",
            "Yes" if rsvp.attending else "No",
            "Yes" if rsvp.plus_one else "No",
            rsvp.dietary_restrictions or "",
            rsvp.confirmation_number,
            rsvp.created_at.strftime("%Y-%m-%d %H:%M:%S") if rsvp.created_at else "",
        ]
        writer.writerow(row)

    csv_content = output.getvalue()
    output.close()

    return csv_content


def generate_invited_guests_csv(guests: list[InvitedGuestResponse]) -> str:
    """Generate CSV content from list of invited guests."""
    output = io.StringIO()
    writer = csv.writer(output)

    headers = [
        "ID",
        "Guest Name",
        "Phone",
        "Notes",
        "Invitation Sent",
        "Added At",
        "Last Updated",
    ]
    writer.writerow(headers)

    for guest in guests:
        row = [
            guest.id,
            guest.name,
            guest.phone,
            guest.notes or "",
            "Yes" if guest.invitation_sent else "No",
            guest.created_at.strftime("%Y-%m-%d %H:%M:%S") if guest.created_at else "",
            guest.updated_at.strftime("%Y-%m-%d %H:%M:%S") if guest.updated_at else "",
        ]
        writer.writerow(row)

    csv_content = output.getvalue()
    output.close()

    return csv_content

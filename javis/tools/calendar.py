from datetime import datetime, timedelta
from typing import Optional, List
from googleapiclient.discovery import build
from pydantic import BaseModel

from javis.helper import get_google_crendential


class CalendarEvent(BaseModel):
    """Model for calendar event details"""

    summary: str
    description: Optional[str] = None
    location: Optional[str] = None
    start_time: datetime
    end_time: datetime
    attendees: Optional[List[str]] = None
    timezone: str = "Asia/Ho_Chi_Minh"


def get_calendar_service():
    """Initialize and return the Google Calendar service.

    Returns:
        Resource: Google Calendar API service
    """
    creds = get_google_crendential()

    service = build("calendar", "v3", credentials=creds)
    return service


async def create_calendar_event(
    summary: str,
    start_time: str,
    end_time: str,
    description: str = None,
    location: str = None,
    attendees: List[str] = None,
    timezone: str = "Asia/Ho_Chi_Minh",
) -> dict:
    """Create a new event in Google Calendar.

    Args:
        summary: Title of the event
        start_time: Start time in ISO format (YYYY-MM-DDTHH:MM:SS)
        end_time: End time in ISO format (YYYY-MM-DDTHH:MM:SS)
        description: Optional description of the event
        location: Optional location of the event
        attendees: Optional list of attendee email addresses
        timezone: Timezone for the event (default: Asia/Ho_Chi_Minh)

    Returns:
        dict: Created event details including event ID and link

    Example:
        >>> await create_calendar_event(
        ...     summary="Team Meeting",
        ...     start_time="2024-04-20T10:00:00",
        ...     end_time="2024-04-20T11:00:00",
        ...     description="Weekly team sync",
        ...     attendees=["john@example.com", "jane@example.com"]
        ... )
    """
    try:
        # Parse the datetime strings
        start_dt = datetime.fromisoformat(start_time)
        end_dt = datetime.fromisoformat(end_time)

        # Create event details
        event = {
            "summary": summary,
            "location": location,
            "description": description,
            "start": {
                "dateTime": start_dt.isoformat(),
                "timeZone": timezone,
            },
            "end": {
                "dateTime": end_dt.isoformat(),
                "timeZone": timezone,
            },
        }

        # Add attendees if provided
        if attendees:
            event["attendees"] = [{"email": email} for email in attendees]
            event["guestsCanModify"] = True
            event["guestsCanInviteOthers"] = True

        print(f"event: {event}")

        # Get calendar service
        service = get_calendar_service()

        # Create the event
        created_event = (
            service.events()
            .insert(
                calendarId="primary",
                body=event,
                sendUpdates="all",  # Send email notifications to attendees
            )
            .execute()
        )

        # Return relevant event details
        return {
            "event_id": created_event["id"],
            "html_link": created_event["htmlLink"],
            "summary": created_event["summary"],
            "start_time": created_event["start"]["dateTime"],
            "end_time": created_event["end"]["dateTime"],
            "attendees": [a["email"] for a in created_event.get("attendees", [])],
        }

    except Exception as e:
        return {"error": str(e), "status": "failed"}


async def get_calendar_events(
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    days: Optional[int] = None,
    timezone: str = "Asia/Ho_Chi_Minh",
) -> dict:
    """Get a list of calendar events within a specified time range.

    This function supports two ways of getting events:
    1. Between two specific dates by providing from_date and to_date
    2. For X days from today by providing days parameter

    Args:
        from_date: Start date/datetime in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
        to_date: End date/datetime in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
        days: Number of days to fetch events from today
        timezone: Timezone for the events (default: Asia/Ho_Chi_Minh)

    Returns:
        dict: List of events with their details or error information

    Examples:
        # Get events between two dates
        >>> await get_calendar_events(
        ...     from_date="2024-04-20T00:00:00",
        ...     to_date="2024-04-21T00:00:00"
        ... )

        # Get events for next 7 days
        >>> await get_calendar_events(days=7)
    """
    try:
        # Get calendar service
        service = get_calendar_service()

        # Determine the time range based on input parameters
        now = datetime.now()

        if days is not None:
            # Case 1: Get events for X days from today
            start_dt = now
            end_dt = now + timedelta(days=days)
        elif from_date and to_date:
            # Case 2: Get events between two specific dates
            start_dt = datetime.fromisoformat(from_date)
            end_dt = datetime.fromisoformat(to_date)
        else:
            start_dt = now
            end_dt = now
            raise ValueError("Either provide (from_date, to_date) or days parameter")

        # Call the Calendar API
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=start_dt.isoformat() + "Z",  # 'Z' indicates UTC time
                timeMax=end_dt.isoformat() + "Z",
                singleEvents=True,
                orderBy="startTime",
                timeZone=timezone,
            )
            .execute()
        )

        events = events_result.get("items", [])

        if not events:
            return {"message": "No events found.", "events": [], "status": "success"}

        # Format the events
        formatted_events = []
        for event in events:
            formatted_event = {
                "event_id": event["id"],
                "summary": event["summary"],
                "html_link": event.get("htmlLink", ""),
                "start_time": event["start"].get(
                    "dateTime", event["start"].get("date")
                ),
                "end_time": event["end"].get("dateTime", event["end"].get("date")),
                "description": event.get("description", ""),
                "location": event.get("location", ""),
                "attendees": [
                    attendee["email"] for attendee in event.get("attendees", [])
                ],
            }
            formatted_events.append(formatted_event)

        return {
            "status": "success",
            "events": formatted_events,
            "period": {
                "start": start_dt.isoformat(),
                "end": end_dt.isoformat(),
                "timezone": timezone,
            },
        }

    except Exception as e:
        return {"error": str(e), "status": "failed"}


async def delete_calendar_event(
    event_name: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    timezone: str = "Asia/Ho_Chi_Minh",
) -> dict:
    """Delete calendar events either by name or within a date range.

    This function supports two ways of deleting events:
    1. Delete a specific event by its name (will delete the first matching event)
    2. Delete all events within a date range

    Args:
        event_name: Name of the event to delete
        from_date: Start date/datetime in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
        to_date: End date/datetime in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
        timezone: Timezone for the events (default: Asia/Ho_Chi_Minh)

    Returns:
        dict: Status of the deletion operation

    Examples:
        # Delete by event name
        >>> await delete_calendar_event(event_name="Team Meeting")

        # Delete events in a date range
        >>> await delete_calendar_event(
        ...     from_date="2024-04-20T00:00:00",
        ...     to_date="2024-04-21T00:00:00"
        ... )
    """
    try:
        # Get calendar service
        service = get_calendar_service()
        print(f"event_name: {event_name}")
        print(f"from_date: {from_date}")
        print(f"to_date: {to_date}")
        if event_name:
            # Case 1: Delete by event name
            # First, search for the event
            now = datetime.now()
            # Search in a broad range (30 days) to find the event
            events_result = (
                service.events()
                .list(
                    calendarId="primary",
                    timeMin=now.isoformat() + "Z",
                    timeMax=(now + timedelta(days=30)).isoformat() + "Z",
                    q=event_name,  # Search by event name
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            print(f"event_name: {event_name}")
            print(f"events_result: {events_result}")
            events = events_result.get("items", [])
            if not events:
                return {
                    "status": "failed",
                    "error": f"No event found with name: {event_name}",
                }

            # Delete the first matching event
            for event in events:
                service.events().delete(
                    calendarId="primary", eventId=event["id"], sendUpdates="all"
                ).execute()

            return {
                "status": "success",
                "message": f"Event '{event_name}' has been successfully deleted",
                "event_details": {
                    "id": event["id"],
                    "summary": event["summary"],
                    "start": event["start"].get("dateTime", event["start"].get("date")),
                },
            }

        elif from_date and to_date:
            # Case 2: Delete events in date range
            # First, get all events in the range
            start_dt = datetime.fromisoformat(from_date)
            end_dt = datetime.fromisoformat(to_date)

            events_result = (
                service.events()
                .list(
                    calendarId="primary",
                    timeMin=start_dt.isoformat() + "Z",
                    timeMax=end_dt.isoformat() + "Z",
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )

            events = events_result.get("items", [])
            if not events:
                return {
                    "status": "success",
                    "message": f"No events found in the specified date range",
                }

            # Delete all events in the range
            deleted_events = []
            for event in events:
                service.events().delete(
                    calendarId="primary", eventId=event["id"], sendUpdates="all"
                ).execute()
                deleted_events.append(
                    {
                        "id": event["id"],
                        "summary": event["summary"],
                        "start": event["start"].get(
                            "dateTime", event["start"].get("date")
                        ),
                    }
                )

            return {
                "status": "success",
                "message": f"Successfully deleted {len(deleted_events)} events",
                "deleted_events": deleted_events,
                "period": {
                    "start": start_dt.isoformat(),
                    "end": end_dt.isoformat(),
                    "timezone": timezone,
                },
            }
        else:
            raise ValueError("Either provide event_name or (from_date, to_date)")

    except Exception as e:
        return {"status": "failed", "error": str(e)}

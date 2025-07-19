"""
Calendar Integration for LifeOS Automations
Handles calendar event creation and management
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import re
import json
import os
from openai import OpenAI

logger = logging.getLogger(__name__)


class CalendarIntegration:
    """Handles calendar-related automations"""
    
    def __init__(self):
        # Initialize calendar service (Google Calendar, Outlook, etc.)
        self.calendar_service = None
        
        # Initialize OpenAI for event extraction
        api_key = os.getenv("OPENAI_API_KEY")
        self.openai_client = OpenAI(api_key=api_key)
        
        # Google Calendar configuration
        self.google_credentials_path = os.getenv("GOOGLE_CALENDAR_CREDENTIALS_PATH")
        self.google_calendar_id = os.getenv("GOOGLE_CALENDAR_ID", "primary")
        
        # Initialize Google Calendar service if credentials are available
        if self.google_credentials_path and os.path.exists(self.google_credentials_path):
            try:
                from google.oauth2 import service_account
                from googleapiclient.discovery import build
                
                credentials = service_account.Credentials.from_service_account_file(
                    self.google_credentials_path,
                    scopes=['https://www.googleapis.com/auth/calendar']
                )
                self.calendar_service = build('calendar', 'v3', credentials=credentials)
                logger.info("Google Calendar service initialized successfully")
            except ImportError:
                logger.warning("Google Calendar dependencies not installed. Run: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
            except Exception as e:
                logger.error(f"Failed to initialize Google Calendar service: {e}")
        else:
            logger.info("Google Calendar credentials not configured. Events will be simulated.")
        
    async def process_calendar_events(
        self, 
        summary: str, 
        analysis: Dict[str, Any], 
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process video summary for calendar events and create them if needed
        
        Args:
            summary: Video summary text
            analysis: LLM analysis results
            metadata: Video metadata
            
        Returns:
            Dictionary with calendar processing results including extracted events
        """
        try:
            logger.info("Processing calendar events from video summary")
            
            # Extract calendar events from the summary
            extracted_events = await self._extract_calendar_events(summary)
            
            # Create calendar events if any were found
            created_events = []
            for event in extracted_events:
                created_event = await self._create_calendar_event(event, metadata)
                if created_event:
                    created_events.append(created_event)
            
            results = {
                "calendar_automation_triggered": True,
                "processing_timestamp": datetime.now().isoformat(),
                "extracted_events": extracted_events,
                "created_events": created_events,
                "events_count": len(created_events),
                "message": f"Processed {len(created_events)} calendar events"
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing calendar events: {e}")
            return {
                "calendar_automation_triggered": False,
                "error": str(e),
                "extracted_events": [],
                "created_events": []
            }
    
    async def _extract_calendar_events(self, summary: str) -> List[Dict[str, Any]]:
        """
        Extract calendar events with date, time, and title from video summary using LLM
        
        Args:
            summary: Video summary text
            
        Returns:
            List of extracted calendar events with date, time, and title
        """
        try:
            logger.info("Extracting calendar events from summary using LLM")
            
            prompt = f"""
Analyze the following video summary and extract any calendar events mentioned.

Video Summary: "{summary}"

Please respond with a JSON object containing:
- "events": array of event objects, each with:
  - "title": descriptive title for the event
  - "date": extracted date (ISO format YYYY-MM-DD or relative like "tomorrow", "next week")
  - "time": extracted time (24-hour format HH:MM or descriptive like "morning", "afternoon")
  - "description": brief description of the event
  - "location": location if mentioned
  - "duration": estimated duration in minutes
  - "type": event type (meeting, appointment, deadline, reminder, etc.)

Only extract events that have a clear date or time reference. Examples:
- "Meeting tomorrow at 3 PM" 
- "Deadline next Friday"
- "Call scheduled for Monday morning"
- "Appointment on January 15th at 2:30"

If no calendar events are found, return an empty events array.

Respond only with valid JSON.
"""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI assistant that extracts calendar events from text. Always respond with valid JSON."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=800
            )
            
            response_text = response.choices[0].message.content
            
            try:
                extraction_result = json.loads(response_text)
                events = extraction_result.get("events", [])
                
                # Process and validate extracted events
                processed_events = []
                for event in events:
                    processed_event = self._process_extracted_event(event)
                    if processed_event:
                        processed_events.append(processed_event)
                
                logger.info(f"Extracted {len(processed_events)} calendar events")
                return processed_events
                
            except json.JSONDecodeError:
                logger.error(f"Failed to parse event extraction JSON: {response_text}")
                return []
                
        except Exception as e:
            logger.error(f"Error extracting calendar events: {e}")
            return []
    
    def _process_extracted_event(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process and validate an extracted event
        
        Args:
            event: Raw event data from LLM
            
        Returns:
            Processed event or None if invalid
        """
        try:
            # Ensure required fields exist
            if not event.get("title") or not (event.get("date") or event.get("time")):
                return None
            
            # Parse and normalize the date/time
            parsed_datetime = self._parse_event_datetime(
                event.get("date"), 
                event.get("time")
            )
            
            processed = {
                "title": (event.get("title") or "").strip(),
                "description": (event.get("description") or "").strip(),
                "location": (event.get("location") or "").strip(),
                "start_time": parsed_datetime.isoformat() if parsed_datetime else None,
                "end_time": None,  # Will be calculated based on duration
                "duration_minutes": event.get("duration", 60),  # Default 1 hour
                "event_type": event.get("type", "event"),
                "raw_date": event.get("date", ""),
                "raw_time": event.get("time", "")
            }
            
            # Calculate end time if start time is available
            if parsed_datetime:
                duration_mins = processed["duration_minutes"]
                if duration_mins and duration_mins > 0:
                    duration = timedelta(minutes=duration_mins)
                    processed["end_time"] = (parsed_datetime + duration).isoformat()
                else:
                    # Default 1 hour for events without duration
                    processed["end_time"] = (parsed_datetime + timedelta(hours=1)).isoformat()
            
            return processed
            
        except Exception as e:
            logger.error(f"Error processing extracted event: {e}")
            return None
    
    def _parse_event_datetime(self, date_str: Optional[str], time_str: Optional[str]) -> Optional[datetime]:
        """
        Parse date and time strings into a datetime object
        
        Args:
            date_str: Date string (ISO format or relative)
            time_str: Time string (24-hour format or descriptive)
            
        Returns:
            Parsed datetime or None
        """
        try:
            # Use EST timezone for all datetime operations
            est_tz = ZoneInfo("America/New_York")
            base_date = datetime.now(est_tz).replace(hour=0, minute=0, second=0, microsecond=0)
            target_date = base_date
            target_time = None
            
            # Parse date
            if date_str:
                date_lower = date_str.lower().strip()
                
                # Handle relative dates
                if "today" in date_lower:
                    target_date = base_date
                elif "tomorrow" in date_lower:
                    target_date = base_date + timedelta(days=1)
                elif "next week" in date_lower:
                    target_date = base_date + timedelta(days=7)
                elif "next month" in date_lower:
                    target_date = base_date + timedelta(days=30)
                elif "monday" in date_lower:
                    # Find next Monday
                    days_ahead = 0 - base_date.weekday()  # Monday is 0
                    if days_ahead <= 0:  # Target day is today or has passed this week
                        days_ahead += 7
                    target_date = base_date + timedelta(days=days_ahead)
                elif "tuesday" in date_lower:
                    days_ahead = 1 - base_date.weekday()
                    if days_ahead <= 0:
                        days_ahead += 7
                    target_date = base_date + timedelta(days=days_ahead)
                elif "wednesday" in date_lower:
                    days_ahead = 2 - base_date.weekday()
                    if days_ahead <= 0:
                        days_ahead += 7
                    target_date = base_date + timedelta(days=days_ahead)
                elif "thursday" in date_lower:
                    days_ahead = 3 - base_date.weekday()
                    if days_ahead <= 0:
                        days_ahead += 7
                    target_date = base_date + timedelta(days=days_ahead)
                elif "friday" in date_lower:
                    days_ahead = 4 - base_date.weekday()
                    if days_ahead <= 0:
                        days_ahead += 7
                    target_date = base_date + timedelta(days=days_ahead)
                elif "saturday" in date_lower:
                    days_ahead = 5 - base_date.weekday()
                    if days_ahead <= 0:
                        days_ahead += 7
                    target_date = base_date + timedelta(days=days_ahead)
                elif "sunday" in date_lower:
                    days_ahead = 6 - base_date.weekday()
                    if days_ahead <= 0:
                        days_ahead += 7
                    target_date = base_date + timedelta(days=days_ahead)
                else:
                    # Try ISO date format but ensure it's using current year or later
                    if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
                        parsed_date = datetime.strptime(date_str[:10], '%Y-%m-%d')
                        # If the parsed year is less than current year, assume they meant current year
                        if parsed_date.year < base_date.year:
                            target_date = parsed_date.replace(year=base_date.year)
                        else:
                            target_date = parsed_date
                    # Add more date parsing logic as needed
            
            # Parse time
            if time_str:
                time_lower = time_str.lower().strip()
                
                # Handle descriptive times
                if "morning" in time_lower:
                    target_time = 9  # 9 AM
                elif "afternoon" in time_lower:
                    target_time = 14  # 2 PM
                elif "evening" in time_lower:
                    target_time = 18  # 6 PM
                elif "night" in time_lower:
                    target_time = 20  # 8 PM
                else:
                    # Try to parse specific time formats
                    time_match = re.search(r'(\d{1,2}):?(\d{0,2})\s*(am|pm)?', time_lower)
                    if time_match:
                        hour = int(time_match.group(1))
                        minute = int(time_match.group(2)) if time_match.group(2) else 0
                        ampm = time_match.group(3)
                        
                        if ampm == 'pm' and hour != 12:
                            hour += 12
                        elif ampm == 'am' and hour == 12:
                            hour = 0
                        
                        target_time = hour
                        target_date = target_date.replace(hour=hour, minute=minute)
                    else:
                        # Try 24-hour format
                        time_24_match = re.search(r'(\d{1,2}):(\d{2})', time_str)
                        if time_24_match:
                            hour = int(time_24_match.group(1))
                            minute = int(time_24_match.group(2))
                            target_date = target_date.replace(hour=hour, minute=minute)
            
            # If we have a time but no specific time was parsed, default to 10 AM
            if time_str and target_time is None and target_date.hour == 0:
                target_date = target_date.replace(hour=10)
            
            return target_date
            
        except Exception as e:
            logger.error(f"Error parsing datetime from '{date_str}' and '{time_str}': {e}")
            return None
    
    async def _create_calendar_event(
        self, 
        event_data: Dict[str, Any], 
        metadata: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Create a calendar event from extracted event data
        
        Args:
            event_data: Event information extracted from LLM
            metadata: Video metadata for context
            
        Returns:
            Created event data or None if failed
        """
        try:
            # Extract event details
            title = event_data.get("title", "Event from LifeOS")
            description = event_data.get("description", "")
            start_time = self._parse_event_time(event_data.get("start_time"))
            end_time = self._parse_event_time(event_data.get("end_time"))
            location = event_data.get("location", "")
            
            # Default duration if no end time
            if start_time and not end_time:
                end_time = start_time + timedelta(hours=1)
            
            # Create event using Google Calendar API if available
            if self.calendar_service and start_time:
                try:
                    google_event = {
                        'summary': title,
                        'description': f"{description}\n\nCreated from LifeOS video analysis\nVideo ID: {metadata.get('video_id', 'N/A')}",
                        'location': location,
                        'start': {
                            'dateTime': start_time.isoformat(),
                            'timeZone': 'America/New_York',
                        },
                        'end': {
                            'dateTime': end_time.isoformat() if end_time else (start_time + timedelta(hours=1)).isoformat(),
                            'timeZone': 'America/New_York',
                        }
                    }
                    
                    # Create the event
                    created_event = self.calendar_service.events().insert(
                        calendarId=self.google_calendar_id,
                        body=google_event
                    ).execute()
                    
                    logger.info(f"Created Google Calendar event: {title} (ID: {created_event['id']})")
                    
                    return {
                        "id": created_event['id'],
                        "title": title,
                        "description": description,
                        "start_time": start_time.isoformat(),
                        "end_time": end_time.isoformat() if end_time else None,
                        "location": location,
                        "source": "LifeOS",
                        "video_id": metadata.get("video_id"),
                        "created_at": datetime.now().isoformat(),
                        "google_calendar_link": created_event.get('htmlLink'),
                        "calendar_id": self.google_calendar_id,
                        "api_created": True
                    }
                    
                except Exception as e:
                    logger.error(f"Failed to create Google Calendar event: {e}")
                    # Fall back to simulation
            
            # Simulate event creation if Google Calendar is not available
            simulated_event = {
                "id": f"lifeos_event_{datetime.now().timestamp()}",
                "title": title,
                "description": f"{description}\n\nCreated from LifeOS video analysis",
                "start_time": start_time.isoformat() if start_time else None,
                "end_time": end_time.isoformat() if end_time else None,
                "location": location,
                "source": "LifeOS",
                "video_id": metadata.get("video_id"),
                "created_at": datetime.now().isoformat(),
                "api_created": False,
                "note": "Simulated event - Google Calendar not configured"
            }
            
            logger.info(f"Simulated calendar event: {simulated_event['title']}")
            
            return simulated_event
            
        except Exception as e:
            logger.error(f"Error creating calendar event: {e}")
            return None
    
    def _parse_event_time(self, time_str: Optional[str]) -> Optional[datetime]:
        """
        Parse event time from string to datetime
        
        Args:
            time_str: Time string to parse
            
        Returns:
            Parsed datetime or None
        """
        if not time_str:
            return None
            
        try:
            # Handle common time formats
            # This is a simplified parser - in production, use a robust library like dateutil
            
            # ISO format
            if re.match(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', time_str):
                return datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            
            # Simple date format
            if re.match(r'\d{4}-\d{2}-\d{2}', time_str):
                return datetime.strptime(time_str, '%Y-%m-%d')
            
            # Add more parsing logic as needed
            logger.warning(f"Could not parse time string: {time_str}")
            return None
            
        except Exception as e:
            logger.error(f"Error parsing time string '{time_str}': {e}")
            return None
    
    async def get_upcoming_events(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """
        Get upcoming calendar events
        
        Args:
            days_ahead: Number of days to look ahead
            
        Returns:
            List of upcoming events
        """
        try:
            # This would query the actual calendar service
            # For now, return empty list
            return []
            
        except Exception as e:
            logger.error(f"Error getting upcoming events: {e}")
            return []
    
    async def update_event(self, event_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update an existing calendar event
        
        Args:
            event_id: ID of the event to update
            updates: Dictionary of fields to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # This would update the actual calendar event
            logger.info(f"Would update event {event_id} with: {updates}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating event {event_id}: {e}")
            return False
    
    async def delete_event(self, event_id: str) -> bool:
        """
        Delete a calendar event
        
        Args:
            event_id: ID of the event to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # This would delete the actual calendar event
            logger.info(f"Would delete event {event_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting event {event_id}: {e}")
            return False
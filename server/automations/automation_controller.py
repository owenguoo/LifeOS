"""
Automation Controller for LifeOS
Processes video summaries and triggers relevant automations
"""

import asyncio
import logging
from typing import Dict, List, Any
from datetime import datetime

from database.supabase_client import SupabaseManager
from .calendar_integration import CalendarIntegration
from .highlights_integration import HighlightsIntegration
from .summary_analyzer import SummaryAnalyzer

logger = logging.getLogger(__name__)


class AutomationController:
    """Main controller that orchestrates automation workflows"""

    def __init__(self):
        self.supabase_manager = SupabaseManager()
        self.calendar_integration = CalendarIntegration()
        self.highlights_integration = HighlightsIntegration()
        self.summary_analyzer = SummaryAnalyzer()

    async def process_video_summary(
        self, video_id: str, summary: str, metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Main entry point for processing video summaries through automation pipeline

        Args:
            video_id: UUID of the video in the database
            summary: Generated summary text from the video
            metadata: Additional metadata about the video (timestamp, user_id, etc.)

        Returns:
            Dictionary containing results of all automation checks
        """
        try:
            logger.info(f"Processing automation for video {video_id}")

            # Analyze the summary using LLM
            analysis_result = await self.summary_analyzer.analyze_summary(
                summary=summary, metadata=metadata
            )

            automation_results = {
                "video_id": video_id,
                "processed_at": datetime.now().isoformat(),
                "analysis": analysis_result,
                "automations_triggered": [],
            }

            # Get triggered automations from LLM analysis
            triggered_automations = analysis_result.get("triggered_automations", [])
            print(f"🤖 LLM Analysis Result: {analysis_result}")
            print(f"🎯 Triggered automations: {triggered_automations}")

            # Run automations in parallel based on analysis
            automation_tasks = []

            # Calendar automation
            if "calendar" in triggered_automations:
                automation_tasks.append(
                    self._run_calendar_automation(
                        video_id, summary, analysis_result, metadata
                    )
                )

            # Highlights automation
            if "highlights" in triggered_automations:
                print(f"✨ Highlights automation triggered for video {video_id}")
                automation_tasks.append(
                    self._run_highlights_automation(
                        video_id, summary, analysis_result, metadata
                    )
                )

            # Execute all automations in parallel
            if automation_tasks:
                automation_results_list = await asyncio.gather(
                    *automation_tasks, return_exceptions=True
                )

                for result in automation_results_list:
                    if isinstance(result, Exception):
                        logger.error(f"Automation failed: {result}")
                        automation_results["automations_triggered"].append(
                            {"type": "error", "status": "failed", "error": str(result)}
                        )
                    else:
                        automation_results["automations_triggered"].append(result)

            # Store automation results in database
            await self._store_automation_results(video_id, automation_results)

            logger.info(f"Completed automation processing for video {video_id}")
            return automation_results

        except Exception as e:
            logger.error(f"Error processing automation for video {video_id}: {e}")
            return {
                "video_id": video_id,
                "processed_at": datetime.now().isoformat(),
                "error": str(e),
                "automations_triggered": [],
            }

    async def _run_calendar_automation(
        self,
        video_id: str,
        summary: str,
        analysis: Dict[str, Any],
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Run calendar-related automations"""
        try:
            calendar_result = await self.calendar_integration.process_calendar_events(
                summary=summary, analysis=analysis, metadata=metadata
            )

            return {"type": "calendar", "status": "success", "result": calendar_result}

        except Exception as e:
            logger.error(f"Calendar automation failed for video {video_id}: {e}")
            raise

    async def _run_highlights_automation(
        self,
        video_id: str,
        summary: str,
        analysis: Dict[str, Any],
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Run highlights-related automations"""
        try:
            print(f"🎬 Running highlights automation for video {video_id}")
            print(f"📝 Summary: {summary[:100]}...")
            print(f"👤 Metadata user_id: {metadata.get('user_id')}")

            highlights_result = await self.highlights_integration.add_to_highlights(
                video_id=video_id, summary=summary, analysis=analysis, metadata=metadata
            )

            print(f"✅ Highlights result: {highlights_result}")

            return {
                "type": "highlights",
                "status": "success",
                "result": highlights_result,
            }

        except Exception as e:
            logger.error(f"Highlights automation failed for video {video_id}: {e}")
            print(f"❌ Highlights automation failed: {e}")
            raise

    async def _store_automation_results(
        self, video_id: str, results: Dict[str, Any]
    ) -> bool:
        """Store automation results in the database"""
        try:
            # This could be stored in a separate automation_logs table
            # For now, we'll just log it
            logger.info(f"Automation results for {video_id}: {results}")
            return True

        except Exception as e:
            logger.error(f"Failed to store automation results for {video_id}: {e}")
            return False

    async def get_automation_history(
        self, user_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get automation history for a user"""
        try:
            # This would query the automation_logs table
            # For now, return empty list
            return []

        except Exception as e:
            logger.error(f"Error getting automation history for user {user_id}: {e}")
            return []

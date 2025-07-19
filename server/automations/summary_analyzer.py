"""
Summary Analyzer for LifeOS Automations
Uses LLM to classify summaries and determine which automations to trigger
"""

import logging
import os
import json
from typing import Dict, List, Any
from openai import OpenAI

logger = logging.getLogger(__name__)


class SummaryAnalyzer:
    """Analyzes video summaries using LLM to determine automation triggers"""

    def __init__(self):
        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key)

    async def analyze_summary(
        self, summary: str, metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze video summary to determine which automations should be triggered

        Args:
            summary: Video summary text
            metadata: Additional metadata about the video

        Returns:
            Dictionary with analysis results and triggered automations
        """
        try:
            logger.info("Analyzing summary for automation triggers using GPT-4o-mini")

            # Create the prompt for GPT-4o-mini
            prompt = f"""
Analyze the following video summary and determine which automations should be triggered.

Video Summary: "{summary}"

Please respond with a JSON object containing:
- "triggered_automations": array of strings (can include "calendar", "highlights", or both, or neither)
- "confidence_scores": object with confidence scores (0.0-1.0) for each automation type
- "reasoning": brief explanation of why each automation was/wasn't triggered
- "summary_classification": general category of the content

Guidelines:
- "calendar" should be triggered for: meetings, appointments, deadlines, scheduled events, reminders
- "highlights" should be triggered for: moments you'd want to take photos/videos of - fun experiences, memorable moments, achievements, celebrations, special occasions, interesting discoveries, beautiful scenes, social gatherings, personal milestones, funny incidents, travel moments, creative work, or anything that would make a good story or memory

Think of highlights as "life moments worth capturing" - not just important business events, but also joyful, fun, interesting, or memorable personal experiences.

Respond only with valid JSON.
"""

            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI assistant that analyzes video summaries to determine which automations should be triggered. Always respond with valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=500,
            )

            # Parse the response
            response_text = response.choices[0].message.content

            try:
                analysis_result = json.loads(response_text)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON response: {response_text}")
                # Fallback to simple analysis
                analysis_result = self._fallback_analysis(summary)

            return analysis_result

        except Exception as e:
            logger.error(f"Error analyzing summary with OpenAI: {e}")
            # Fallback to simple analysis
            return self._fallback_analysis(summary)

    def _fallback_analysis(self, summary: str) -> Dict[str, Any]:
        """Fallback analysis when OpenAI fails"""
        return {
            "triggered_automations": self._determine_triggered_automations(summary),
            "confidence_scores": self._calculate_confidence_scores(summary),
            "reasoning": "Fallback analysis used due to API error",
            "summary_classification": self._classify_summary(summary),
        }

    def _determine_triggered_automations(self, summary: str) -> List[str]:
        """
        Determine which automations should be triggered based on summary content

        Args:
            summary: Video summary text

        Returns:
            List of automation types to trigger
        """
        triggered = []

        # Placeholder logic - in production, this would use LLM classification
        summary_lower = summary.lower()

        # Calendar automation triggers
        calendar_keywords = [
            "meeting",
            "appointment",
            "schedule",
            "call",
            "conference",
            "deadline",
            "due date",
            "reminder",
            "event",
            "presentation",
        ]
        if any(keyword in summary_lower for keyword in calendar_keywords):
            triggered.append("calendar")

        # Highlights automation triggers
        highlights_keywords = [
            "important",
            "significant",
            "breakthrough",
            "achievement",
            "milestone",
            "success",
            "discovery",
            "insight",
            "memorable",
        ]
        if any(keyword in summary_lower for keyword in highlights_keywords):
            triggered.append("highlights")

        return triggered

    def _calculate_confidence_scores(self, summary: str) -> Dict[str, float]:
        """
        Calculate confidence scores for each automation type

        Args:
            summary: Video summary text

        Returns:
            Dictionary with confidence scores for each automation
        """
        # Placeholder implementation
        return {"calendar": 0.0, "highlights": 0.0}

    def _extract_entities(self, summary: str) -> Dict[str, List[str]]:
        """
        Extract relevant entities from the summary

        Args:
            summary: Video summary text

        Returns:
            Dictionary with extracted entities by type
        """
        # Placeholder implementation
        return {"people": [], "dates": [], "locations": [], "organizations": []}

    def _classify_summary(self, summary: str) -> str:
        """
        Classify the overall type/category of the summary

        Args:
            summary: Video summary text

        Returns:
            Classification category
        """
        # Placeholder implementation
        return "general"

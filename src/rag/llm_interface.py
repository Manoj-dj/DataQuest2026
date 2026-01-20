"""
OpenAI LLM interface for response generation.
Handles prompt construction, context injection, and response parsing.
Uses OpenAI GPT models for fast, reliable generation.
"""

from openai import OpenAI
from typing import List, Dict, Any, Optional
import time
import json
from src.utils.logger import app_logger

class OpenAILLM:
    def __init__(
        self,
        api_key: str,
        model_name: str = "gpt-4o-mini",
        temperature: float = 0.2,
        max_tokens: int = 1000
    ):
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.logger = app_logger
        
        self._initialize_model()
    
    def _initialize_model(self):
        """
        Configure OpenAI API client.
        """
        try:
            self.client = OpenAI(api_key=self.api_key)
            
            self.logger.logger.info(f"OpenAI LLM initialized: {self.model_name}")
        
        except Exception as e:
            self.logger.log_error("OpenAILLM._initialize_model", e)
            raise
    
    def generate_rag_response(
        self,
        query: str,
        retrieved_contexts: List[Dict[str, Any]],
        include_risk_assessment: bool = True
    ) -> Dict[str, Any]:
        """
        Generate response using RAG pattern with retrieved contexts.
        
        Args:
            query: User's natural language question
            retrieved_contexts: List of relevant disaster events from vector store
            include_risk_assessment: Whether to include risk analysis
            
        Returns:
            Dict with 'answer', 'sources', 'risk_assessment'
        """
        try:
            start_time = time.time()
            
            system_prompt, user_prompt = self._construct_rag_prompt(
                query,
                retrieved_contexts,
                include_risk_assessment
            )
            
            # Try JSON mode first, fallback to regular mode if not supported
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    response_format={"type": "json_object"}
                )
            except Exception as e:
                # Fallback if JSON mode not supported
                self.logger.logger.warning(f"JSON mode not supported, using regular mode: {str(e)}")
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
            
            response_content = response.choices[0].message.content.strip()
            
            # Parse JSON response
            try:
                structured_data = json.loads(response_content)
            except json.JSONDecodeError:
                # Fallback: if JSON parsing fails, treat as plain text
                self.logger.logger.warning("Failed to parse JSON response, using fallback")
                structured_data = {
                    'key_events': [],
                    'risk_assessment_items': [],
                    'recommendations': [],
                    'actionable_insight': response_content
                }
            
            latency_ms = (time.time() - start_time) * 1000
            
            sources = self._extract_sources(retrieved_contexts)
            risk_assessment = self._extract_risk_assessment(retrieved_contexts)
            
            self.logger.log_query(query, latency_ms, len(sources))
            
            return {
                'answer': structured_data.get('actionable_insight', ''),  # Keep for backward compatibility
                'sources': sources,
                'risk_assessment': risk_assessment if include_risk_assessment else None,  # Keep for backward compatibility
                'latency_ms': latency_ms,
                'model': self.model_name,
                # New structured fields
                'key_events': structured_data.get('key_events', []),
                'risk_assessment_items': structured_data.get('risk_assessment', []),
                'recommendations': structured_data.get('recommendations', []),
                'actionable_insight': structured_data.get('actionable_insight', '')
            }
        
        except Exception as e:
            self.logger.log_error("OpenAILLM.generate_rag_response", e)
            return {
                'answer': "I apologize, but I encountered an error processing your query. Please try again.",
                'sources': [],
                'risk_assessment': None,
                'latency_ms': 0,
                'model': self.model_name
            }
    
    def _construct_rag_prompt(
        self,
        query: str,
        contexts: List[Dict[str, Any]],
        include_risk: bool
    ) -> tuple:
        """
        Build RAG prompt with system instructions and retrieved contexts.
        Returns (system_prompt, user_prompt) tuple for OpenAI chat API.
        """
        system_instruction = """You are DisasterLens AI, an expert real-time climate emergency intelligence assistant.

Your role is to provide accurate, timely information about natural disasters based on the latest available data.

CRITICAL INSTRUCTIONS:
1. Base your answers ONLY on the provided disaster event contexts
2. If information is not in the contexts, clearly state that
3. Always cite sources by mentioning the disaster type, location, and timestamp
4. Prioritize recent events (check event_time in contexts)
5. For evacuation/safety questions, be cautious and recommend official sources
6. Include severity levels (Red/Orange/Green) when relevant
7. Be concise but comprehensive
8. Use clear, professional language suitable for emergency managers

RESPONSE FORMAT (JSON ONLY):
You MUST respond with valid JSON in this exact structure:
{
  "key_events": [
    "Event description 1 (e.g., 'Earthquake (Severity: Red) - Location, magnitude X.X, affecting Y people')",
    "Event description 2",
    ...
  ],
  "risk_assessment": [
    "Risk point 1 (e.g., 'High risk due to magnitude and population density')",
    "Risk point 2",
    ...
  ],
  "recommendations": [
    "Recommendation 1 (e.g., 'Monitor official sources for updates')",
    "Recommendation 2",
    ...
  ],
  "actionable_insight": "A concise summary sentence or paragraph that provides the main takeaway"
}

IMPORTANT:
- Do NOT use markdown formatting (no **, ##, -, etc.)
- Do NOT include asterisks or markdown syntax
- Use plain text strings in arrays
- key_events: List the most important disaster events from the contexts
- risk_assessment: List specific risk factors or concerns
- recommendations: List actionable steps or advice
- actionable_insight: A single clear summary sentence or short paragraph
- All fields should be arrays of strings except actionable_insight which is a string
"""
        
        context_section = self._format_contexts(contexts)
        
        risk_instruction = ""
        if include_risk:
            risk_instruction = "\n\nALSO: Provide a brief risk assessment based on the severity and scope of events mentioned."
        
        user_prompt = f"""RETRIEVED DISASTER EVENTS (LATEST DATA):
{context_section}

USER QUERY: {query}
{risk_instruction}

RESPONSE:"""
        
        return (system_instruction, user_prompt)
    
    def _format_contexts(self, contexts: List[Dict[str, Any]]) -> str:
        """
        Format retrieved contexts into readable text for LLM.
        """
        if not contexts:
            return "No relevant disaster events found in the database."
        
        formatted = []
        for i, ctx in enumerate(contexts, 1):
            metadata = ctx.get('metadata', {})
            text = ctx.get('text', '')
            
            event_section = f"""
EVENT {i}:
Type: {metadata.get('disaster_type', 'Unknown')}
Severity: {metadata.get('severity', 'Unknown')}
Location: {metadata.get('location', 'Unknown')}
Risk Score: {metadata.get('risk_score', 'N/A')}/10
Time: {metadata.get('event_time', 'Unknown')}
Source: {metadata.get('source', 'Unknown')}

Details:
{text}

---
"""
            formatted.append(event_section.strip())
        
        return "\n\n".join(formatted)
    
    def _extract_sources(self, contexts: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Extract source citations from contexts.
        """
        sources = []
        for ctx in contexts:
            metadata = ctx.get('metadata', {})
            # Use location_name first, fallback to location, then 'Unknown Location'
            location = metadata.get('location_name') or metadata.get('location') or 'Unknown Location'
            sources.append({
                'event_id': ctx.get('id', 'Unknown'),
                'disaster_type': metadata.get('disaster_type', 'Unknown'),
                'location': location,
                'severity': metadata.get('severity', 'Unknown'),
                'source': metadata.get('source', 'Unknown'),
                'url': metadata.get('url', ''),
                'event_time': metadata.get('event_time', 'Unknown')
            })
        
        return sources
    
    def _extract_risk_assessment(self, contexts: List[Dict[str, Any]]) -> Optional[str]:
        """
        Generate quick risk summary from contexts.
        """
        if not contexts:
            return None
        
        risk_scores = []
        red_alerts = 0
        
        for ctx in contexts:
            metadata = ctx.get('metadata', {})
            
            risk_score = metadata.get('risk_score')
            if risk_score:
                try:
                    risk_scores.append(float(risk_score))
                except:
                    pass
            
            if metadata.get('severity') == 'Red':
                red_alerts += 1
        
        if risk_scores:
            avg_risk = sum(risk_scores) / len(risk_scores)
            
            if avg_risk >= 7.0 or red_alerts >= 2:
                level = "CRITICAL"
            elif avg_risk >= 5.0 or red_alerts >= 1:
                level = "HIGH"
            elif avg_risk >= 3.0:
                level = "MODERATE"
            else:
                level = "LOW"
            
            return f"{level} - Average Risk Score: {avg_risk:.1f}/10 | Red Alerts: {red_alerts}"
        
        return None
    
    def analyze_disaster_image(
        self,
        image_url: str,
        event_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze disaster imagery using GPT-4 Vision.
        
        Args:
            image_url: URL to the disaster image
            context: Optional text context about the disaster event
            
        Returns:
            Dict with 'analysis', 'severity_indicators', 'key_observations'
        """
        try:
            from openai import OpenAI
            
            system_prompt = """You are an expert disaster analyst specializing in satellite and aerial imagery analysis.
Analyze the provided disaster imagery and provide detailed insights.

Focus on:
1. Visible disaster indicators (smoke, fire, flooding, damage)
2. Severity assessment based on visible scale and intensity
3. Geographic context and affected area estimation
4. Key observations that would help emergency responders

Be specific, factual, and actionable in your analysis."""
            
            user_content = []
            
            # Add text context if provided
            if event_context:
                user_content.append({
                    "type": "text",
                    "text": f"Context: {event_context}\n\nAnalyze this disaster imagery:"
                })
            
            # Add image
            user_content.append({
                "type": "image_url",
                "image_url": {"url": image_url}
            })
            
            response = self.client.chat.completions.create(
                model="gpt-4o",  # GPT-4 Vision model
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.2,
                max_tokens=500
            )
            
            analysis_text = response.choices[0].message.content.strip()
            
            # Parse analysis for structured output
            severity_indicators = self._extract_severity_from_analysis(analysis_text)
            observations = self._extract_observations_from_analysis(analysis_text)
            
            return {
                'analysis': analysis_text,
                'severity_indicators': severity_indicators,
                'key_observations': observations,
                'image_url': image_url,
                'model': 'gpt-4o'
            }
        
        except Exception as e:
            self.logger.log_error("OpenAILLM.analyze_disaster_image", e)
            return {
                'analysis': "Unable to analyze image due to an error.",
                'severity_indicators': [],
                'key_observations': [],
                'image_url': image_url,
                'model': 'gpt-4o',
                'error': str(e)
            }
    
    def _extract_severity_from_analysis(self, analysis_text: str) -> List[str]:
        """Extract severity indicators from analysis text."""
        indicators = []
        text_lower = analysis_text.lower()
        
        severity_keywords = {
            'severe': ['extensive', 'large-scale', 'widespread', 'intense'],
            'moderate': ['moderate', 'localized', 'contained'],
            'minor': ['minor', 'small', 'limited', 'isolated']
        }
        
        for severity, keywords in severity_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                indicators.append(severity)
        
        return indicators
    
    def _extract_observations_from_analysis(self, analysis_text: str) -> List[str]:
        """Extract key observations from analysis text."""
        # Simple extraction - look for bullet points or numbered lists
        observations = []
        lines = analysis_text.split('\n')
        
        for line in lines:
            line = line.strip()
            # Look for bullet points or numbered items
            if line.startswith(('-', '•', '*')) or (line and line[0].isdigit() and '.' in line[:3]):
                obs = line.lstrip('- •* 0123456789.')
                if obs:
                    observations.append(obs)
        
        # If no structured observations found, return first few sentences
        if not observations:
            sentences = analysis_text.split('.')[:3]
            observations = [s.strip() for s in sentences if s.strip()]
        
        return observations[:5]  # Limit to 5 observations
    
    def predict_disaster_impact(
        self,
        current_event: Dict[str, Any],
        similar_events: List[Dict[str, Any]]
    ) -> str:
        """
        Use RAG to predict impact based on historical similar disasters.
        Uses our AI model to analyze patterns and forecast outcomes.
        """
        try:
            # Build context from similar historical events
            historical_context_parts = []
            for i, evt in enumerate(similar_events[:3]):
                metadata = evt.get('metadata', {})
                historical_context_parts.append(
                    f"**Past Event {i+1}:**\n"
                    f"- Type: {metadata.get('disaster_type', 'Unknown')}\n"
                    f"- Location: {metadata.get('location_name') or metadata.get('location', 'Unknown')}\n"
                    f"- Severity: {metadata.get('severity', 'Unknown')}\n"
                    f"- Impact: {metadata.get('population_affected', 0)} people affected\n"
                    f"- Risk Score: {metadata.get('risk_score', 'N/A')}/10\n"
                    f"- Description: {evt.get('text', '')[:200]}"
                )
            
            historical_context = "\n\n".join(historical_context_parts)
            
            current_metadata = current_event.get('metadata', {})
            
            prompt = f"""Based on historical disaster data, predict the likely impact and trajectory of this current event:

**Current Disaster:**
- Type: {current_metadata.get('disaster_type', 'Unknown')}
- Location: {current_metadata.get('location_name') or current_metadata.get('location', 'Unknown')}
- Current Severity: {current_metadata.get('severity', 'Unknown')}
- Coordinates: {current_metadata.get('latitude', 'N/A')}, {current_metadata.get('longitude', 'N/A')}
- Current Risk Score: {current_metadata.get('risk_score', 'N/A')}/10

**Similar Historical Disasters:**
{historical_context if historical_context else 'No similar historical events found.'}

Provide a prediction covering:
1. **Expected Impact Scale** (population affected, infrastructure damage)
2. **Timeline** (how long will this disaster last/evolve)
3. **Secondary Risks** (cascading disasters, evacuation needs)
4. **Recommended Actions** (immediate response priorities)

Be specific and data-driven based on historical patterns. Format as JSON with keys: expected_impact, timeline, secondary_risks, recommended_actions."""
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a disaster prediction AI that analyzes historical patterns to forecast current disaster impacts. Use our AI model's predictive capabilities to provide accurate, data-driven forecasts."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,  # Low temperature for factual predictions
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            prediction_text = response.choices[0].message.content.strip()
            
            # Parse JSON response
            try:
                prediction_data = json.loads(prediction_text)
                # Format as readable text
                formatted = f"""**Expected Impact:** {prediction_data.get('expected_impact', 'Analysis in progress')}

**Timeline:** {prediction_data.get('timeline', 'Monitoring ongoing')}

**Secondary Risks:** {prediction_data.get('secondary_risks', 'None identified')}

**Recommended Actions:** {prediction_data.get('recommended_actions', 'Continue monitoring')}"""
                return formatted
            except json.JSONDecodeError:
                # Fallback to raw response
                return prediction_text
        
        except Exception as e:
            self.logger.log_error("OpenAILLM.predict_disaster_impact", e)
            return "Unable to generate prediction at this time. Please try again later."
        
        risk_scores = []
        red_alerts = 0
        
        for ctx in contexts:
            metadata = ctx.get('metadata', {})
            
            risk_score = metadata.get('risk_score')
            if risk_score:
                try:
                    risk_scores.append(float(risk_score))
                except:
                    pass
            
            if metadata.get('severity') == 'Red':
                red_alerts += 1
        
        if risk_scores:
            avg_risk = sum(risk_scores) / len(risk_scores)
            
            if avg_risk >= 7.0 or red_alerts >= 2:
                level = "CRITICAL"
            elif avg_risk >= 5.0 or red_alerts >= 1:
                level = "HIGH"
            elif avg_risk >= 3.0:
                level = "MODERATE"
            else:
                level = "LOW"
            
            return f"{level} - Average Risk Score: {avg_risk:.1f}/10 | Red Alerts: {red_alerts}"
        
        return None

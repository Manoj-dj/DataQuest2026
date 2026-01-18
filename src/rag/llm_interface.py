"""
OpenAI LLM interface for response generation.
Handles prompt construction, context injection, and response parsing.
Uses OpenAI GPT models for fast, reliable generation.
"""

from openai import OpenAI
from typing import List, Dict, Any, Optional
import time
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
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            answer = response.choices[0].message.content.strip()
            
            latency_ms = (time.time() - start_time) * 1000
            
            sources = self._extract_sources(retrieved_contexts)
            risk_assessment = self._extract_risk_assessment(retrieved_contexts)
            
            self.logger.log_query(query, latency_ms, len(sources))
            
            return {
                'answer': answer,
                'sources': sources,
                'risk_assessment': risk_assessment if include_risk_assessment else None,
                'latency_ms': latency_ms,
                'model': self.model_name
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

RESPONSE FORMAT (Use Markdown):
Format your response using clean, structured markdown:
- Use ## for main sections (e.g., ## Current Situation, ## Risk Assessment)
- Use ### for subsections
- Use **bold** for important information like locations, severities, magnitudes
- Use bullet points (-) for lists of events or recommendations
- Use numbered lists (1., 2., 3.) for step-by-step recommendations
- Write in clear, professional language
- Include specific numbers, dates, and locations
- End with actionable insights if applicable

Example format:
## Current Situation
Based on the latest data, there are [number] active disaster events...

**Key Events:**
- **Earthquake** (Severity: Red) - Location, magnitude X.X, affecting Y people
- **Wildfire** (Severity: Orange) - Location, Z hectares affected

## Risk Assessment
The earthquake poses a **high risk** due to...

## Recommendations
1. Monitor official sources for updates
2. Follow evacuation orders if applicable
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
            sources.append({
                'event_id': ctx.get('id', 'Unknown'),
                'disaster_type': metadata.get('disaster_type', 'Unknown'),
                'location': metadata.get('location', 'Unknown'),
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

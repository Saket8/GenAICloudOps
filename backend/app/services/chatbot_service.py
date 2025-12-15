import asyncio
import json
import re
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
import time

from app.core.database import get_db
from app.models.chatbot import (
    Conversation, ConversationMessage, ConversationIntent, QueryTemplate,
    ConversationAnalytics, ChatbotFeedback, MessageRole, IntentType, ConversationStatus
)
from app.models.user import User
from app.services.genai_service import genai_service, GenAIRequest, PromptType
from app.schemas.chatbot import (
    IntentResponse, EnhancedChatResponse, ConversationResponse, 
    MessageResponse, TemplateResponse
)
import logging

logger = logging.getLogger(__name__)


class ResourceContextCache:
    """
    Thread-safe cache for OCI resource context with TTL.
    Prevents repeated API calls and maintains performance.
    """
    
    def __init__(self, ttl_seconds: int = 60):
        self._cache: Dict[str, Any] = {}
        self._timestamps: Dict[str, float] = {}
        self._ttl = ttl_seconds
        self._lock = asyncio.Lock()
    
    def is_valid(self, key: str) -> bool:
        """Check if cached entry is still valid"""
        if key not in self._cache:
            return False
        age = time.time() - self._timestamps.get(key, 0)
        return age < self._ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value if valid"""
        if self.is_valid(key):
            return self._cache[key]
        return None
    
    async def set(self, key: str, value: Any):
        """Set cache value with timestamp"""
        async with self._lock:
            self._cache[key] = value
            self._timestamps[key] = time.time()
    
    def clear(self):
        """Clear all cached entries"""
        self._cache.clear()
        self._timestamps.clear()


# Global resource context cache - 60 second TTL for balance of freshness and performance
_resource_cache = ResourceContextCache(ttl_seconds=60)


class IntentRecognitionService:
    """Service for recognizing user intents from messages"""
    
    # Intent patterns for regex-based recognition
    INTENT_PATTERNS = {
        IntentType.INFRASTRUCTURE_QUERY: [
            r'\b(server|instance|compute|vm|virtual machine)s?\b',
            r'\b(network|subnet|vcn|vpc)s?\b',
            r'\b(storage|volume|bucket|object storage)s?\b',
            r'\b(database|db|autonomous)s?\b',
            r'\b(load balancer|lb|gateway|api gateway)s?\b',
            # Resource states - important for follow-up queries
            r'\b(running|stopped|terminated|starting|stopping|available|provisioning)s?\b',
            # General resource terms
            r'\b(resource|compartment|tenancy|oci|cloud)s?\b',
            # List/show/get commands
            r'\b(list|show|get|what|which|how many)\b.*\b(instance|server|db|database|vcn|network|storage|bucket|resource)s?\b',
        ],
        IntentType.TROUBLESHOOTING: [
            r'\b(error|issue|problem|fail|down|not working)\b',
            r'\b(troubleshoot|debug|fix|solve|resolve)\b',
            r'\b(crash|hang|timeout|slow)\b',
            r'\b(what\'s wrong|what happened|why)\b'
        ],
        IntentType.MONITORING_ALERT: [
            r'\b(alert|alarm|notification|warning)\b',
            r'\b(metric|cpu|memory|disk|utilization)\b',
            r'\b(threshold|exceeded|high|critical)\b'
        ],
        IntentType.COST_OPTIMIZATION: [
            r'\b(cost|expense|billing|budget)\b',
            r'\b(optimize|reduce|save|cheaper)\b',
            r'\b(usage|consumption|spending)\b'
        ],
        IntentType.REMEDIATION_REQUEST: [
            r'\b(fix|repair|remediate|resolve)\b',
            r'\b(automated|automatic|script)\b',
            r'\b(restart|stop|start|scale)\b'
        ],
        IntentType.RESOURCE_ANALYSIS: [
            r'\b(analyze|analysis|report|overview)\b',
            r'\b(performance|utilization|efficiency)\b',
            r'\b(resources|capacity|usage)\b'
        ],
        IntentType.HELP_REQUEST: [
            r'\b(help|how to|how do|guide|tutorial)\b',
            r'\b(explain|show me|what is|documentation)\b'
        ],
        # Explicit GENERAL_CHAT patterns - greetings, casual conversation
        IntentType.GENERAL_CHAT: [
            r'^(hi|hello|hey|good morning|good afternoon|good evening)\b',
            r'\b(thank you|thanks|bye|goodbye|cheers)\b',
            r'^(who are you|what can you do|what are you)\b',
            r'\b(weather|joke|fun|chat|talk)\b',
        ]
    }
    
    def recognize_intent(self, message: str) -> Tuple[IntentType, float, Dict[str, Any]]:
        """Recognize intent from message using pattern matching"""
        message_lower = message.lower()
        best_intent = IntentType.GENERAL_CHAT
        best_score = 0.1
        entities = {}
        
        # Extract potential entities
        entities.update(self._extract_entities(message))
        
        # Check each intent pattern
        for intent_type, patterns in self.INTENT_PATTERNS.items():
            score = 0
            matches = 0
            
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    matches += 1
                    score += 0.2
            
            # Bonus for multiple pattern matches
            if matches > 1:
                score += 0.3
            
            # Context-based scoring improvements
            if intent_type == IntentType.INFRASTRUCTURE_QUERY and any(
                keyword in message_lower for keyword in ['oci', 'oracle', 'compartment', 'tenancy']
            ):
                score += 0.2
                
            if intent_type == IntentType.TROUBLESHOOTING and any(
                keyword in message_lower for keyword in ['down', 'failing', 'not responding']
            ):
                score += 0.3
            
            if score > best_score:
                best_score = score
                best_intent = intent_type
        
        # Cap confidence at 0.95 for pattern-based recognition
        confidence = min(best_score, 0.95)
        
        return best_intent, confidence, entities
    
    def _extract_entities(self, message: str) -> Dict[str, Any]:
        """Extract entities from message"""
        entities = {}
        
        # Extract OCI-specific entities
        compartment_match = re.search(r'compartment[:\s]+([a-zA-Z0-9\-._]+)', message, re.IGNORECASE)
        if compartment_match:
            entities['compartment_id'] = compartment_match.group(1)
        
        # Extract resource names
        resource_patterns = {
            'instance_name': r'instance[:\s]+([a-zA-Z0-9\-._]+)',
            'service_name': r'service[:\s]+([a-zA-Z0-9\-._]+)',
            'resource_name': r'resource[:\s]+([a-zA-Z0-9\-._]+)'
        }
        
        for entity_type, pattern in resource_patterns.items():
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                entities[entity_type] = match.group(1)
        
        return entities

class ChatbotService:
    """Enhanced chatbot service with advanced conversation management"""
    
    def __init__(self):
        self.intent_service = IntentRecognitionService()
        self.default_templates = self._load_default_templates()
    
    async def enhanced_chat(
        self,
        message: str,
        user_id: int,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        oci_context: Optional[Dict[str, Any]] = None,
        enable_intent_recognition: bool = True,
        use_templates: bool = True
    ) -> EnhancedChatResponse:
        """Enhanced chat with full conversation management and intent recognition"""
        
        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
        
        db = next(get_db())
        try:
            # Get or create conversation
            conversation = self._get_or_create_conversation(db, session_id, user_id, context)
            
            # Intent recognition
            intent_response = None
            if enable_intent_recognition:
                intent_type, confidence, entities = self.intent_service.recognize_intent(message)
                intent_response = IntentResponse(
                    intent_type=intent_type,
                    confidence_score=confidence,
                    entities=entities
                )
                
                # Store intent in database
                db_intent = ConversationIntent(
                    conversation_id=conversation.id,
                    intent_type=intent_type,
                    confidence_score=confidence,
                    entities=entities
                )
                db.add(db_intent)
            
            # AUTO-FETCH: Enhanced logic for resource-aware responses
            # 1. Always check cache first (for follow-up questions)
            # 2. Fetch fresh data if intent is infrastructure-related
            # 3. Use cached context for ANY query to maintain conversation continuity
            
            should_fetch_fresh = intent_response and intent_response.intent_type in [
                IntentType.INFRASTRUCTURE_QUERY,
                IntentType.RESOURCE_ANALYSIS,
                IntentType.MONITORING_ALERT,
                IntentType.TROUBLESHOOTING,
                IntentType.REMEDIATION_REQUEST
            ]
            
            if oci_context is None:
                # Check if we have cached context (useful for follow-up questions)
                cached_context = _resource_cache.get("oci_resources_summary")
                
                if cached_context:
                    # Use cached context for all queries (enables follow-up questions)
                    oci_context = cached_context
                    logger.info("Using cached OCI context for query")
                elif should_fetch_fresh:
                    # Fetch fresh data for infrastructure-related queries
                    try:
                        oci_context = await self._auto_fetch_resource_context(
                            message, intent_response
                        )
                        logger.info(f"Auto-fetched OCI context for intent: {intent_response.intent_type.value}")
                    except Exception as e:
                        logger.warning(f"Failed to auto-fetch OCI context: {e}")
                        # Continue without context - graceful degradation
            
            # Enhanced prompt with OCI context
            enhanced_prompt = await self._build_enhanced_prompt(
                message, conversation, oci_context, intent_response
            )
            
            # Generate AI response
            ai_response = await genai_service.chat_completion(
                message=enhanced_prompt,
                session_id=session_id,
                user_id=str(user_id),
                context=context
            )
            
            # Store user message
            user_message = ConversationMessage(
                conversation_id=conversation.id,
                role=MessageRole.USER,
                content=message,
                context_snapshot=context
            )
            db.add(user_message)
            
            # Store AI response
            ai_message = ConversationMessage(
                conversation_id=conversation.id,
                role=MessageRole.ASSISTANT,
                content=ai_response.content,
                model_used=ai_response.model,
                tokens_used=ai_response.tokens_used,
                response_time=ai_response.response_time,
                cached=ai_response.cached,
                context_snapshot=oci_context
            )
            db.add(ai_message)
            
            # Update conversation stats
            conversation.total_messages += 2
            conversation.total_tokens_used += ai_response.tokens_used
            conversation.last_activity = datetime.utcnow()
            
            # Update intent message reference
            if intent_response:
                db_intent.message_id = user_message.id
            
            db.commit()
            
            # Get template suggestions
            suggested_templates = []
            if use_templates and intent_response:
                suggested_templates = self._get_template_suggestions(
                    db, intent_response.intent_type, user_id
                )
            
            # Generate OCI insights if context provided
            oci_insights = None
            if oci_context and intent_response and intent_response.intent_type in [
                IntentType.INFRASTRUCTURE_QUERY, IntentType.RESOURCE_ANALYSIS
            ]:
                oci_insights = await self._generate_oci_insights(oci_context)
            
            return EnhancedChatResponse(
                response=ai_response.content,
                session_id=session_id,
                conversation_id=conversation.id,
                model=ai_response.model,
                tokens_used=ai_response.tokens_used,
                response_time=ai_response.response_time,
                cached=ai_response.cached,
                intent=intent_response,
                suggested_templates=suggested_templates,
                oci_insights=oci_insights
            )
            
        except Exception as e:
            db.rollback()
            logger.error(f"Enhanced chat error: {e}")
            raise
        finally:
            db.close()
    
    def _get_or_create_conversation(
        self, 
        db: Session, 
        session_id: str, 
        user_id: int, 
        context: Optional[Dict[str, Any]]
    ) -> Conversation:
        """Get existing conversation or create new one"""
        conversation = db.query(Conversation).filter(
            Conversation.session_id == session_id
        ).first()
        
        if not conversation:
            conversation = Conversation(
                session_id=session_id,
                user_id=user_id,
                context=context,
                status=ConversationStatus.ACTIVE
            )
            db.add(conversation)
            db.flush()  # To get the ID
        
        return conversation
    
    async def _build_enhanced_prompt(
        self,
        message: str,
        conversation: Conversation,
        oci_context: Optional[Dict[str, Any]],
        intent: Optional[IntentResponse]
    ) -> str:
        """Build enhanced prompt with OCI context and conversation history"""
        
        # Determine if this is an infrastructure query or general chat
        is_infrastructure_query = intent and intent.intent_type in [
            IntentType.INFRASTRUCTURE_QUERY,
            IntentType.RESOURCE_ANALYSIS,
            IntentType.MONITORING_ALERT,
            IntentType.TROUBLESHOOTING,
            IntentType.REMEDIATION_REQUEST,
            IntentType.COST_OPTIMIZATION
        ]
        
        # Build appropriate system preamble based on query type
        if is_infrastructure_query and oci_context and oci_context.get("resources"):
            # INFRASTRUCTURE MODE: Use live OCI data
            enhanced_prompt = """You are an AI assistant for the GenAI CloudOps dashboard with LIVE ACCESS to the user's actual OCI (Oracle Cloud Infrastructure) resources.

🔹 MODE: INFRASTRUCTURE QUERY

IMPORTANT INSTRUCTIONS:
1. USE THE ACTUAL RESOURCE DATA provided below to answer questions.
2. Reference SPECIFIC resource names, states, and counts from the context.
3. DO NOT give generic web-based instructions - the user has direct dashboard access.
4. List ACTUAL resources with their real names and states.
5. Be concise and factual based on the live data.

"""
            enhanced_prompt += "=== LIVE OCI RESOURCE DATA ===\n"
            enhanced_prompt += f"{json.dumps(oci_context, indent=2)}\n"
            enhanced_prompt += "=== END LIVE DATA ===\n\n"
            
        else:
            # GENERAL CHAT MODE: Friendly conversation
            enhanced_prompt = """You are a friendly AI assistant for the GenAI CloudOps dashboard.

🔹 MODE: GENERAL CONVERSATION

You help with:
- General questions about cloud operations concepts
- Explaining OCI/cloud terminology
- Providing guidance on best practices
- Friendly conversation and greetings

Note: For specific infrastructure questions (like "show my instances"), suggest asking directly about resources so I can fetch live data.

"""
        
        # User's actual question
        enhanced_prompt += f"USER QUESTION: {message}\n\n"
        
        # Add intent context
        if intent and intent.confidence_score > 0.3:
            enhanced_prompt += f"Detected Intent: {intent.intent_type.value} (confidence: {intent.confidence_score:.0%})\n"
            if intent.entities:
                enhanced_prompt += f"Entities: {json.dumps(intent.entities)}\n"
            enhanced_prompt += "\n"
        
        # Add conversation context
        if conversation.context:
            enhanced_prompt += f"Previous Context: {json.dumps(conversation.context)}\n\n"
        
        # Add system instructions based on intent
        if intent:
            system_instructions = self._get_system_instructions(intent.intent_type)
            enhanced_prompt += f"Additional Guidance: {system_instructions}\n\n"
        
        enhanced_prompt += "Provide a helpful, SPECIFIC response using the actual resource data above."
        
        return enhanced_prompt
    
    def _get_system_instructions(self, intent_type: IntentType) -> str:
        """Get system instructions based on intent type"""
        instructions = {
            IntentType.INFRASTRUCTURE_QUERY: "Focus on providing accurate information about cloud infrastructure components, their configurations, and relationships.",
            IntentType.TROUBLESHOOTING: "Analyze the problem systematically, suggest diagnostic steps, and provide clear resolution paths.",
            IntentType.MONITORING_ALERT: "Interpret monitoring data, explain alert conditions, and suggest appropriate responses.",
            IntentType.COST_OPTIMIZATION: "Analyze cost patterns, identify optimization opportunities, and provide actionable recommendations.",
            IntentType.REMEDIATION_REQUEST: "Suggest specific remediation actions, consider safety and approval requirements.",
            IntentType.RESOURCE_ANALYSIS: "Provide comprehensive analysis of resource usage, performance, and optimization opportunities.",
            IntentType.HELP_REQUEST: "Provide clear, step-by-step guidance and educational information."
        }
        return instructions.get(intent_type, "Provide helpful and accurate information.")
    
    async def _auto_fetch_resource_context(
        self,
        message: str,
        intent: IntentResponse
    ) -> Dict[str, Any]:
        """
        Automatically fetch OCI resource context based on query intent.
        Uses caching and parallel fetching for optimal performance.
        """
        global _resource_cache
        
        # Check cache first
        cache_key = "oci_resources_summary"
        cached = _resource_cache.get(cache_key)
        if cached:
            logger.info("Using cached OCI resource context")
            return cached
        
        context = {
            "timestamp": datetime.utcnow().isoformat(),
            "resources": {}
        }
        
        try:
            # Import OCI service lazily to avoid circular imports
            from app.services.cloud_service import get_oci_service
            oci_service = get_oci_service()
            
            if not oci_service.oci_available:
                logger.warning("OCI service not available, returning empty context")
                return context
            
            # Get compartments first (needed for queries)
            compartments = await oci_service.get_compartments()
            if not compartments:
                logger.warning("No compartments found")
                return context
            
            # Use first compartment or tenancy root
            compartment_id = oci_service.config.get('tenancy') if oci_service.config else compartments[0]['id']
            logger.info(f"Fetching resources for context from compartment: {compartment_id[:20]}...")
            
            # Fetch all resources using the existing parallel method
            try:
                all_resources = await oci_service.get_all_resources(compartment_id)
                resources = all_resources.get('resources', {})
                
                # Process compute instances
                instances = resources.get('compute_instances', [])
                if instances:
                    context["resources"]["compute_instances"] = {
                        "count": len(instances),
                        "items": [
                            {
                                "name": inst.get("display_name", "Unknown"),
                                "state": inst.get("lifecycle_state", "UNKNOWN"),
                                "shape": inst.get("shape", "Unknown")
                            }
                            for inst in instances[:15]  # Limit for token efficiency
                        ],
                        "summary": f"{len(instances)} instances ({sum(1 for i in instances if i.get('lifecycle_state') == 'RUNNING')} running)"
                    }
                
                # Process databases
                databases = resources.get('databases', [])
                if databases:
                    context["resources"]["databases"] = {
                        "count": len(databases),
                        "items": [
                            {
                                "name": db.get("display_name", "Unknown"),
                                "state": db.get("lifecycle_state", "UNKNOWN"),
                                "type": db.get("db_workload", "Unknown")
                            }
                            for db in databases[:10]
                        ],
                        "summary": f"{len(databases)} databases"
                    }
                
                # Process VCNs/Networks
                vcns = resources.get('vcns', [])
                if vcns:
                    context["resources"]["networks"] = {
                        "count": len(vcns),
                        "items": [
                            {
                                "name": vcn.get("display_name", "Unknown"),
                                "cidr": vcn.get("cidr_block", "Unknown"),
                                "state": vcn.get("lifecycle_state", "UNKNOWN")
                            }
                            for vcn in vcns[:5]
                        ],
                        "summary": f"{len(vcns)} VCNs"
                    }
                
                # Process storage (buckets + block volumes)
                buckets = resources.get('object_storage_buckets', [])
                block_volumes = resources.get('block_volumes', [])
                if buckets or block_volumes:
                    context["resources"]["storage"] = {
                        "buckets": len(buckets),
                        "block_volumes": len(block_volumes),
                        "summary": f"{len(buckets)} buckets, {len(block_volumes)} block volumes"
                    }
                
                logger.info(f"Successfully fetched OCI context: {len(context['resources'])} resource types")
                
            except Exception as e:
                logger.error(f"Failed to fetch all resources: {e}")
                # Continue with empty but valid context
            
            # Fetch alerts separately (monitoring service)
            try:
                from app.services.monitoring_service import get_monitoring_service
                monitoring = get_monitoring_service()
                alert_data = await monitoring.get_alert_summary(compartment_id)
                alarms = alert_data.get('all_alerts', []) if alert_data else []
                if alarms:
                    context["resources"]["alerts"] = {
                        "count": len(alarms),
                        "items": [
                            {
                                "name": a.get("title", a.get("display_name", "Unknown")),
                                "severity": a.get("severity", "INFO"),
                                "status": a.get("status", "UNKNOWN")
                            }
                            for a in alarms[:10]
                        ],
                        "summary": f"{len(alarms)} alerts"
                    }
            except Exception as e:
                logger.warning(f"Failed to fetch alerts: {e}")
            
            # Cache the result for 60 seconds
            if context.get("resources"):
                await _resource_cache.set(cache_key, context)
            
            return context
            
        except Exception as e:
            logger.error(f"Error in auto-fetch resource context: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return context
    
    def _get_template_suggestions(
        self, 
        db: Session, 
        intent_type: IntentType, 
        user_id: int
    ) -> List[TemplateResponse]:
        """Get relevant template suggestions based on intent"""
        
        # Map intents to categories
        category_map = {
            IntentType.INFRASTRUCTURE_QUERY: "Infrastructure",
            IntentType.TROUBLESHOOTING: "Troubleshooting",
            IntentType.MONITORING_ALERT: "Monitoring",
            IntentType.COST_OPTIMIZATION: "Cost",
            IntentType.REMEDIATION_REQUEST: "Remediation",
            IntentType.RESOURCE_ANALYSIS: "Analysis"
        }
        
        category = category_map.get(intent_type)
        if not category:
            return []
        
        # Get user's role for permission filtering
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return []
        
        user_roles = [ur.role.name for ur in user.user_roles]
        
        # Query templates
        query = db.query(QueryTemplate).filter(
            QueryTemplate.category == category,
            QueryTemplate.is_active == True
        )
        
        # Filter by role requirements
        if 'admin' not in user_roles:
            query = query.filter(
                (QueryTemplate.requires_role.is_(None)) |
                (QueryTemplate.requires_role.in_(user_roles))
            )
        
        templates = query.order_by(desc(QueryTemplate.usage_count)).limit(3).all()
        
        return [
            TemplateResponse(
                id=t.id,
                name=t.name,
                description=t.description,
                category=t.category,
                template_text=t.template_text,
                variables=t.variables,
                usage_count=t.usage_count,
                requires_role=t.requires_role,
                is_active=t.is_active,
                created_at=t.created_at,
                updated_at=t.updated_at
            )
            for t in templates
        ]
    
    async def _generate_oci_insights(self, oci_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate OCI-specific insights based on context"""
        try:
            # Import OCI services lazily to avoid circular imports
            from app.services.cloud_service import get_cloud_service
            from app.services.monitoring_service import get_monitoring_service
            
            cloud_service = get_cloud_service()
            monitoring_service = get_monitoring_service()
            
            insights = {}
            
            # Get compartment information if available
            if 'compartment_id' in oci_context:
                compartment_id = oci_context['compartment_id']
                
                # Get basic compartment info
                try:
                    compartment_info = await cloud_service.get_compartment_details(compartment_id)
                    insights['compartment'] = compartment_info
                except Exception as e:
                    logger.warning(f"Could not get compartment details: {e}")
                
                # Get current alerts
                try:
                    alerts = await monitoring_service.get_alert_summary(compartment_id)
                    insights['alerts'] = alerts
                except Exception as e:
                    logger.warning(f"Could not get alert summary: {e}")
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating OCI insights: {e}")
            return {}
    
    def _load_default_templates(self) -> List[Dict[str, Any]]:
        """Load default query templates"""
        return [
            {
                "name": "Check Instance Status",
                "category": "Infrastructure",
                "description": "Check the status of compute instances",
                "template_text": "What is the current status of instance {instance_name} in compartment {compartment_id}?",
                "variables": {"instance_name": "string", "compartment_id": "string"}
            },
            {
                "name": "Analyze High CPU",
                "category": "Troubleshooting",
                "description": "Analyze high CPU utilization",
                "template_text": "Why is {resource_name} showing high CPU utilization and how can I fix it?",
                "variables": {"resource_name": "string"}
            },
            {
                "name": "Cost Analysis",
                "category": "Cost",
                "description": "Analyze costs for a compartment",
                "template_text": "Analyze the costs for compartment {compartment_id} and suggest optimizations",
                "variables": {"compartment_id": "string"}
            },
            {
                "name": "Alert Investigation",
                "category": "Monitoring",
                "description": "Investigate monitoring alerts",
                "template_text": "Investigate the {alert_type} alert for {resource_name} and suggest remediation",
                "variables": {"alert_type": "string", "resource_name": "string"}
            }
        ]

# Global service instance - lazy loading
_chatbot_service = None

def get_chatbot_service() -> ChatbotService:
    """Get chatbot service instance with lazy loading"""
    global _chatbot_service
    if _chatbot_service is None:
        _chatbot_service = ChatbotService()
    return _chatbot_service

# Access via function call only - don't instantiate at module level 
"""
Diagnostic Agent for Rift
Diagnoses root causes of infrastructure incidents using RAG and AI analysis
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from agents.base_agent import BaseAgent
from mcp_clients.terraform_mcp import TerraformMCP
from mcp_clients.do_mcp import DigitalOceanMCP
from models.incident import (
    Incident,
    Diagnosis,
    KnowledgeEntry,
    RemediationPlan,
    RemediationAction,
    MetricType,
    ResourceType
)

logger = logging.getLogger("rift.agents.diagnostic")


class DiagnosticAgent(BaseAgent):
    """
    Diagnostic Agent for analyzing infrastructure incidents.
    Uses RAG (Retrieval Augmented Generation) to find similar past incidents
    and recommend remediation strategies.
    """

    def __init__(
        self,
        agent_endpoint: str,
        agent_key: str,
        agent_id: str,
        knowledge_base_id: str,
        terraform_mcp: TerraformMCP,
        do_mcp: DigitalOceanMCP
    ):
        """
        Initialize Diagnostic Agent.

        Args:
            agent_endpoint: Gradient AI agent endpoint URL
            agent_key: API key for authentication
            agent_id: Unique agent identifier
            knowledge_base_id: Knowledge base ID for RAG
            terraform_mcp: Terraform MCP client instance
            do_mcp: DigitalOcean MCP client instance
        """
        super().__init__(
            agent_endpoint=agent_endpoint,
            agent_key=agent_key,
            agent_id=agent_id,
            agent_name="Diagnostic Agent",
            knowledge_base_id=knowledge_base_id
        )

        self.terraform_mcp = terraform_mcp
        self.do_mcp = do_mcp

        logger.info("Diagnostic Agent initialized with knowledge base")

    async def diagnose_incident(self, incident: Incident) -> Diagnosis:
        """
        Diagnose an infrastructure incident.

        Args:
            incident: The incident to diagnose

        Returns:
            Diagnosis with root cause analysis and recommendations
        """
        try:
            logger.info(f"Diagnosing incident {incident.id}: {incident.description}")

            # Step 1: Query knowledge base for similar incidents
            kb_matches = await self.query_knowledge_base(
                f"Similar incidents: {incident.metric.value} {incident.resource_type.value} "
                f"{incident.current_value}% severity {incident.severity.value}"
            )

            # Step 2: Analyze current infrastructure state
            state_analysis = await self.analyze_infrastructure_state(incident)

            # Step 3: Use AI to diagnose with all context
            diagnosis_prompt = self._build_diagnosis_prompt(incident, kb_matches, state_analysis)

            ai_response = await self.query_agent(
                prompt=diagnosis_prompt,
                use_knowledge_base=True
            )

            # Step 4: Parse AI response
            diagnosis_text = ai_response.get("response", "")

            # Extract structured information from AI response
            root_cause, root_cause_category, reasoning, recommendations = self._parse_diagnosis(diagnosis_text)

            # Step 5: Calculate confidence score
            confidence = await self.calculate_confidence(
                kb_matches=kb_matches,
                state_analysis=state_analysis,
                diagnosis_text=diagnosis_text
            )

            # Step 6: Estimate cost and duration
            estimated_cost, estimated_duration = await self._estimate_remediation(
                incident=incident,
                recommendations=recommendations
            )

            # Create diagnosis object
            diagnosis = Diagnosis(
                incident_id=incident.id,
                root_cause=root_cause,
                root_cause_category=root_cause_category,
                confidence=confidence,
                reasoning=reasoning,
                knowledge_base_matches=kb_matches,
                recommendations=recommendations,
                estimated_cost=estimated_cost,
                estimated_duration=estimated_duration,
                metadata={
                    "state_analysis": state_analysis,
                    "ai_full_response": diagnosis_text,
                    "infrastructure_state": state_analysis,  # Include droplet info for remediation
                    "droplet_id": incident.resource_id,
                    "resource_type": incident.resource_type.value
                }
            )

            logger.info(f"Diagnosis complete: {root_cause} (confidence: {confidence:.2f})")
            return diagnosis

        except Exception as e:
            logger.error(f"Failed to diagnose incident {incident.id}: {str(e)}")
            raise

    async def query_knowledge_base(self, query: str) -> List[KnowledgeEntry]:
        """
        Query the knowledge base for relevant information.

        Args:
            query: Search query

        Returns:
            List of relevant knowledge entries
        """
        try:
            logger.debug(f"Querying knowledge base: {query}")

            # Query the AI agent with RAG enabled
            response = await self.query_agent(
                prompt=f"Search knowledge base for: {query}\n\nProvide the most relevant troubleshooting information and past incident resolutions.",
                use_knowledge_base=True
            )

            # Parse response to extract knowledge entries
            # For now, create a single entry from the response
            # In production, the Gradient AI platform would return structured retrieval info
            entries = [
                KnowledgeEntry(
                    content=response.get("response", ""),
                    source="knowledge_base",
                    relevance_score=0.8,  # Would come from actual RAG system
                    metadata={"query": query}
                )
            ]

            logger.info(f"Retrieved {len(entries)} knowledge base entries")
            return entries

        except Exception as e:
            logger.error(f"Failed to query knowledge base: {str(e)}")
            return []

    async def analyze_infrastructure_state(self, incident: Incident) -> Dict[str, Any]:
        """
        Analyze current infrastructure state related to the incident.

        Args:
            incident: The incident being analyzed

        Returns:
            State analysis dictionary
        """
        try:
            logger.debug(f"Analyzing infrastructure state for {incident.resource_name}")

            analysis = {
                "resource_type": incident.resource_type.value,
                "resource_id": incident.resource_id,
                "resource_name": incident.resource_name,
                "timestamp": datetime.utcnow().isoformat()
            }

            # Get resource details based on type
            if incident.resource_type == ResourceType.DROPLET:
                # Check if this is a demo incident (metadata.demo = true) or if resource_id is not numeric
                is_demo = incident.metadata and incident.metadata.get("demo", False)
                try:
                    droplet_id = int(incident.resource_id) if not is_demo else None
                except (ValueError, TypeError):
                    droplet_id = None
                
                if droplet_id:
                    droplet = await self.do_mcp.get_droplet(droplet_id)
                    
                    # Extract public IP address
                    droplet_ip = None
                    networks = droplet.get("networks", {}).get("v4", [])
                    for network in networks:
                        if network.get("type") == "public":
                            droplet_ip = network.get("ip_address")
                            break
                    
                    analysis.update({
                        "current_size": droplet.get("size", {}).get("slug"),
                        "vcpus": droplet.get("vcpus"),
                        "memory_mb": droplet.get("memory"),
                        "disk_gb": droplet.get("disk"),
                        "region": droplet.get("region", {}).get("slug"),
                        "status": droplet.get("status"),
                        "created_at": droplet.get("created_at"),
                        "features": droplet.get("features", []),
                        "tags": droplet.get("tags", []),
                        "droplet_ip": droplet_ip,  # Add IP for remediation
                        "networks": droplet.get("networks", {})  # Full network info
                    })
                else:
                    # Demo incident - use simulated data
                    analysis.update({
                        "current_size": "s-1vcpu-1gb",
                        "vcpus": 1,
                        "memory_mb": 1024,
                        "disk_gb": 25,
                        "region": "nyc3",
                        "status": "active",
                        "demo_mode": True
                    })

            # Add metric-specific analysis
            analysis["affected_metric"] = incident.metric.value
            analysis["current_value"] = incident.current_value
            analysis["threshold_value"] = incident.threshold_value
            analysis["overage_percent"] = ((incident.current_value - incident.threshold_value) / incident.threshold_value) * 100

            logger.info(f"State analysis complete for {incident.resource_name}")
            return analysis

        except Exception as e:
            logger.error(f"Failed to analyze infrastructure state: {str(e)}")
            return {"error": str(e)}

    async def calculate_confidence(
        self,
        kb_matches: List[KnowledgeEntry],
        state_analysis: Dict[str, Any],
        diagnosis_text: str
    ) -> float:
        """
        Calculate confidence score for the diagnosis.

        Formula:
        confidence = (0.4 * kb_match_score) +
                     (0.3 * state_validation_score) +
                     (0.3 * ai_confidence_score)

        Args:
            kb_matches: Knowledge base matches
            state_analysis: Infrastructure state analysis
            diagnosis_text: AI diagnosis text

        Returns:
            Confidence score between 0.0 and 1.0
        """
        try:
            # Knowledge base match score (based on number and relevance of matches)
            if kb_matches:
                avg_relevance = sum(m.relevance_score for m in kb_matches) / len(kb_matches)
                match_count_factor = min(len(kb_matches) / 3, 1.0)  # Cap at 3 matches
                kb_score = (avg_relevance * 0.7) + (match_count_factor * 0.3)
            else:
                kb_score = 0.3  # Low confidence without KB matches

            # State validation score (based on completeness of state analysis)
            required_fields = ["resource_type", "current_size", "affected_metric"]
            present_fields = sum(1 for field in required_fields if field in state_analysis and state_analysis.get(field))
            state_score = present_fields / len(required_fields)

            # AI confidence score (based on certainty indicators in diagnosis text)
            certainty_indicators = ["definitely", "clearly", "obviously", "certainly", "confirmed"]
            uncertainty_indicators = ["possibly", "might", "maybe", "unclear", "uncertain"]

            certainty_count = sum(1 for indicator in certainty_indicators if indicator in diagnosis_text.lower())
            uncertainty_count = sum(1 for indicator in uncertainty_indicators if indicator in diagnosis_text.lower())

            if certainty_count + uncertainty_count > 0:
                ai_score = certainty_count / (certainty_count + uncertainty_count)
            else:
                ai_score = 0.6  # Neutral confidence if no indicators

            # Combine scores with weights
            confidence = (0.4 * kb_score) + (0.3 * state_score) + (0.3 * ai_score)

            # Ensure confidence is between 0 and 1
            confidence = max(0.0, min(1.0, confidence))

            logger.debug(f"Confidence calculation: KB={kb_score:.2f}, State={state_score:.2f}, AI={ai_score:.2f} → {confidence:.2f}")
            return confidence

        except Exception as e:
            logger.error(f"Failed to calculate confidence: {str(e)}")
            return 0.5  # Return neutral confidence on error

    async def generate_remediation_plan(self, diagnosis: Diagnosis) -> RemediationPlan:
        """
        Generate a remediation plan based on the diagnosis.

        Args:
            diagnosis: The diagnosis to create a plan for

        Returns:
            RemediationPlan with action steps
        """
        try:
            logger.info(f"Generating remediation plan for diagnosis {diagnosis.id}")

            # Use AI to generate remediation plan
            plan_prompt = f"""
            Based on this diagnosis:

            Root Cause: {diagnosis.root_cause}
            Category: {diagnosis.root_cause_category}
            Confidence: {diagnosis.confidence:.2f}
            Recommendations: {', '.join(diagnosis.recommendations)}

            Generate a detailed remediation plan with:
            1. Specific action to take
            2. Safety checks required
            3. Rollback plan
            4. Terraform configuration (if applicable)

            Be specific and actionable.
            """

            ai_response = await self.query_agent(
                prompt=plan_prompt,
                use_knowledge_base=True
            )

            plan_text = ai_response.get("response", "")

            # Determine remediation action type
            action = self._determine_remediation_action(diagnosis.root_cause_category, plan_text)

            # Extract parameters from plan
            parameters = self._extract_remediation_parameters(plan_text, diagnosis)

            # Build safety checks
            safety_checks = [
                "Validate Terraform configuration",
                "Check estimated cost is within acceptable range",
                "Verify no destructive operations on production resources",
                "Ensure rollback plan is available"
            ]

            # Build rollback plan
            rollback_plan = {
                "description": "Rollback to previous state using Terraform state file",
                "steps": [
                    "terraform state pull > rollback.tfstate",
                    "terraform apply -auto-approve rollback.tfstate"
                ]
            }

            # Determine if approval is required (based on cost and destructive operations)
            requires_approval = (
                diagnosis.estimated_cost and diagnosis.estimated_cost > 50.0
            ) or action == RemediationAction.UPDATE_FIREWALL

            plan = RemediationPlan(
                diagnosis_id=diagnosis.id,
                incident_id=diagnosis.incident_id,
                action=action,
                action_description=plan_text[:500],  # Truncate if too long
                parameters=parameters,
                safety_checks=safety_checks,
                rollback_plan=rollback_plan,
                requires_approval=requires_approval,
                estimated_cost=diagnosis.estimated_cost,
                estimated_duration=diagnosis.estimated_duration
            )

            logger.info(f"Remediation plan created: {action.value} (approval required: {requires_approval})")
            return plan

        except Exception as e:
            logger.error(f"Failed to generate remediation plan: {str(e)}")
            raise

    def _build_diagnosis_prompt(
        self,
        incident: Incident,
        kb_matches: List[KnowledgeEntry],
        state_analysis: Dict[str, Any]
    ) -> str:
        """Build comprehensive diagnosis prompt for AI."""

        kb_context = "\n\n".join([
            f"Knowledge Base Entry {i+1}:\n{entry.content}"
            for i, entry in enumerate(kb_matches[:3])  # Top 3 matches
        ]) if kb_matches else "No similar past incidents found."

        return f"""
        Analyze this infrastructure incident and provide a detailed diagnosis:

        INCIDENT DETAILS:
        - Resource: {incident.resource_name} ({incident.resource_type.value})
        - Metric: {incident.metric.value}
        - Current Value: {incident.current_value:.2f}%
        - Threshold: {incident.threshold_value:.2f}%
        - Severity: {incident.severity.value}
        - Description: {incident.description}

        CURRENT INFRASTRUCTURE STATE:
        {self._format_state_analysis(state_analysis)}

        KNOWLEDGE BASE CONTEXT:
        {kb_context}

        Provide your diagnosis in this format:

        ROOT CAUSE: [One sentence describing the root cause]
        CATEGORY: [capacity/performance/configuration/security/other]
        REASONING: [Detailed explanation of how you reached this conclusion]
        RECOMMENDATIONS: [Numbered list of 2-3 specific actionable recommendations]
        """

    def _format_state_analysis(self, state: Dict[str, Any]) -> str:
        """Format state analysis for prompt."""
        return "\n".join([f"- {key}: {value}" for key, value in state.items() if not key.startswith("_")])

    def _parse_diagnosis(self, diagnosis_text: str) -> tuple[str, str, str, List[str]]:
        """Parse AI diagnosis response into structured components."""

        lines = diagnosis_text.split('\n')
        root_cause = ""
        category = ""
        reasoning = ""
        recommendations = []

        current_section = None

        for line in lines:
            line = line.strip()

            if line.startswith("ROOT CAUSE:"):
                root_cause = line.replace("ROOT CAUSE:", "").strip()
                current_section = "root_cause"
            elif line.startswith("CATEGORY:"):
                category = line.replace("CATEGORY:", "").strip().lower()
                current_section = "category"
            elif line.startswith("REASONING:"):
                reasoning = line.replace("REASONING:", "").strip()
                current_section = "reasoning"
            elif line.startswith("RECOMMENDATIONS:"):
                current_section = "recommendations"
            elif current_section == "reasoning" and line:
                reasoning += " " + line
            elif current_section == "recommendations" and line:
                # Extract numbered recommendations
                if line[0].isdigit() or line.startswith("-") or line.startswith("•"):
                    rec = line.lstrip("0123456789.-•) ").strip()
                    if rec:
                        recommendations.append(rec)

        # Fallbacks
        if not root_cause:
            root_cause = f"High {diagnosis_text.split()[0] if diagnosis_text else 'resource'} usage detected"
        if not category:
            category = "performance"
        if not reasoning:
            reasoning = diagnosis_text[:200]
        if not recommendations:
            recommendations = ["Scale up resources", "Investigate resource usage", "Enable monitoring"]

        return root_cause, category, reasoning.strip(), recommendations

    def _determine_remediation_action(self, category: str, plan_text: str) -> RemediationAction:
        """Determine the remediation action type from category and plan."""

        plan_lower = plan_text.lower()

        if "resize" in plan_lower or "scale" in plan_lower:
            return RemediationAction.RESIZE_DROPLET
        elif "volume" in plan_lower or "disk" in plan_lower:
            return RemediationAction.ADD_VOLUME
        elif "restart" in plan_lower or "reboot" in plan_lower:
            return RemediationAction.RESTART_SERVICE
        elif "firewall" in plan_lower or "security" in plan_lower:
            return RemediationAction.UPDATE_FIREWALL
        elif "clean" in plan_lower:
            return RemediationAction.CLEAN_DISK
        else:
            # Default based on category
            if category == "capacity":
                return RemediationAction.RESIZE_DROPLET
            elif category == "security":
                return RemediationAction.UPDATE_FIREWALL
            else:
                return RemediationAction.RESTART_SERVICE

    def _extract_remediation_parameters(self, plan_text: str, diagnosis: Diagnosis) -> Dict[str, Any]:
        """Extract remediation parameters from plan text and incident context."""

        parameters = {
            "diagnosis_id": diagnosis.id,
            "incident_id": diagnosis.incident_id,
            "root_cause": diagnosis.root_cause
        }

        # Get droplet info from metadata (populated by analyze_infrastructure_state)
        if diagnosis.metadata:
            metadata = diagnosis.metadata
            
            # Get resource ID
            if 'droplet_id' in metadata:
                parameters["droplet_id"] = metadata['droplet_id']
            if 'resource_type' in metadata:
                parameters["resource_type"] = metadata['resource_type']
            
            # Get infrastructure state
            if 'infrastructure_state' in metadata or 'state_analysis' in metadata:
                state = metadata.get('infrastructure_state') or metadata.get('state_analysis', {})
                
                # Get droplet IP directly from state
                if 'droplet_ip' in state and state['droplet_ip']:
                    parameters["droplet_ip"] = state['droplet_ip']
                    logger.info(f"Extracted droplet IP for remediation: {state['droplet_ip']}")
                
                # Also get resource_id if available
                if 'resource_id' in state:
                    parameters["droplet_id"] = state['resource_id']
                
                # Extract from networks if IP not found
                if 'droplet_ip' not in parameters and 'networks' in state:
                    networks = state.get('networks', {}).get('v4', [])
                    for net in networks:
                        if net.get('type') == 'public':
                            parameters["droplet_ip"] = net.get('ip_address')
                            logger.info(f"Extracted droplet IP from networks: {net.get('ip_address')}")
                            break

        # Extract size parameters (e.g., "s-2vcpu-4gb")
        import re
        size_match = re.search(r's-\d+vcpu-\d+gb', plan_text)
        if size_match:
            parameters["new_size"] = size_match.group(0)

        logger.info(f"Remediation parameters: {parameters}")
        return parameters

    async def _estimate_remediation(
        self,
        incident: Incident,
        recommendations: List[str]
    ) -> tuple[Optional[float], Optional[int]]:
        """Estimate cost and duration of remediation."""

        # Simple estimation logic
        # In production, this would query pricing APIs

        cost = None
        duration = None

        if incident.metric == MetricType.CPU_USAGE or incident.metric == MetricType.MEMORY_USAGE:
            # Likely needs resize
            cost = 12.0  # Approximate cost difference for 1 month
            duration = 90  # 90 seconds for resize
        elif incident.metric == MetricType.DISK_USAGE:
            # Might need volume addition
            cost = 10.0  # $10/month for 100GB volume
            duration = 60  # 60 seconds
        else:
            # Other fixes
            cost = 0.0
            duration = 30

        return cost, duration

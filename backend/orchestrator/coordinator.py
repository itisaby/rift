"""
Agent Coordinator for Rift
Orchestrates the autonomous incident response workflow
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from agents.monitor_agent import MonitorAgent
from agents.diagnostic_agent import DiagnosticAgent
from agents.remediation_agent import RemediationAgent
from models.incident import (
    Incident,
    Diagnosis,
    RemediationResult,
    IncidentStatus
)
from utils.logger import IncidentLogger, get_logger

logger = get_logger(__name__)


class Coordinator:
    """
    Coordinates all AI agents to autonomously handle infrastructure incidents.

    Main Loop:
    1. Monitor infrastructure for incidents
    2. Diagnose root causes
    3. Execute remediations (if confidence > threshold)
    4. Verify fixes and learn from results
    """

    def __init__(
        self,
        monitor_agent: MonitorAgent,
        diagnostic_agent: DiagnosticAgent,
        remediation_agent: RemediationAgent,
        confidence_threshold: float = 0.85,
        auto_remediation_enabled: bool = True,
        check_interval: int = 30
    ):
        """
        Initialize Coordinator.

        Args:
            monitor_agent: Monitor Agent instance
            diagnostic_agent: Diagnostic Agent instance
            remediation_agent: Remediation Agent instance
            confidence_threshold: Minimum confidence for auto-remediation
            auto_remediation_enabled: Whether to auto-remediate
            check_interval: Seconds between infrastructure checks
        """
        self.monitor_agent = monitor_agent
        self.diagnostic_agent = diagnostic_agent
        self.remediation_agent = remediation_agent

        self.confidence_threshold = confidence_threshold
        self.auto_remediation_enabled = auto_remediation_enabled
        self.check_interval = check_interval

        # State tracking
        self.active_incidents: Dict[str, Incident] = {}
        self.diagnoses: Dict[str, Diagnosis] = {}
        self.results: Dict[str, RemediationResult] = {}

        # Statistics
        self.stats = {
            "incidents_detected": 0,
            "incidents_resolved": 0,
            "remediations_executed": 0,
            "remediations_successful": 0,
            "total_cost": 0.0
        }

        self.running = False

        logger.info(
            "coordinator_initialized",
            confidence_threshold=confidence_threshold,
            auto_remediation=auto_remediation_enabled,
            check_interval=check_interval
        )

    async def start_autonomous_loop(self):
        """
        Start the autonomous monitoring and remediation loop.

        This is the main event loop that continuously:
        1. Checks for incidents
        2. Diagnoses issues
        3. Executes fixes
        4. Learns from outcomes
        """
        self.running = True
        logger.info("autonomous_loop_started", message="Starting autonomous infrastructure monitoring")

        try:
            while self.running:
                try:
                    # Check for new incidents
                    logger.debug("checking_infrastructure", message="Running infrastructure health check")

                    incidents = await self.monitor_agent.check_all_infrastructure(tag="rift")

                    if incidents:
                        logger.info(
                            "incidents_found",
                            count=len(incidents),
                            message=f"Detected {len(incidents)} incident(s)"
                        )

                        # Process each incident
                        for incident in incidents:
                            await self.handle_incident_workflow(incident)

                    else:
                        logger.debug("no_incidents", message="No incidents detected")

                except Exception as e:
                    logger.error(
                        "loop_error",
                        error=str(e),
                        message=f"Error in autonomous loop: {str(e)}"
                    )

                # Wait before next check
                await asyncio.sleep(self.check_interval)

        except asyncio.CancelledError:
            logger.info("autonomous_loop_cancelled", message="Autonomous loop cancelled")
            self.running = False

        except Exception as e:
            logger.error(
                "autonomous_loop_failed",
                error=str(e),
                message=f"Autonomous loop failed: {str(e)}"
            )
            self.running = False

    async def stop_autonomous_loop(self):
        """Stop the autonomous loop."""
        logger.info("stopping_autonomous_loop", message="Stopping autonomous loop")
        self.running = False

    async def handle_incident_workflow(self, incident: Incident) -> Optional[RemediationResult]:
        """
        Handle complete incident workflow from detection to resolution.

        Args:
            incident: The detected incident

        Returns:
            RemediationResult if remediation was executed, None otherwise
        """
        incident_logger = IncidentLogger(incident.id)

        try:
            # Log detection
            incident_logger.log_detection({
                "resource": incident.resource_name,
                "metric": incident.metric.value,
                "current_value": incident.current_value,
                "threshold": incident.threshold_value,
                "severity": incident.severity.value
            })

            # Track incident
            self.active_incidents[incident.id] = incident
            self.stats["incidents_detected"] += 1

            # Update incident status
            incident.status = IncidentStatus.DIAGNOSING

            # Step 1: Diagnose the incident
            logger.info(
                "diagnosing_incident",
                incident_id=incident.id,
                trace_id=incident_logger.get_trace_id(),
                message=f"Diagnosing incident {incident.id}"
            )

            diagnosis = await self.diagnostic_agent.diagnose_incident(incident)
            self.diagnoses[incident.id] = diagnosis

            # Log diagnosis
            incident_logger.log_diagnosis({
                "diagnosis_id": diagnosis.id,
                "root_cause": diagnosis.root_cause,
                "confidence": diagnosis.confidence,
                "recommendations": diagnosis.recommendations,
                "estimated_cost": diagnosis.estimated_cost
            })

            # Update incident status
            incident.status = IncidentStatus.DIAGNOSED

            # Step 2: Check if we should remediate
            should_remediate = (
                self.auto_remediation_enabled and
                diagnosis.confidence >= self.confidence_threshold
            )

            if not should_remediate:
                logger.info(
                    "remediation_skipped",
                    incident_id=incident.id,
                    confidence=diagnosis.confidence,
                    threshold=self.confidence_threshold,
                    auto_enabled=self.auto_remediation_enabled,
                    message=f"Skipping remediation (confidence: {diagnosis.confidence:.2f} < {self.confidence_threshold})"
                )
                return None

            # Step 3: Generate remediation plan
            logger.info(
                "generating_plan",
                incident_id=incident.id,
                trace_id=incident_logger.get_trace_id(),
                message="Generating remediation plan"
            )

            plan = await self.diagnostic_agent.generate_remediation_plan(diagnosis)

            # Log remediation start
            incident_logger.log_remediation_start({
                "plan_id": plan.id,
                "action": plan.action.value,
                "estimated_cost": plan.estimated_cost,
                "requires_approval": plan.requires_approval
            })

            # Update incident status
            incident.status = IncidentStatus.REMEDIATING

            # Step 4: Execute remediation
            logger.info(
                "executing_remediation",
                incident_id=incident.id,
                plan_id=plan.id,
                trace_id=incident_logger.get_trace_id(),
                message=f"Executing remediation: {plan.action.value}"
            )

            result = await self.remediation_agent.execute_remediation(
                plan=plan,
                auto_approve=not plan.requires_approval
            )

            self.results[incident.id] = result
            self.stats["remediations_executed"] += 1

            if result.success:
                self.stats["remediations_successful"] += 1

            if result.actual_cost:
                self.stats["total_cost"] += result.actual_cost

            # Log remediation completion
            incident_logger.log_remediation_complete({
                "result_id": result.id,
                "success": result.success,
                "verification_passed": result.verification_passed,
                "duration": result.duration,
                "actual_cost": result.actual_cost
            })

            # Step 5: Update incident status
            if result.success and result.verification_passed:
                incident.status = IncidentStatus.RESOLVED
                self.stats["incidents_resolved"] += 1
                logger.info(
                    "incident_resolved",
                    incident_id=incident.id,
                    message=f"Incident {incident.id} resolved successfully"
                )
            else:
                incident.status = IncidentStatus.FAILED
                logger.error(
                    "incident_failed",
                    incident_id=incident.id,
                    error=result.error_message,
                    message=f"Incident {incident.id} remediation failed"
                )

            # Step 6: Learn from the outcome
            await self.update_knowledge_base(incident, diagnosis, result)

            return result

        except Exception as e:
            logger.error(
                "workflow_error",
                incident_id=incident.id,
                error=str(e),
                message=f"Error in incident workflow: {str(e)}"
            )
            incident_logger.log_error(str(e))
            incident.status = IncidentStatus.FAILED
            return None

    async def route_to_agent(
        self,
        agent_type: str,
        request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Route a request to the appropriate agent.

        Args:
            agent_type: Type of agent (monitor, diagnostic, remediation)
            request: Request data

        Returns:
            Agent response
        """
        logger.debug(
            "routing_request",
            agent_type=agent_type,
            request_size=len(str(request))
        )

        try:
            if agent_type == "monitor":
                # Route to monitor agent
                incidents = await self.monitor_agent.check_all_infrastructure()
                return {"incidents": [inc.dict() for inc in incidents]}

            elif agent_type == "diagnostic":
                # Route to diagnostic agent
                incident_data = request.get("incident")
                if not incident_data:
                    raise ValueError("Missing incident data")

                incident = Incident(**incident_data)
                diagnosis = await self.diagnostic_agent.diagnose_incident(incident)
                return {"diagnosis": diagnosis.dict()}

            elif agent_type == "remediation":
                # Route to remediation agent
                plan_data = request.get("plan")
                if not plan_data:
                    raise ValueError("Missing plan data")

                from models.incident import RemediationPlan
                plan = RemediationPlan(**plan_data)

                result = await self.remediation_agent.execute_remediation(plan)
                return {"result": result.dict()}

            else:
                raise ValueError(f"Unknown agent type: {agent_type}")

        except Exception as e:
            logger.error(
                "routing_error",
                agent_type=agent_type,
                error=str(e)
            )
            raise

    async def aggregate_results(
        self,
        results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Aggregate results from multiple operations.

        Args:
            results: List of result dictionaries

        Returns:
            Aggregated summary
        """
        return {
            "total_results": len(results),
            "timestamp": datetime.utcnow().isoformat(),
            "results": results
        }

    async def update_knowledge_base(
        self,
        incident: Incident,
        diagnosis: Diagnosis,
        result: RemediationResult
    ):
        """
        Update knowledge base with learned information.

        Args:
            incident: The incident
            diagnosis: The diagnosis
            result: The remediation result
        """
        try:
            # Create knowledge entry
            entry = f"""
            Incident Resolution Record:

            Incident: {incident.description}
            Resource: {incident.resource_name} ({incident.resource_type.value})
            Metric: {incident.metric.value} - {incident.current_value}%

            Diagnosis:
            - Root Cause: {diagnosis.root_cause}
            - Confidence: {diagnosis.confidence:.2f}
            - Recommendations: {', '.join(diagnosis.recommendations)}

            Resolution:
            - Action: {result.action_taken}
            - Success: {result.success}
            - Verification: {result.verification_passed}
            - Duration: {result.duration}s
            - Cost: ${result.actual_cost:.2f if result.actual_cost else 0.0}

            Outcome: {'Successful' if result.success and result.verification_passed else 'Failed'}
            """

            # Log for knowledge base
            logger.info(
                "knowledge_base_update",
                incident_id=incident.id,
                diagnosis_id=diagnosis.id,
                success=result.success,
                entry_preview=entry[:200]
            )

        except Exception as e:
            logger.error(
                "kb_update_error",
                error=str(e),
                message=f"Failed to update knowledge base: {str(e)}"
            )

    def get_system_status(self) -> Dict[str, Any]:
        """
        Get current system status.

        Returns:
            System status dictionary
        """
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "running": self.running,
            "active_incidents": len(self.active_incidents),
            "confidence_threshold": self.confidence_threshold,
            "auto_remediation_enabled": self.auto_remediation_enabled,
            "check_interval": self.check_interval,
            "stats": self.stats.copy()
        }

    def get_active_incidents(self) -> List[Incident]:
        """Get list of active incidents."""
        return list(self.active_incidents.values())

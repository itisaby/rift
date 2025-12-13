"""
Provisioner Agent for Rift
Proactive infrastructure provisioning based on natural language requests
"""

import logging
import time
from typing import Dict, Any, Optional, List
import json

from agents.base_agent import BaseAgent
from mcp_clients.terraform_mcp import TerraformMCP
from mcp_clients.do_mcp import DigitalOceanMCP
from models.provision_request import (
    ProvisionRequest,
    ProvisionResult,
    ProvisionStatus,
    ProvisionTemplate,
    BUILTIN_TEMPLATES
)

logger = logging.getLogger("rift.agents.provisioner")


class ProvisionerAgent(BaseAgent):
    """
    Proactive infrastructure provisioning agent.
    Creates new infrastructure based on natural language requests or templates.
    """

    def __init__(
        self,
        agent_endpoint: str,
        agent_key: str,
        agent_id: str,
        terraform_mcp: TerraformMCP,
        do_mcp: DigitalOceanMCP,
        knowledge_base_id: Optional[str] = None
    ):
        """
        Initialize Provisioner Agent.

        Args:
            agent_endpoint: Gradient AI agent endpoint URL
            agent_key: API key for authentication
            agent_id: Unique agent identifier
            terraform_mcp: Terraform MCP client instance
            do_mcp: DigitalOcean MCP client instance
            knowledge_base_id: Optional knowledge base ID
        """
        super().__init__(
            agent_endpoint=agent_endpoint,
            agent_key=agent_key,
            agent_id=agent_id,
            agent_name="Provisioner Agent",
            knowledge_base_id=knowledge_base_id
        )

        self.terraform_mcp = terraform_mcp
        self.do_mcp = do_mcp
        self.templates = {t.id: t for t in BUILTIN_TEMPLATES}

        logger.info("Provisioner Agent initialized with %d templates", len(self.templates))

    async def provision(
        self,
        request: ProvisionRequest
    ) -> ProvisionResult:
        """
        Main provisioning workflow.

        Workflow:
        1. Parse and understand request
        2. Generate or load Terraform configuration
        3. Validate configuration
        4. Estimate costs
        5. Apply configuration
        6. Extract access information

        Args:
            request: ProvisionRequest with user's infrastructure needs

        Returns:
            ProvisionResult with created resources and access info
        """
        start_time = time.time()
        logs = []

        try:
            logger.info(f"Starting provisioning request: {request.request_id}")
            logs.append(f"Provisioning request {request.request_id} started")
            logs.append(f"Description: {request.description}")

            # Step 1: Generate or load Terraform configuration
            if request.template:
                logs.append(f"Using template: {request.template}")
                terraform_config = await self._generate_from_template(
                    request.template,
                    request.template_params or {}
                )
            else:
                logs.append("Generating Terraform from natural language request...")
                terraform_config = await self._generate_terraform(request)

            if not terraform_config:
                return self._create_failed_result(
                    request=request,
                    error="Failed to generate Terraform configuration",
                    logs=logs,
                    duration=time.time() - start_time
                )

            logs.append(f"Generated {len(terraform_config)} bytes of Terraform configuration")

            # Step 2: Validate configuration
            logs.append("Validating Terraform configuration...")
            validation = await self.terraform_mcp.validate_config(terraform_config)

            if not validation.valid:
                return self._create_failed_result(
                    request=request,
                    error=f"Terraform validation failed: {', '.join(validation.errors)}",
                    logs=logs,
                    duration=time.time() - start_time,
                    validation_errors=validation.errors
                )

            logs.append("✓ Terraform configuration is valid")

            if validation.warnings:
                for warning in validation.warnings:
                    logs.append(f"⚠️  Warning: {warning}")

            # Step 3: Estimate costs
            logs.append("Estimating infrastructure costs...")
            cost_estimate = await self._estimate_cost(request, terraform_config)
            logs.append(f"Estimated monthly cost: ${cost_estimate:.2f}")

            # Check budget limit
            if request.budget_limit and cost_estimate > request.budget_limit:
                return self._create_failed_result(
                    request=request,
                    error=f"Cost estimate (${cost_estimate:.2f}) exceeds budget limit (${request.budget_limit:.2f})",
                    logs=logs,
                    duration=time.time() - start_time
                )

            # Step 4: Plan Terraform changes
            logs.append("Running Terraform plan (dry-run)...")
            plan_result = await self.terraform_mcp.plan(
                config=terraform_config,
                variables=self._extract_variables(request)
            )

            if not plan_result.success:
                return self._create_failed_result(
                    request=request,
                    error=f"Terraform plan failed: {plan_result.plan_output}",
                    logs=logs,
                    duration=time.time() - start_time
                )

            logs.append(f"Plan: {plan_result.resources_to_add} to add, "
                       f"{plan_result.resources_to_change} to change, "
                       f"{plan_result.resources_to_destroy} to destroy")

            # Step 5: Apply configuration
            logs.append("Applying Terraform configuration...")
            apply_result = await self.terraform_mcp.apply(
                config=terraform_config,
                variables=self._extract_variables(request),
                auto_approve=True
            )

            if not apply_result.success:
                return self._create_failed_result(
                    request=request,
                    error=f"Terraform apply failed: {apply_result.error_message}",
                    logs=logs,
                    duration=time.time() - start_time
                )

            logs.append(f"✓ Successfully created {apply_result.resources_created} resource(s)")

            # Step 6: Extract access information
            logs.append("Extracting access information...")
            access_info = await self._extract_access_info(apply_result.output_values)
            resources_created = self._parse_created_resources(apply_result)

            # Step 7: Update knowledge base
            logs.append("Updating knowledge base...")
            await self._update_knowledge_base(request, apply_result, cost_estimate)

            duration = time.time() - start_time
            logs.append(f"✓ Provisioning completed in {duration:.1f} seconds")

            return ProvisionResult(
                request_id=request.request_id,
                status=ProvisionStatus.COMPLETED,
                success=True,
                resources_created=resources_created,
                access_info=access_info,
                cost_estimate=cost_estimate,
                terraform_config=terraform_config,
                terraform_outputs=apply_result.output_values,
                logs=logs,
                duration_seconds=duration
            )

        except Exception as e:
            logger.error(f"Provisioning failed: {str(e)}")
            logs.append(f"❌ Exception: {str(e)}")

            return self._create_failed_result(
                request=request,
                error=str(e),
                logs=logs,
                duration=time.time() - start_time
            )

    async def _generate_terraform(
        self,
        request: ProvisionRequest
    ) -> str:
        """
        Generate Terraform configuration from natural language request.

        Uses AI with RAG to create production-ready Terraform code.

        Args:
            request: The provision request

        Returns:
            Terraform configuration as string
        """
        logger.debug(f"Generating Terraform for: {request.description}")

        prompt = f"""
        You are an expert infrastructure engineer specializing in DigitalOcean and Terraform.
        Generate complete, production-ready Terraform 1.x configuration based on this request:

        Request: {request.description}

        Requirements:
        - Region: {request.region}
        - Environment: {request.environment}
        - Budget Limit: ${request.budget_limit or "unlimited"}
        - Tags: {', '.join(request.tags) if request.tags else 'none'}

        CRITICAL: Your Terraform configuration MUST begin with EXACTLY this block.
        Copy it character-by-character. DO NOT change "digitalocean" to "digitaldocean".
        
        START YOUR RESPONSE WITH:
        
terraform {{
  required_version = ">= 1.0.0"
  required_providers {{
    digitalocean = {{
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }}
  }}
}}

provider "digitalocean" {{
  token = var.do_token
}}

        RESOURCE GUIDELINES BY REQUEST TYPE:

        For Web Applications (Node.js, Python, etc.):
        - Use digitalocean_droplet with appropriate size (s-1vcpu-2gb for small, s-2vcpu-4gb for medium)
        - Include image = "ubuntu-22-04-x64" or "ubuntu-24-04-x64"
        - Add user_data script to install dependencies and start the app
        - Enable monitoring = true and backups = true
        - Create outputs: droplet_id, droplet_name, ipv4_address, app_url

        For Databases (MongoDB, PostgreSQL, MySQL, Redis):
        - Use digitalocean_database_cluster resource
        - engine options: "pg" (PostgreSQL), "mysql", "mongodb", "redis"
        - size options: "db-s-1vcpu-1gb", "db-s-2vcpu-4gb", "db-s-4vcpu-8gb"
        - ALWAYS set version (pg: "16", mysql: "8", mongodb: "7", redis: "7")
        - node_count = 1 for dev, 2-3 for production
        - Include private_network_uuid for secure connections
        - Create outputs: database_id, database_host, database_port, database_name, connection_string

        For Load Balancers:
        - Use digitalocean_loadbalancer resource
        - algorithm = "round_robin" or "least_connections"
        - forwarding_rule with entry_protocol, entry_port, target_protocol, target_port
        - healthcheck with protocol, port, path (for HTTP)
        - droplet_ids to distribute traffic across
        - Create outputs: lb_id, lb_ip, lb_url

        For Auto-Scaling / Multiple Droplets:
        - Use count parameter on digitalocean_droplet
        - Create variable for instance_count with default 2-3
        - Use count.index in names: "${{var.prefix}}-${{count.index + 1}}"
        - Connect to load balancer using droplet_ids

        For Firewalls:
        - Use digitalocean_firewall resource
        - inbound_rule for allowing traffic (SSH: 22, HTTP: 80, HTTPS: 443, MongoDB: 27017, PostgreSQL: 5432, Redis: 6379)
        - source_addresses = ["0.0.0.0/0", "::/0"] for public access
        - droplet_ids to attach firewall to specific droplets

        IMPORTANT RULES:
        1. Always include meaningful outputs with resource IDs, IPs, and connection info
        2. Use var.tags ONLY on: digitalocean_droplet, digitalocean_database_cluster, digitalocean_volume
        3. NO tags on: digitalocean_loadbalancer, digitalocean_vpc, digitalocean_firewall
        4. Enable monitoring and backups for production (environment = "production")
        5. Use private networking (VPC) for database connections
        6. Always specify resource versions (database engine version, image version)
        7. Include proper healthchecks for load balancers
        8. Set appropriate droplet sizes based on workload (see budget limit)

        REQUIRED VARIABLES:
        - do_token (sensitive, no default)
        - region (default: "{request.region}")
        - environment (default: "{request.environment}")
        - tags (default: ["managed-by-rift"])

        NAMING CONVENTION:
        Use descriptive names: "webapp-server", "mongodb-cluster", "app-loadbalancer"

        Return ONLY the Terraform HCL code, no explanations or markdown formatting.
        """

        try:
            response = await self.query_agent(
                prompt=prompt,
                use_knowledge_base=True
            )

            terraform_config = response.get("response", "")
            
            # Log raw response for debugging
            logger.debug(f"Raw AI response length: {len(terraform_config)} bytes")
            logger.debug(f"Raw AI response preview: {terraform_config[:500]}...")

            # Clean up response (remove markdown code blocks if present)
            terraform_config = self._extract_terraform_code(terraform_config)
            
            # Post-process to fix common AI mistakes
            terraform_config = self._fix_terraform_config(terraform_config)

            logger.info(f"Generated Terraform configuration ({len(terraform_config)} bytes)")
            
            if not terraform_config:
                logger.error("Terraform extraction resulted in empty config")
                raw_response = response.get('response', '')
                logger.error(f"Original response length: {len(raw_response)} bytes")
                logger.error(f"Original response preview: {raw_response[:2000]}")
                logger.error(f"Response contains 'terraform': {'terraform' in raw_response.lower()}")
                logger.error(f"Response contains 'resource': {'resource' in raw_response.lower()}")
                logger.error(f"Response contains code blocks: {'```' in raw_response}")
                
                # Last resort: if response contains terraform keywords, use it as-is
                if 'terraform' in raw_response.lower() or 'resource' in raw_response.lower():
                    logger.warning("Attempting to use raw response as Terraform code")
                    terraform_config = raw_response.strip()
            
            return terraform_config

        except Exception as e:
            logger.error(f"Failed to generate Terraform: {str(e)}")
            return ""

    async def _generate_from_template(
        self,
        template_id: str,
        params: Dict[str, Any]
    ) -> str:
        """
        Generate Terraform from a pre-built template.

        Args:
            template_id: Template identifier
            params: Template parameters

        Returns:
            Terraform configuration
        """
        template = self.templates.get(template_id)

        if not template:
            raise ValueError(f"Template '{template_id}' not found")

        logger.info(f"Using template: {template.name}")

        # Merge provided params with template defaults
        merged_params = {**template.optional_params, **params}

        # Check required params
        missing = [p for p in template.required_params if p not in merged_params]
        if missing:
            raise ValueError(f"Missing required parameters: {', '.join(missing)}")

        # Use AI to customize template with parameters
        prompt = f"""
        Generate Terraform configuration using the '{template.name}' template.

        Template Description: {template.description}
        Terraform Module: {template.terraform_module}

        Parameters:
        {json.dumps(merged_params, indent=2)}

        Generate complete Terraform configuration that uses the module path
        '{template.terraform_module}' with these parameters.

        Include:
        - Provider configuration for DigitalOcean
        - Module instantiation with all parameters
        - Output values from the module

        Return ONLY the Terraform HCL code.
        """

        response = await self.query_agent(prompt=prompt, use_knowledge_base=False)
        terraform_config = self._extract_terraform_code(response.get("response", ""))

        return terraform_config

    async def _estimate_cost(
        self,
        request: ProvisionRequest,
        terraform_config: str
    ) -> float:
        """
        Estimate monthly cost of infrastructure.

        Parses Terraform to identify resources and calculates cost
        based on DigitalOcean pricing.

        Args:
            request: The provision request
            terraform_config: Terraform configuration

        Returns:
            Estimated monthly cost in USD
        """
        # If using a template, return its estimated cost
        if request.template and request.template in self.templates:
            return self.templates[request.template].estimated_cost

        # Otherwise, analyze the Terraform config
        cost = 0.0

        # Simple regex-based parsing (in production, use HCL parser)
        import re

        # Droplet costs
        droplet_sizes = re.findall(r'size\s*=\s*"(s-\d+vcpu-\d+gb[^"]*)"', terraform_config)
        for size in droplet_sizes:
            cost += self._get_droplet_cost(size)

        # Database costs
        db_sizes = re.findall(r'size\s*=\s*"(db-[^"]+)"', terraform_config)
        for size in db_sizes:
            cost += self._get_database_cost(size)

        # Load balancer costs
        lb_count = terraform_config.count("resource \"digitalocean_loadbalancer\"")
        cost += lb_count * 12.0  # $12/month per LB

        # Volume costs
        volume_sizes = re.findall(r'size\s*=\s*(\d+)', terraform_config)
        for size_str in volume_sizes:
            cost += int(size_str) * 0.10  # $0.10/GB

        logger.info(f"Estimated cost: ${cost:.2f}/month")
        return cost

    def _get_droplet_cost(self, size: str) -> float:
        """Get monthly cost for a droplet size."""
        # DigitalOcean pricing (approximate)
        pricing = {
            "s-1vcpu-1gb": 6.0,
            "s-1vcpu-2gb": 12.0,
            "s-2vcpu-2gb": 18.0,
            "s-2vcpu-4gb": 24.0,
            "s-4vcpu-8gb": 48.0,
            "s-8vcpu-16gb": 96.0,
        }
        return pricing.get(size, 12.0)  # Default to $12 if unknown

    def _get_database_cost(self, size: str) -> float:
        """Get monthly cost for a database size."""
        pricing = {
            "db-s-1vcpu-1gb": 15.0,
            "db-s-1vcpu-2gb": 30.0,
            "db-s-2vcpu-4gb": 60.0,
            "db-s-4vcpu-8gb": 120.0,
        }
        return pricing.get(size, 15.0)

    def _extract_variables(self, request: ProvisionRequest) -> Dict[str, Any]:
        """Extract Terraform variables from request."""
        variables = {
            "do_token": self.do_mcp.api_token,  # DigitalOcean API token
            "region": request.region,
            "environment": request.environment,
            "tags": request.tags
        }

        if request.template_params:
            variables.update(request.template_params)

        return variables

    async def _extract_access_info(
        self,
        outputs: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Extract access information from Terraform outputs.

        Args:
            outputs: Terraform output values

        Returns:
            Dictionary with access information
        """
        access_info = {}

        # Extract IP addresses
        if "ipv4_address" in outputs:
            ip = outputs["ipv4_address"]
            access_info["ssh"] = f"ssh root@{ip}"
            access_info["http"] = f"http://{ip}"

        # Extract database connection info
        if "database_uri" in outputs:
            access_info["database"] = outputs["database_uri"]

        # Extract load balancer info
        if "load_balancer_ip" in outputs:
            access_info["load_balancer"] = f"http://{outputs['load_balancer_ip']}"

        return access_info

    def _parse_created_resources(self, apply_result: Any) -> List[Dict[str, Any]]:
        """Parse created resources from Terraform apply result."""
        resources = []

        # Extract from output values
        if hasattr(apply_result, "output_values"):
            outputs = apply_result.output_values
            
            # Parse different resource types from outputs
            for key, value in outputs.items():
                key_lower = key.lower()
                
                # Droplet resources
                if "droplet" in key_lower and ("id" in key_lower or key == "droplet_id"):
                    resources.append({
                        "type": "droplet",
                        "id": value,
                        "name": outputs.get("droplet_name") or outputs.get("name") or f"droplet-{value}",
                        "ipv4_address": outputs.get("ipv4_address") or outputs.get("droplet_ip")
                    })
                
                # Database resources
                elif "database" in key_lower and ("id" in key_lower or key == "database_id"):
                    resources.append({
                        "type": "database",
                        "id": value,
                        "name": outputs.get("database_name") or f"database-{value}",
                        "host": outputs.get("database_host"),
                        "port": outputs.get("database_port"),
                        "connection_string": outputs.get("connection_string")
                    })
                
                # Load balancer resources
                elif ("loadbalancer" in key_lower or "lb" in key_lower) and ("id" in key_lower or key == "lb_id"):
                    resources.append({
                        "type": "loadbalancer",
                        "id": value,
                        "name": outputs.get("lb_name") or f"loadbalancer-{value}",
                        "ip": outputs.get("lb_ip") or outputs.get("loadbalancer_ip"),
                        "url": outputs.get("lb_url")
                    })
                
                # VPC resources
                elif "vpc" in key_lower and "id" in key_lower:
                    resources.append({
                        "type": "vpc",
                        "id": value,
                        "name": outputs.get("vpc_name") or f"vpc-{value}",
                        "ip_range": outputs.get("vpc_ip_range")
                    })
                
                # Volume resources
                elif "volume" in key_lower and "id" in key_lower:
                    resources.append({
                        "type": "volume",
                        "id": value,
                        "name": outputs.get("volume_name") or f"volume-{value}",
                        "size": outputs.get("volume_size")
                    })
                
                # Firewall resources
                elif "firewall" in key_lower and "id" in key_lower:
                    resources.append({
                        "type": "firewall",
                        "id": value,
                        "name": outputs.get("firewall_name") or f"firewall-{value}"
                    })
                
                # Generic ID detection (fallback)
                elif key.endswith("_id") and not any(r.get("id") == value for r in resources):
                    resource_type = key.replace("_id", "")
                    resources.append({
                        "type": resource_type,
                        "id": value,
                        "name": outputs.get(f"{resource_type}_name") or f"{resource_type}-{value}"
                    })
                
                # IP addresses (likely droplets if not already parsed)
                elif "ip" in key_lower and "address" in key_lower and value:
                    if not any(r.get("ipv4_address") == value for r in resources):
                        resources.append({
                            "type": "droplet",
                            "id": outputs.get("droplet_id") or outputs.get("id"),
                            "name": outputs.get("droplet_name") or outputs.get("name") or "server",
                            "ipv4_address": value
                        })

        # If no specific resources found, create generic entries from resource count
        if not resources and hasattr(apply_result, "resources_created") and apply_result.resources_created > 0:
            for i in range(apply_result.resources_created):
                resources.append({
                    "type": "resource",
                    "id": f"resource-{i+1}",
                    "name": f"Resource {i+1}",
                    "summary": "Created via Terraform"
                })

        return resources

    def _fix_terraform_config(self, config: str) -> str:
        """
        Fix common AI mistakes in generated Terraform configuration.
        
        Args:
            config: The generated Terraform configuration
            
        Returns:
            Fixed Terraform configuration
        """
        if not config:
            return config
        
        # Fix common typo: digitaldocean -> digitalocean
        config = config.replace('digitaldocean = {', 'digitalocean = {')
        config = config.replace('"digitaldocean"', '"digitalocean"')
        
        # Fix incorrect DigitalOcean attribute names
        # Do most specific replacements first to avoid double-replacements
        config = config.replace('.private_ipv4_address', '.ipv4_address_private')
        config = config.replace('.private_ip', '.ipv4_address_private')
        config = config.replace('.public_ip', '.ipv4_address')
        
        # Fix any double-replacement errors
        config = config.replace('.ipv4_address_privatev4_address', '.ipv4_address_private')
        config = config.replace('ipv4_address_privatev4_address', 'ipv4_address_private')
        
        # Remove deprecated parameter
        import re
        config = re.sub(r'\n\s*private_networking\s*=\s*\w+\s*\n', '\n', config)
        
        # Fix firewall rule attribute: ports -> port_range (use regex for flexibility)
        config = re.sub(r'(\s+)ports(\s+)=', r'\1port_range\2=', config)
        
        # Fix variables with dynamic default values (not allowed in Terraform)
        # Change default = "name-${resource.id}" to default = "name"
        import re
        config = re.sub(
            r'(default\s*=\s*)"[^"]*\$\{[^}]+\}[^"]*"',
            r'\1"ubuntu-droplet"',
            config
        )
        
        # Fix old provider syntax (version in provider block instead of required_providers)
        lines = config.split('\n')
        new_lines = []
        in_provider_block = False
        
        for line in lines:
            # Skip version lines in provider blocks
            if 'provider "digitalocean"' in line:
                in_provider_block = True
                new_lines.append(line)
            elif in_provider_block and line.strip().startswith('version'):
                # Skip this line - version should be in required_providers
                continue
            elif in_provider_block and line.strip() == '}':
                in_provider_block = False
                new_lines.append(line)
            else:
                new_lines.append(line)
        
        config = '\n'.join(new_lines)
        
        logger.debug("Applied terraform config fixes")
        return config
    
    def _extract_terraform_code(self, response: str) -> str:
        """Extract Terraform code from AI response (remove markdown formatting)."""
        if not response:
            logger.warning("Empty response received for Terraform extraction")
            return ""
            
        config = response.strip()
        logger.debug(f"Extracting Terraform from response of length {len(config)}")

        # If response contains markdown code blocks
        if "```" in config:
            logger.debug("Response contains markdown code blocks")
            # Extract code between ```hcl or ```terraform and ```
            parts = config.split("```")
            logger.debug(f"Split into {len(parts)} parts by triple backticks")
            
            for i, part in enumerate(parts):
                part_stripped = part.strip()
                part_lower = part_stripped.lower()
                
                # Check if this is a code block with language identifier
                if part_lower.startswith("hcl") or part_lower.startswith("terraform"):
                    # Remove language identifier and get the code
                    lines = part_stripped.split('\n', 1)
                    if len(lines) > 1:
                        config = lines[1].strip()
                        logger.debug(f"Found code block with language identifier: {lines[0]}")
                        break
                # Or if this part contains terraform code directly
                elif "terraform {" in part or "resource \"" in part or "provider \"" in part:
                    config = part_stripped
                    logger.debug(f"Found Terraform code in part {i}")
                    break
        
        # If still empty or no terraform blocks found, check if response itself is terraform code
        if not config or (not "terraform" in config.lower() and not "resource" in config.lower()):
            logger.debug("No code blocks found, checking if response is raw Terraform")
            # Maybe the AI returned plain terraform without markdown
            if "terraform {" in response or "resource \"" in response or "provider \"" in response:
                config = response.strip()
                logger.debug("Using raw response as Terraform code")
            else:
                logger.warning("No Terraform code patterns found in response")
        
        logger.debug(f"Extracted config length: {len(config)}")
        return config

    async def _update_knowledge_base(
        self,
        request: ProvisionRequest,
        apply_result: Any,
        cost: float
    ):
        """Update knowledge base with provisioning information."""
        try:
            entry = f"""
            Provisioning Record:

            Request: {request.description}
            Environment: {request.environment}
            Region: {request.region}

            Result:
            - Resources Created: {apply_result.resources_created}
            - Resources Updated: {apply_result.resources_updated}
            - Monthly Cost: ${cost:.2f}
            - Duration: {apply_result.duration_seconds}s

            This provisioning was successful and can be used as a reference
            for similar infrastructure requests.
            """

            await self.query_agent(prompt=f"Record this successful provisioning:\n{entry}", use_knowledge_base=True)
            logger.debug("Knowledge base updated")

        except Exception as e:
            logger.warning(f"Failed to update knowledge base: {str(e)}")

    def _create_failed_result(
        self,
        request: ProvisionRequest,
        error: str,
        logs: List[str],
        duration: float,
        validation_errors: Optional[List[str]] = None
    ) -> ProvisionResult:
        """Create a failed ProvisionResult."""
        return ProvisionResult(
            request_id=request.request_id,
            status=ProvisionStatus.FAILED,
            success=False,
            error=error,
            validation_errors=validation_errors,
            logs=logs,
            duration_seconds=duration
        )

    def get_templates(self) -> List[ProvisionTemplate]:
        """Get list of available templates."""
        return list(self.templates.values())

    def get_template(self, template_id: str) -> Optional[ProvisionTemplate]:
        """Get a specific template by ID."""
        return self.templates.get(template_id)

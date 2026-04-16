"use client"

import { useEffect, useState, useRef, useCallback } from "react"
import Link from "next/link"
import { ArrowLeft, Zap, Send, Terminal, CheckCircle2, XCircle, Loader2, FolderKanban, Sparkles, Server, ArrowRight, Database, Shield, Activity } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { useWebSocket } from "@/lib/useWebSocket"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
const WS_URL = API_URL.replace("http", "ws") + "/ws/events"

interface Project {
    project_id: string
    name: string
    description?: string
    cloud_providers: Array<{
        provider: string
        region?: string
    }>
}

interface ProvisionLog {
    timestamp: string
    message: string
    type: "info" | "success" | "error" | "warning" | "mcp"
    mcpServer?: string
    mcpTool?: string
    step?: string
    stepStatus?: "running" | "done" | "error"
    elapsed?: number
}

interface ProvisionResult {
    request_id: string
    status: string
    success: boolean
    resources_created?: Array<{
        id: string
        name: string
        type: string
    }>
    cost_estimate?: number
    logs?: string[]
    error?: string
}

// MCP server display config
const MCP_SERVER_STYLES: Record<string, { color: string; bg: string; icon: string }> = {
    "terraform": { color: "text-purple-300", bg: "bg-purple-900/60 border-purple-500/40", icon: "TF" },
    "gradient-ai": { color: "text-cyan-300", bg: "bg-cyan-900/60 border-cyan-500/40", icon: "AI" },
    "infra": { color: "text-orange-300", bg: "bg-orange-900/60 border-orange-500/40", icon: "IF" },
    "do": { color: "text-blue-300", bg: "bg-blue-900/60 border-blue-500/40", icon: "DO" },
    "prometheus": { color: "text-yellow-300", bg: "bg-yellow-900/60 border-yellow-500/40", icon: "PM" },
}

function getMcpStyle(server: string) {
    return MCP_SERVER_STYLES[server] || { color: "text-gray-300", bg: "bg-gray-800/60 border-gray-500/40", icon: "??" }
}

export default function ProvisionPage() {
    const [projects, setProjects] = useState<Project[]>([])
    const [selectedProject, setSelectedProject] = useState<string | null>(null)
    const [naturalLanguageInput, setNaturalLanguageInput] = useState("")
    const [provisioning, setProvisioning] = useState(false)
    const [logs, setLogs] = useState<ProvisionLog[]>([])
    const [result, setResult] = useState<ProvisionResult | null>(null)
    const [loading, setLoading] = useState(true)
    const [activeStep, setActiveStep] = useState<string | null>(null)
    const [currentRequestId, setCurrentRequestId] = useState<string | null>(null)

    const logsEndRef = useRef<HTMLDivElement>(null)

    // WebSocket for real-time MCP step streaming
    const addLogRef = useRef<(log: ProvisionLog) => void>(() => {})
    const activeStepRef = useRef(activeStep)

    const handleWsMessage = useCallback((message: { type: string; [key: string]: any }) => {
        if (message.type === "provision_step") {
            const { step, detail, status, mcp_server, mcp_tool, elapsed } = message
            const logType = status === "error" ? "error" : status === "done" ? "success" : "mcp"
            const newLog: ProvisionLog = {
                timestamp: new Date().toLocaleTimeString(),
                message: detail,
                type: logType,
                mcpServer: mcp_server || undefined,
                mcpTool: mcp_tool || undefined,
                step,
                stepStatus: status,
                elapsed,
            }
            setLogs(prev => [...prev, newLog])
            if (status === "running") {
                setActiveStep(step)
            } else if (status === "done" || status === "error") {
                setActiveStep(null)
            }
        }
    }, [])

    const { isConnected } = useWebSocket(WS_URL, { onMessage: handleWsMessage })

    useEffect(() => {
        fetchProjects()
    }, [])

    useEffect(() => {
        logsEndRef.current?.scrollIntoView({ behavior: "smooth" })
    }, [logs])

    const fetchProjects = async () => {
        try {
            const response = await fetch(`${API_URL}/projects`)
            if (response.ok) {
                const data = await response.json()
                setProjects(data)
                if (data.length > 0) {
                    setSelectedProject(data[0].project_id)
                }
            }
            setLoading(false)
        } catch (error) {
            console.error("Failed to fetch projects:", error)
            setLoading(false)
        }
    }

    const addLog = (message: string, type: ProvisionLog["type"] = "info", extra?: Partial<ProvisionLog>) => {
        setLogs(prev => [...prev, {
            timestamp: new Date().toLocaleTimeString(),
            message,
            type,
            ...extra,
        }])
    }

    const handleProvision = async () => {
        if (!naturalLanguageInput.trim()) {
            addLog("Please enter infrastructure requirements", "error")
            return
        }
        if (!selectedProject) {
            addLog("Please select a project", "error")
            return
        }

        setProvisioning(true)
        setLogs([])
        setResult(null)
        setActiveStep(null)

        addLog("Starting infrastructure provisioning...", "info")
        addLog(`Request: "${naturalLanguageInput}"`, "info")
        addLog(`Project: ${projects.find(p => p.project_id === selectedProject)?.name}`, "info")

        try {
            const requestBody = {
                user_id: "frontend-user",
                description: naturalLanguageInput,
                region: projects.find(p => p.project_id === selectedProject)?.cloud_providers[0]?.region || "nyc3",
                environment: "production",
                tags: ["frontend-provisioned"]
            }

            addLog("Sending request to provisioning agent...", "info")

            const url = `${API_URL}/provision/create?project_id=${selectedProject}`
            const response = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestBody)
            })

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
            }

            const data: ProvisionResult = await response.json()

            // Display backend logs (these include [MCP:server] prefixed entries)
            if (data.logs && data.logs.length > 0) {
                data.logs.forEach(log => {
                    const parsed = parseBackendLog(log)
                    addLog(parsed.message, parsed.type, {
                        mcpServer: parsed.mcpServer,
                        mcpTool: parsed.mcpTool,
                    })
                })
            }

            setResult(data)

            if (data.success) {
                addLog("Infrastructure provisioning completed successfully!", "success")
                if (data.resources_created && data.resources_created.length > 0) {
                    addLog(`Created ${data.resources_created.length} resource(s)`, "success")
                }
                if (data.cost_estimate) {
                    addLog(`Estimated monthly cost: $${data.cost_estimate.toFixed(2)}`, "info")
                }
            } else {
                addLog(`Provisioning failed: ${data.error || 'Unknown error'}`, "error")
            }

        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error'
            addLog(`Error: ${errorMessage}`, "error")
        } finally {
            setProvisioning(false)
            setActiveStep(null)
        }
    }

    const selectedProjectDetails = projects.find(p => p.project_id === selectedProject)

    if (loading) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 p-8">
                <div className="max-w-7xl mx-auto">
                    <div className="flex items-center justify-center h-64">
                        <div className="text-white text-xl">Loading...</div>
                    </div>
                </div>
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 p-8">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="mb-8">
                    <div className="flex items-center justify-between mb-4">
                        <div>
                            <Link href="/">
                                <Button variant="outline" className="bg-gray-800 border-gray-700 text-white hover:bg-gray-700 mb-4">
                                    <ArrowLeft className="w-4 h-4 mr-2" />
                                    Back to Dashboard
                                </Button>
                            </Link>
                            <h1 className="text-4xl font-bold text-white mb-2 flex items-center gap-3">
                                <Sparkles className="w-10 h-10 text-purple-400" />
                                AI-Powered Infrastructure Provisioning
                            </h1>
                            <p className="text-gray-300">
                                Describe your infrastructure needs in plain English, and watch it come to life
                            </p>
                        </div>
                        {/* WebSocket status indicator */}
                        <div className="flex items-center gap-2 text-xs">
                            <span className={`w-2 h-2 rounded-full ${isConnected ? "bg-green-400 animate-pulse" : "bg-red-400"}`} />
                            <span className="text-gray-400">{isConnected ? "Live" : "Offline"}</span>
                        </div>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Left Column - Input */}
                    <div className="space-y-6">
                        {/* Project Selection */}
                        <Card className="bg-gray-800/50 border-gray-700">
                            <CardHeader>
                                <CardTitle className="text-white flex items-center gap-2">
                                    <FolderKanban className="w-5 h-5 text-blue-400" />
                                    Select Project
                                </CardTitle>
                                <CardDescription className="text-gray-400">
                                    Choose which project to provision infrastructure for
                                </CardDescription>
                            </CardHeader>
                            <CardContent>
                                {projects.length === 0 ? (
                                    <div className="text-center py-8">
                                        <p className="text-gray-400 mb-4">No projects found</p>
                                        <Link href="/projects">
                                            <Button className="bg-blue-600 hover:bg-blue-700 text-white">
                                                Create a Project
                                            </Button>
                                        </Link>
                                    </div>
                                ) : (
                                    <div className="space-y-3">
                                        {projects.map(project => (
                                            <div
                                                key={project.project_id}
                                                onClick={() => setSelectedProject(project.project_id)}
                                                className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                                                    selectedProject === project.project_id
                                                        ? "border-blue-500 bg-blue-900/30"
                                                        : "border-gray-700 hover:border-gray-600 bg-gray-900/30"
                                                }`}
                                            >
                                                <div className="flex items-start justify-between">
                                                    <div className="flex-1">
                                                        <h3 className="text-white font-semibold mb-1">
                                                            {project.name}
                                                        </h3>
                                                        {project.description && (
                                                            <p className="text-gray-400 text-sm mb-2">
                                                                {project.description}
                                                            </p>
                                                        )}
                                                        <div className="flex gap-2 flex-wrap">
                                                            {project.cloud_providers.map((cp, idx) => (
                                                                <Badge key={idx} variant="secondary" className="bg-gray-700 text-white">
                                                                    {cp.provider} {cp.region && `(${cp.region})`}
                                                                </Badge>
                                                            ))}
                                                        </div>
                                                    </div>
                                                    {selectedProject === project.project_id && (
                                                        <CheckCircle2 className="w-6 h-6 text-blue-400 flex-shrink-0" />
                                                    )}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </CardContent>
                        </Card>

                        {/* Natural Language Input */}
                        <Card className="bg-gray-800/50 border-gray-700">
                            <CardHeader>
                                <CardTitle className="text-white flex items-center gap-2">
                                    <Zap className="w-5 h-5 text-yellow-400" />
                                    Describe Your Infrastructure
                                </CardTitle>
                                <CardDescription className="text-gray-400">
                                    Tell us what you need in plain English
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <textarea
                                    value={naturalLanguageInput}
                                    onChange={(e) => setNaturalLanguageInput(e.target.value)}
                                    placeholder="E.g., 'Create a web server with a PostgreSQL database and Redis cache for my e-commerce application'"
                                    className="w-full h-32 bg-gray-900 border border-gray-700 text-white rounded-lg px-4 py-3 focus:border-blue-500 focus:outline-none resize-none"
                                    disabled={provisioning || projects.length === 0}
                                />

                                <div className="space-y-2">
                                    <p className="text-sm text-gray-400">Example requests:</p>
                                    <div className="space-y-1">
                                        {[
                                            "Deploy a Node.js web app with MongoDB database",
                                            "Set up a load-balanced web application with auto-scaling",
                                            "Create a Kubernetes cluster for microservices",
                                            "Provision a PostgreSQL database with automated backups"
                                        ].map((example, idx) => (
                                            <button
                                                key={idx}
                                                onClick={() => setNaturalLanguageInput(example)}
                                                disabled={provisioning}
                                                className="block w-full text-left text-sm text-gray-500 hover:text-blue-400 transition-colors py-1 px-2 rounded hover:bg-gray-800/50"
                                            >
                                                • {example}
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                <Button
                                    onClick={handleProvision}
                                    disabled={provisioning || !selectedProject || !naturalLanguageInput.trim() || projects.length === 0}
                                    className="w-full bg-blue-600 hover:bg-blue-700 text-white py-6 text-lg"
                                >
                                    {provisioning ? (
                                        <>
                                            <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                                            Provisioning...
                                        </>
                                    ) : (
                                        <>
                                            <Send className="w-5 h-5 mr-2" />
                                            Provision Infrastructure
                                        </>
                                    )}
                                </Button>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Right Column - Logs & Output */}
                    <div className="space-y-6">
                        {/* MCP Orchestration Pipeline */}
                        {provisioning && activeStep && (
                            <McpPipelineIndicator activeStep={activeStep} />
                        )}

                        {/* Real-time Logs */}
                        <Card className="bg-gray-800/50 border-gray-700">
                            <CardHeader>
                                <CardTitle className="text-white flex items-center gap-2">
                                    <Terminal className="w-5 h-5 text-green-400" />
                                    Provisioning Logs
                                    {provisioning && (
                                        <Loader2 className="w-4 h-4 text-blue-400 animate-spin ml-auto" />
                                    )}
                                </CardTitle>
                                <CardDescription className="text-gray-400">
                                    Real-time MCP tool orchestration and execution logs
                                </CardDescription>
                            </CardHeader>
                            <CardContent>
                                <div className="bg-gray-900 rounded-lg p-4 h-[500px] overflow-y-auto font-mono text-sm">
                                    {logs.length === 0 ? (
                                        <div className="flex items-center justify-center h-full text-gray-500">
                                            <div className="text-center">
                                                <Terminal className="w-12 h-12 mx-auto mb-2 opacity-50" />
                                                <p>Logs will appear here when you start provisioning</p>
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="space-y-1.5">
                                            {logs.map((log, idx) => (
                                                <LogEntry key={idx} log={log} />
                                            ))}
                                            <div ref={logsEndRef} />
                                        </div>
                                    )}
                                </div>
                            </CardContent>
                        </Card>

                        {/* Result Summary */}
                        {result && (
                            <Card className={`border-2 ${result.success ? 'bg-green-900/20 border-green-500/50' : 'bg-red-900/20 border-red-500/50'}`}>
                                <CardHeader>
                                    <CardTitle className={`flex items-center gap-2 ${result.success ? 'text-green-300' : 'text-red-300'}`}>
                                        {result.success ? (
                                            <>
                                                <CheckCircle2 className="w-5 h-5" />
                                                Provisioning Complete
                                            </>
                                        ) : (
                                            <>
                                                <XCircle className="w-5 h-5" />
                                                Provisioning Failed
                                            </>
                                        )}
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    {result.success ? (
                                        <div className="space-y-3">
                                            {result.resources_created && result.resources_created.length > 0 && (
                                                <div>
                                                    <h4 className="text-white font-semibold mb-2">Created Resources:</h4>
                                                    <div className="space-y-2">
                                                        {result.resources_created.map((resource, idx) => (
                                                            <div key={idx} className="bg-gray-800/50 rounded p-3">
                                                                <div className="flex items-center gap-2">
                                                                    <Badge className="bg-blue-600 text-white">
                                                                        {resource.type}
                                                                    </Badge>
                                                                    <span className="text-white font-medium">
                                                                        {resource.name}
                                                                    </span>
                                                                </div>
                                                                <p className="text-gray-400 text-sm mt-1">
                                                                    ID: {resource.id}
                                                                </p>
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}
                                            {result.cost_estimate && (
                                                <div className="bg-gray-800/50 rounded p-3">
                                                    <span className="text-gray-400">Estimated Monthly Cost: </span>
                                                    <span className="text-green-400 font-bold text-lg">
                                                        ${result.cost_estimate.toFixed(2)}
                                                    </span>
                                                </div>
                                            )}
                                            {selectedProjectDetails && (
                                                <Link href={`/projects/${selectedProjectDetails.project_id}/infrastructure`}>
                                                    <Button className="w-full bg-blue-600 hover:bg-blue-700 text-white mt-2">
                                                        View in Infrastructure Graph
                                                    </Button>
                                                </Link>
                                            )}
                                        </div>
                                    ) : (
                                        <div className="text-red-300">
                                            {result.error || "An unknown error occurred"}
                                        </div>
                                    )}
                                </CardContent>
                            </Card>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}


// ─── Sub-Components ──────────────────────────────────────────────────────

/** Visual pipeline showing which MCP step is currently active */
function McpPipelineIndicator({ activeStep }: { activeStep: string }) {
    const steps = [
        { id: "generate_config", label: "Generate", server: "gradient-ai" },
        { id: "validate", label: "Validate", server: "terraform" },
        { id: "estimate_cost", label: "Cost", server: null },
        { id: "plan", label: "Plan", server: "terraform" },
        { id: "apply", label: "Apply", server: "terraform" },
        { id: "extract_outputs", label: "Outputs", server: "terraform" },
        { id: "prometheus_register", label: "Monitor", server: "infra" },
        { id: "update_kb", label: "Learn", server: "gradient-ai" },
    ]

    const activeIdx = steps.findIndex(s => s.id === activeStep)

    return (
        <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-4">
            <div className="flex items-center gap-1 text-xs mb-2">
                <Server className="w-3.5 h-3.5 text-cyan-400" />
                <span className="text-gray-400 font-medium">MCP Tool Orchestration Pipeline</span>
            </div>
            <div className="flex items-center gap-0.5 overflow-x-auto pb-1">
                {steps.map((step, idx) => {
                    const isDone = idx < activeIdx
                    const isActive = idx === activeIdx
                    const style = step.server ? getMcpStyle(step.server) : { color: "text-gray-400", bg: "bg-gray-800/60 border-gray-600/40", icon: "--" }
                    return (
                        <div key={step.id} className="flex items-center">
                            <div className={`
                                flex flex-col items-center px-2 py-1.5 rounded border text-[10px] leading-tight min-w-[52px]
                                ${isActive ? style.bg + " border " + "ring-1 ring-white/20" : isDone ? "bg-gray-800/40 border-gray-700/40" : "bg-gray-900/40 border-gray-800/40"}
                            `}>
                                {step.server && (
                                    <span className={`font-bold ${isActive ? style.color : isDone ? "text-green-400" : "text-gray-600"}`}>
                                        {style.icon}
                                    </span>
                                )}
                                <span className={isActive ? "text-white font-medium" : isDone ? "text-gray-400" : "text-gray-600"}>
                                    {step.label}
                                </span>
                                {isActive && <Loader2 className="w-3 h-3 animate-spin text-cyan-400 mt-0.5" />}
                                {isDone && <CheckCircle2 className="w-3 h-3 text-green-400 mt-0.5" />}
                            </div>
                            {idx < steps.length - 1 && (
                                <ArrowRight className={`w-3 h-3 mx-0.5 flex-shrink-0 ${idx < activeIdx ? "text-green-500" : "text-gray-700"}`} />
                            )}
                        </div>
                    )
                })}
            </div>
        </div>
    )
}


/** Single log entry with optional MCP badge */
function LogEntry({ log }: { log: ProvisionLog }) {
    const hasMcp = log.mcpServer || log.type === "mcp"

    return (
        <div className={`flex items-start gap-2 py-0.5 ${hasMcp ? "pl-0" : ""}`}>
            {/* Status icon */}
            {log.stepStatus === "running" ? (
                <Loader2 className="w-3.5 h-3.5 text-cyan-400 animate-spin flex-shrink-0 mt-0.5" />
            ) : log.type === "success" || log.stepStatus === "done" ? (
                <CheckCircle2 className="w-3.5 h-3.5 text-green-400 flex-shrink-0 mt-0.5" />
            ) : log.type === "error" ? (
                <XCircle className="w-3.5 h-3.5 text-red-400 flex-shrink-0 mt-0.5" />
            ) : log.type === "warning" ? (
                <span className="text-yellow-400 flex-shrink-0 text-xs mt-0.5">!</span>
            ) : (
                <Terminal className="w-3.5 h-3.5 text-gray-500 flex-shrink-0 mt-0.5" />
            )}

            {/* Timestamp */}
            <span className="text-gray-600 text-[10px] flex-shrink-0 mt-0.5 min-w-[60px]">
                {log.timestamp}
            </span>

            {/* MCP Server Badge */}
            {log.mcpServer && (
                <McpBadge server={log.mcpServer} tool={log.mcpTool} />
            )}

            {/* Elapsed time */}
            {log.elapsed !== undefined && (
                <span className="text-gray-600 text-[10px] flex-shrink-0 mt-0.5">
                    {log.elapsed}s
                </span>
            )}

            {/* Message */}
            <span className={`text-xs leading-relaxed ${
                log.type === "success" || log.stepStatus === "done" ? "text-green-300" :
                log.type === "error" ? "text-red-300" :
                log.type === "warning" ? "text-yellow-300" :
                log.type === "mcp" ? "text-cyan-200" :
                "text-gray-300"
            }`}>
                {log.message}
            </span>
        </div>
    )
}


/** Colored badge showing MCP server and tool name */
function McpBadge({ server, tool }: { server: string; tool?: string }) {
    const style = getMcpStyle(server)
    return (
        <span className={`inline-flex items-center gap-1 px-1.5 py-0 rounded text-[10px] font-mono border flex-shrink-0 ${style.bg}`}>
            <span className={`font-bold ${style.color}`}>{server}</span>
            {tool && (
                <>
                    <ArrowRight className="w-2.5 h-2.5 text-gray-500" />
                    <span className="text-gray-300">{tool}</span>
                </>
            )}
        </span>
    )
}


// ─── Helpers ──────────────────────────────────────────────────────────────

/** Parse backend log strings that may contain [MCP:server] prefixes */
function parseBackendLog(raw: string): { message: string; type: ProvisionLog["type"]; mcpServer?: string; mcpTool?: string } {
    // Match [MCP:server] tool_name → result
    const mcpMatch = raw.match(/^\[MCP:(\w[\w-]*)\]\s*(.*)$/)
    if (mcpMatch) {
        const server = mcpMatch[1]
        const rest = mcpMatch[2]
        // Try to extract tool name from "Calling tool_name..." or "✓ tool_name → ..."
        const toolMatch = rest.match(/(?:Calling\s+|✓\s+)(terraform_\w+|infra_\w+|query_agent)/)
        const tool = toolMatch ? toolMatch[1] : undefined
        const isSuccess = rest.includes("✓")
        const isError = rest.includes("❌") || rest.toLowerCase().includes("failed")
        return {
            message: rest,
            type: isSuccess ? "success" : isError ? "error" : "mcp",
            mcpServer: server,
            mcpTool: tool,
        }
    }

    // Regular log classification
    if (raw.includes("✓") || raw.includes("Successfully")) return { message: raw, type: "success" }
    if (raw.includes("⚠️") || raw.includes("Warning")) return { message: raw, type: "warning" }
    if (raw.includes("❌") || raw.includes("Error") || raw.includes("Failed")) return { message: raw, type: "error" }
    return { message: raw, type: "info" }
}

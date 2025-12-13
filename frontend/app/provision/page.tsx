"use client"

import { useEffect, useState, useRef } from "react"
import Link from "next/link"
import { ArrowLeft, Zap, Send, Terminal, CheckCircle2, XCircle, Loader2, FolderKanban, Sparkles } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

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
    type: "info" | "success" | "error" | "warning"
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

export default function ProvisionPage() {
    const [projects, setProjects] = useState<Project[]>([])
    const [selectedProject, setSelectedProject] = useState<string | null>(null)
    const [naturalLanguageInput, setNaturalLanguageInput] = useState("")
    const [provisioning, setProvisioning] = useState(false)
    const [logs, setLogs] = useState<ProvisionLog[]>([])
    const [result, setResult] = useState<ProvisionResult | null>(null)
    const [loading, setLoading] = useState(true)
    
    const logsEndRef = useRef<HTMLDivElement>(null)

    useEffect(() => {
        fetchProjects()
    }, [])

    useEffect(() => {
        // Auto-scroll logs to bottom
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

    const addLog = (message: string, type: ProvisionLog["type"] = "info") => {
        setLogs(prev => [...prev, {
            timestamp: new Date().toLocaleTimeString(),
            message,
            type
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

        addLog("🚀 Starting infrastructure provisioning...", "info")
        addLog(`📝 Request: "${naturalLanguageInput}"`, "info")
        addLog(`📁 Project: ${projects.find(p => p.project_id === selectedProject)?.name}`, "info")

        try {
            const requestBody = {
                user_id: "frontend-user",
                description: naturalLanguageInput,
                region: projects.find(p => p.project_id === selectedProject)?.cloud_providers[0]?.region || "nyc3",
                environment: "production",
                tags: ["frontend-provisioned"]
            }

            addLog("🔄 Sending request to provisioning agent...", "info")

            const url = `${API_URL}/provision/create?project_id=${selectedProject}`
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody)
            })

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
            }

            const data: ProvisionResult = await response.json()
            
            // Display logs from backend
            if (data.logs && data.logs.length > 0) {
                data.logs.forEach(log => {
                    if (log.includes('✓') || log.includes('Successfully')) {
                        addLog(log, "success")
                    } else if (log.includes('⚠️') || log.includes('Warning')) {
                        addLog(log, "warning")
                    } else if (log.includes('❌') || log.includes('Error') || log.includes('Failed')) {
                        addLog(log, "error")
                    } else {
                        addLog(log, "info")
                    }
                })
            }

            setResult(data)

            if (data.success) {
                addLog("✅ Infrastructure provisioning completed successfully!", "success")
                if (data.resources_created && data.resources_created.length > 0) {
                    addLog(`📦 Created ${data.resources_created.length} resource(s)`, "success")
                    data.resources_created.forEach(resource => {
                        addLog(`  ├─ ${resource.type}: ${resource.name} (${resource.id})`, "info")
                    })
                }
                if (data.cost_estimate) {
                    addLog(`💰 Estimated monthly cost: $${data.cost_estimate.toFixed(2)}`, "info")
                }
            } else {
                addLog(`❌ Provisioning failed: ${data.error || 'Unknown error'}`, "error")
            }

        } catch (error) {
            console.error("❌ Failed to provision:", error)
            const errorMessage = error instanceof Error ? error.message : 'Unknown error'
            addLog(`❌ Error: ${errorMessage}`, "error")
        } finally {
            setProvisioning(false)
        }
    }

    const getLogIcon = (type: ProvisionLog["type"]) => {
        switch (type) {
            case "success":
                return <CheckCircle2 className="w-4 h-4 text-green-400 flex-shrink-0" />
            case "error":
                return <XCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
            case "warning":
                return <span className="text-yellow-400 flex-shrink-0">⚠️</span>
            default:
                return <Terminal className="w-4 h-4 text-blue-400 flex-shrink-0" />
        }
    }

    const getLogColor = (type: ProvisionLog["type"]) => {
        switch (type) {
            case "success":
                return "text-green-300"
            case "error":
                return "text-red-300"
            case "warning":
                return "text-yellow-300"
            default:
                return "text-gray-300"
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
                                    Real-time execution logs and status updates
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
                                        <div className="space-y-2">
                                            {logs.map((log, idx) => (
                                                <div key={idx} className="flex items-start gap-2">
                                                    {getLogIcon(log.type)}
                                                    <span className="text-gray-500 text-xs flex-shrink-0">
                                                        {log.timestamp}
                                                    </span>
                                                    <span className={getLogColor(log.type)}>
                                                        {log.message}
                                                    </span>
                                                </div>
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

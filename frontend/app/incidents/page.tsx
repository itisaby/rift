"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { ArrowLeft, AlertTriangle, CheckCircle2, Clock, XCircle, Filter, Search } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface Incident {
    id: string
    resource_name: string
    severity: string
    status: string
    description: string
    timestamp: string
    detection_method?: string
    remediation_actions?: string[]
}

export default function IncidentsPage() {
    const [incidents, setIncidents] = useState<Incident[]>([])
    const [loading, setLoading] = useState(true)
    const [filter, setFilter] = useState<string>("all")

    useEffect(() => {
        fetchIncidents()
        const interval = setInterval(fetchIncidents, 10000) // Refresh every 10s
        return () => clearInterval(interval)
    }, [])

    const fetchIncidents = async () => {
        try {
            console.log("Fetching from:", `${API_URL}/incidents`)
            const response = await fetch(`${API_URL}/incidents`)

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`)
            }

            const data = await response.json()
            console.log("✅ Incidents received:", data)

            // Backend returns: { count: number, incidents: [{ incident: {...}, has_diagnosis: bool, has_remediation: bool }] }
            if (data && Array.isArray(data.incidents)) {
                // Extract the incident objects from the wrapper
                const extractedIncidents = data.incidents.map((item: any) => item.incident)
                setIncidents(extractedIncidents)
            } else if (Array.isArray(data)) {
                setIncidents(data)
            } else {
                setIncidents([])
            }
            setLoading(false)
        } catch (error) {
            console.error("❌ Failed to fetch incidents:", error)
            setIncidents([])
            setLoading(false)
        }
    }

    const getSeverityColor = (severity: string) => {
        switch (severity.toLowerCase()) {
            case 'critical': return 'destructive'
            case 'high': return 'warning'
            case 'medium': return 'secondary'
            case 'low': return 'default'
            default: return 'outline'
        }
    }

    const getStatusColor = (status: string) => {
        switch (status.toLowerCase()) {
            case 'resolved': return 'success'
            case 'remediating': return 'warning'
            case 'detected': return 'destructive'
            default: return 'outline'
        }
    }

    const getStatusIcon = (status: string) => {
        switch (status.toLowerCase()) {
            case 'resolved': return <CheckCircle2 className="w-5 h-5 text-green-400" />
            case 'remediating': return <Clock className="w-5 h-5 text-yellow-400" />
            case 'detected': return <XCircle className="w-5 h-5 text-red-400" />
            default: return <AlertTriangle className="w-5 h-5 text-cyan-400" />
        }
    }

    const filteredIncidents = filter === "all"
        ? incidents
        : incidents.filter(i => i.status.toLowerCase() === filter)

    const stats = {
        total: incidents.length,
        detected: incidents.filter(i => i.status.toLowerCase() === 'detected').length,
        remediating: incidents.filter(i => i.status.toLowerCase() === 'remediating').length,
        resolved: incidents.filter(i => i.status.toLowerCase() === 'resolved').length,
    }

    return (
        <div className="min-h-screen cyber-gradient scanline">
            <header className="border-b border-cyan-500/30 bg-linear-to-r from-black/80 via-cyan-950/30 to-black/80 backdrop-blur-xl sticky top-0 z-50 shadow-lg shadow-cyan-500/10">
                <div className="container mx-auto px-8 py-5">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <Link href="/">
                                <Button variant="outline" size="sm" className="gap-2">
                                    <ArrowLeft className="w-4 h-4" />
                                    <span className="font-mono">BACK</span>
                                </Button>
                            </Link>
                            <div>
                                <h1 className="text-3xl font-black text-transparent bg-clip-text bg-linear-to-r from-red-400 via-orange-400 to-red-400 tracking-wider animate-glow">
                                    INCIDENT MANAGEMENT
                                </h1>
                                <p className="text-sm text-cyan-400/70 font-mono tracking-wide">
                                    REAL-TIME INCIDENT TRACKING & RESOLUTION
                                </p>
                            </div>
                        </div>

                        <div className="flex items-center gap-2">
                            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                            <span className="text-xs text-cyan-400 font-mono">LIVE</span>
                        </div>
                    </div>
                </div>
            </header>

            <main className="container mx-auto px-8 py-10">
                {loading ? (
                    <div className="flex flex-col items-center justify-center h-96">
                        <div className="relative">
                            <div className="w-20 h-20 border-4 border-cyan-500/30 border-t-cyan-400 rounded-full animate-spin"></div>
                            <div className="absolute inset-0 w-20 h-20 border-4 border-purple-500/30 border-b-purple-400 rounded-full animate-spin" style={{ animationDirection: 'reverse', animationDuration: '1.5s' }}></div>
                        </div>
                        <p className="text-cyan-400 text-xl font-mono mt-6 animate-pulse">LOADING INCIDENTS...</p>
                    </div>
                ) : (
                    <>
                        {/* Stats Overview */}
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-10">
                            <Card className="relative overflow-hidden group hover:scale-105 transition-transform duration-300">
                                <CardHeader className="pb-3">
                                    <CardTitle className="text-xs font-mono text-cyan-300/70 uppercase">Total Incidents</CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="text-5xl font-black text-cyan-400">{stats.total}</div>
                                </CardContent>
                            </Card>

                            <Card className="relative overflow-hidden group hover:scale-105 transition-transform duration-300">
                                <CardHeader className="pb-3">
                                    <CardTitle className="text-xs font-mono text-cyan-300/70 uppercase">Detected</CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="text-5xl font-black text-red-400">{stats.detected}</div>
                                </CardContent>
                            </Card>

                            <Card className="relative overflow-hidden group hover:scale-105 transition-transform duration-300">
                                <CardHeader className="pb-3">
                                    <CardTitle className="text-xs font-mono text-cyan-300/70 uppercase">Remediating</CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="text-5xl font-black text-yellow-400">{stats.remediating}</div>
                                </CardContent>
                            </Card>

                            <Card className="relative overflow-hidden group hover:scale-105 transition-transform duration-300">
                                <CardHeader className="pb-3">
                                    <CardTitle className="text-xs font-mono text-cyan-300/70 uppercase">Resolved</CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="text-5xl font-black text-green-400">{stats.resolved}</div>
                                </CardContent>
                            </Card>
                        </div>

                        {/* Filter Buttons */}
                        <div className="flex items-center gap-4 mb-6">
                            <Filter className="w-5 h-5 text-cyan-400" />
                            <div className="flex gap-2">
                                <Button
                                    variant={filter === "all" ? "default" : "outline"}
                                    size="sm"
                                    onClick={() => setFilter("all")}
                                    className="font-mono"
                                >
                                    ALL ({stats.total})
                                </Button>
                                <Button
                                    variant={filter === "detected" ? "default" : "outline"}
                                    size="sm"
                                    onClick={() => setFilter("detected")}
                                    className="font-mono"
                                >
                                    DETECTED ({stats.detected})
                                </Button>
                                <Button
                                    variant={filter === "remediating" ? "default" : "outline"}
                                    size="sm"
                                    onClick={() => setFilter("remediating")}
                                    className="font-mono"
                                >
                                    REMEDIATING ({stats.remediating})
                                </Button>
                                <Button
                                    variant={filter === "resolved" ? "default" : "outline"}
                                    size="sm"
                                    onClick={() => setFilter("resolved")}
                                    className="font-mono"
                                >
                                    RESOLVED ({stats.resolved})
                                </Button>
                            </div>
                        </div>

                        {/* Incidents List */}
                        <Card className="overflow-hidden">
                            <div className="bg-linear-to-r from-red-500/10 via-orange-500/10 to-red-500/10 p-6 border-b border-cyan-500/20">
                                <CardTitle className="flex items-center gap-3 text-2xl font-bold text-cyan-300">
                                    <AlertTriangle className="w-6 h-6" />
                                    INCIDENTS ({filteredIncidents.length})
                                </CardTitle>
                                <CardDescription className="mt-2 font-mono">All infrastructure incidents</CardDescription>
                            </div>
                            <CardContent className="p-6">
                                {filteredIncidents.length === 0 ? (
                                    <div className="text-center py-12">
                                        <div className="relative inline-block">
                                            <div className="absolute inset-0 bg-green-500/20 blur-2xl rounded-full"></div>
                                            <CheckCircle2 className="relative w-16 h-16 mx-auto mb-4 text-green-400" />
                                        </div>
                                        <p className="text-xl font-mono text-cyan-300 mb-2">NO INCIDENTS FOUND</p>
                                        <p className="text-sm text-cyan-400/60">
                                            {filter === "all" ? "System is healthy" : `No ${filter} incidents`}
                                        </p>
                                    </div>
                                ) : (
                                    <div className="space-y-4">
                                        {filteredIncidents.map((incident, index) => (
                                            <Link key={incident.id} href={`/incidents/${incident.id}`}>
                                                <div
                                                    className="group p-6 rounded-xl border border-cyan-500/20 bg-linear-to-r from-black via-cyan-950/5 to-black hover:border-cyan-400/40 transition-all duration-300 hover:shadow-lg hover:shadow-cyan-500/10 cursor-pointer"
                                                    style={{ animationDelay: `${index * 0.05}s` }}
                                                >
                                                <div className="flex items-start justify-between mb-4">
                                                    <div className="flex items-center gap-4">
                                                        {getStatusIcon(incident.status)}
                                                        <div>
                                                            <h3 className="text-xl font-bold text-cyan-300 font-mono mb-1">
                                                                {incident.resource_name}
                                                            </h3>
                                                            <div className="flex items-center gap-2">
                                                                <Badge variant={getSeverityColor(incident.severity)} className="uppercase font-mono">
                                                                    {incident.severity}
                                                                </Badge>
                                                                <Badge variant={getStatusColor(incident.status)} className="uppercase font-mono">
                                                                    {incident.status}
                                                                </Badge>
                                                            </div>
                                                        </div>
                                                    </div>
                                                    <div className="text-right">
                                                        <p className="text-xs text-cyan-300/50 font-mono">
                                                            {new Date(incident.timestamp).toLocaleDateString()}
                                                        </p>
                                                        <p className="text-xs text-cyan-300/50 font-mono">
                                                            {new Date(incident.timestamp).toLocaleTimeString()}
                                                        </p>
                                                    </div>
                                                </div>

                                                <p className="text-sm text-cyan-300/80 mb-4 leading-relaxed">
                                                    {incident.description}
                                                </p>

                                                {incident.detection_method && (
                                                    <div className="text-xs text-cyan-400/60 font-mono">
                                                        Detection: {incident.detection_method}
                                                    </div>
                                                )}

                                                {incident.remediation_actions && incident.remediation_actions.length > 0 && (
                                                    <div className="mt-3 pt-3 border-t border-cyan-500/20">
                                                        <p className="text-xs text-purple-400 font-mono mb-2">REMEDIATION ACTIONS:</p>
                                                        <ul className="space-y-1">
                                                            {incident.remediation_actions.map((action, i) => (
                                                                <li key={i} className="text-xs text-cyan-300/70 font-mono flex items-center gap-2">
                                                                    <div className="w-1 h-1 bg-purple-400 rounded-full"></div>
                                                                    {action}
                                                                </li>
                                                            ))}
                                                        </ul>
                                                    </div>
                                                )}
                                            </div>
                                            </Link>
                                        ))}
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    </>
                )}
            </main>
        </div>
    )
}

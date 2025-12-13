"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { Activity, Zap, AlertTriangle, CheckCircle2, TrendingUp, Server, FolderKanban } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { useWebSocket } from "@/lib/useWebSocket"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
const WS_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace('http', 'ws') + '/ws/events'

interface SystemStatus {
  agents: Array<{
    agent_name: string
    status: string
  }>
  active_incidents: number
  incidents_resolved_today: number
  autonomous_mode: boolean
}

interface RecentIncident {
  id: string
  resource_name: string
  severity: string
  status: string
  description: string
  timestamp: string
}

export default function Dashboard() {
  const [status, setStatus] = useState<SystemStatus | null>(null)
  const [recentIncidents, setRecentIncidents] = useState<RecentIncident[]>([])
  const [loading, setLoading] = useState(true)
  const [injecting, setInjecting] = useState(false)

  // WebSocket connection for real-time updates
  const { isConnected, lastMessage } = useWebSocket(WS_URL, {
    onMessage: (message) => {
      console.log('📡 WebSocket message received:', message)

      // Handle different message types
      if (message.type === 'incident_detected' ||
          message.type === 'diagnosis_complete' ||
          message.type === 'remediation_complete') {
        // Refresh incidents when we get updates
        fetchRecentIncidents()
        fetchSystemStatus()
      }
    },
    onConnect: () => {
      console.log('✅ WebSocket connected - receiving real-time updates')
    },
    onDisconnect: () => {
      console.log('⚠️ WebSocket disconnected - falling back to polling')
    }
  })

  // Declare functions BEFORE useEffect
  const fetchSystemStatus = async () => {
    try {
      console.log("Fetching from:", `${API_URL}/status`)
      const response = await fetch(`${API_URL}/status`)

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      console.log("✅ System status received:", data)
      setStatus(data)
      setLoading(false)
    } catch (error) {
      console.error("❌ Failed to fetch system status:", error)
      setLoading(false)
    }
  }

  const fetchRecentIncidents = async () => {
    try {
      console.log("Fetching from:", `${API_URL}/incidents?limit=5`)
      const response = await fetch(`${API_URL}/incidents?limit=5`)

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      console.log("✅ Incidents data received:", data)

      // Backend returns: { count: number, incidents: [{ incident: {...}, has_diagnosis: bool, has_remediation: bool }] }
      if (data && Array.isArray(data.incidents)) {
        // Extract the incident objects from the wrapper
        const extractedIncidents = data.incidents.map((item: any) => item.incident)
        setRecentIncidents(extractedIncidents)
      } else if (Array.isArray(data)) {
        setRecentIncidents(data)
      } else {
        console.log("⚠️ No incidents array found, using empty array")
        setRecentIncidents([])
      }
    } catch (error) {
      console.error("❌ Failed to fetch incidents:", error)
      setRecentIncidents([])
    }
  }

  const handleInjectFailure = async () => {
    setInjecting(true)
    try {
      console.log("Injecting demo failure...")
      const response = await fetch(`${API_URL}/demo/inject-failure`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          resource_name: "demo-web-app",
          failure_type: "high_cpu"
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      console.log("✅ Failure injected:", data)

      // Refresh data immediately
      await fetchSystemStatus()
      await fetchRecentIncidents()

      alert(`✅ Demo failure injected!\n\n${data.message || 'Check the incidents page to see the new incident.'}`)
    } catch (error) {
      console.error("❌ Failed to inject failure:", error)
      alert(`❌ Failed to inject demo failure. Error: ${error}`)
    } finally {
      setInjecting(false)
    }
  }

  useEffect(() => {
    fetchSystemStatus()
    fetchRecentIncidents()

    const interval = setInterval(() => {
      fetchSystemStatus()
      fetchRecentIncidents()
    }, 5000)

    return () => clearInterval(interval)
  }, [])

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
      case 'healthy': return 'success'
      case 'unhealthy': return 'destructive'
      default: return 'outline'
    }
  }

  return (
    <div className="min-h-screen cyber-gradient scanline">
      <header className="border-b border-cyan-500/30 bg-linear-to-r from-black/80 via-cyan-950/30 to-black/80 backdrop-blur-xl sticky top-0 z-50 shadow-lg shadow-cyan-500/10">
        <div className="container mx-auto px-8 py-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="relative">
                <div className="absolute inset-0 bg-cyan-500/20 blur-xl rounded-full animate-pulse-slow"></div>
                <div className="relative text-5xl">🌌</div>
              </div>
              <div>
                <h1 className="text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-purple-400 to-cyan-400 tracking-wider animate-glow">
                  RIFT
                </h1>
                <p className="text-sm text-cyan-400/70 font-mono tracking-wide">
                  AUTONOMOUS INFRASTRUCTURE ORCHESTRATOR
                </p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              {/* WebSocket Status */}
              <div className="flex items-center gap-3 px-4 py-2 rounded-lg border border-cyan-500/30 bg-black/40 backdrop-blur-sm">
                <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-400 animate-pulse' : 'bg-yellow-400'}`}></div>
                <span className="text-xs font-mono text-cyan-300">
                  {isConnected ? "LIVE" : "POLLING"}
                </span>
              </div>
              {status && (
                <div className="flex items-center gap-3 px-4 py-2 rounded-lg border border-cyan-500/30 bg-black/40 backdrop-blur-sm">
                  <div className={`w-2 h-2 rounded-full ${status.autonomous_mode ? 'bg-green-400 animate-pulse' : 'bg-gray-400'}`}></div>
                  <span className="text-sm font-mono text-cyan-300">
                    {status.autonomous_mode ? "AUTONOMOUS MODE" : "MANUAL MODE"}
                  </span>
                </div>
              )}
              <Link href="/projects">
                <Button variant="outline" className="gap-2">
                  <Server className="w-4 h-4" />
                  <span className="font-mono">PROJECTS</span>
                </Button>
              </Link>
              <Link href="/incidents">
                <Button variant="outline" className="gap-2">
                  <AlertTriangle className="w-4 h-4" />
                  <span className="font-mono">INCIDENTS</span>
                </Button>
              </Link>
              <Link href="/provision">
                <Button variant="secondary" className="gap-2">
                  <Zap className="w-4 h-4" />
                  <span className="font-mono">PROVISION</span>
                </Button>
              </Link>
              <Link href="/agents">
                <Button variant="outline" className="gap-2 border-purple-500/30 text-purple-400 hover:bg-purple-500/10">
                  <Activity className="w-4 h-4" />
                  <span className="font-mono">TEST AGENTS</span>
                </Button>
              </Link>
              <Button
                variant="outline"
                className="gap-2 border-red-500/30 text-red-400 hover:bg-red-500/10"
                onClick={handleInjectFailure}
                disabled={injecting}
              >
                {injecting ? (
                  <>
                    <div className="w-4 h-4 border-2 border-red-500/30 border-t-red-400 rounded-full animate-spin"></div>
                    <span className="font-mono">INJECTING...</span>
                  </>
                ) : (
                  <>
                    <Activity className="w-4 h-4" />
                    <span className="font-mono">DEMO FAILURE</span>
                  </>
                )}
              </Button>
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
            <p className="text-cyan-400 text-xl font-mono mt-6 animate-pulse">INITIALIZING RIFT SYSTEM...</p>
          </div>
        ) : (
          <>
            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
              {/* Active Incidents */}
              <Card className="relative overflow-hidden group hover:scale-105 transition-transform duration-300">
                <div className="absolute inset-0 bg-gradient-to-br from-red-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-xs font-mono text-cyan-300/70 uppercase tracking-wider">Active Incidents</CardTitle>
                    <AlertTriangle className="w-4 h-4 text-red-400" />
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-5xl font-black text-transparent bg-clip-text bg-gradient-to-br from-red-400 to-red-600">
                    {status?.active_incidents || 0}
                  </div>
                  <p className="text-xs text-cyan-300/60 mt-2 font-mono">REQUIRING ATTENTION</p>
                </CardContent>
              </Card>

              {/* Resolved Today */}
              <Card className="relative overflow-hidden group hover:scale-105 transition-transform duration-300" style={{ animationDelay: '0.1s' }}>
                <div className="absolute inset-0 bg-gradient-to-br from-green-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-xs font-mono text-cyan-300/70 uppercase tracking-wider">Resolved Today</CardTitle>
                    <CheckCircle2 className="w-4 h-4 text-green-400" />
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-5xl font-black text-transparent bg-clip-text bg-gradient-to-br from-green-400 to-green-600">
                    {status?.incidents_resolved_today || 0}
                  </div>
                  <p className="text-xs text-cyan-300/60 mt-2 font-mono">AUTO-REMEDIATED</p>
                </CardContent>
              </Card>

              {/* Agent Status */}
              <Card className="relative overflow-hidden group hover:scale-105 transition-transform duration-300" style={{ animationDelay: '0.2s' }}>
                <div className="absolute inset-0 bg-gradient-to-br from-purple-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-xs font-mono text-cyan-300/70 uppercase tracking-wider">Agent Status</CardTitle>
                    <Activity className="w-4 h-4 text-purple-400" />
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-5xl font-black text-transparent bg-clip-text bg-gradient-to-br from-purple-400 to-purple-600">
                    {status?.agents.filter(a => a.status === 'healthy').length || 0}<span className="text-2xl text-cyan-500/50">/{status?.agents.length || 0}</span>
                  </div>
                  <p className="text-xs text-cyan-300/60 mt-2 font-mono">AGENTS OPERATIONAL</p>
                </CardContent>
              </Card>

              {/* System Mode */}
              <Card className="relative overflow-hidden group hover:scale-105 transition-transform duration-300" style={{ animationDelay: '0.3s' }}>
                <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-xs font-mono text-cyan-300/70 uppercase tracking-wider">System Mode</CardTitle>
                    <Zap className="w-4 h-4 text-cyan-400" />
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-4xl font-black text-transparent bg-clip-text bg-gradient-to-br from-cyan-400 to-cyan-600">
                    {status?.autonomous_mode ? "AUTO" : "MANUAL"}
                  </div>
                  <p className="text-xs text-cyan-300/60 mt-2 font-mono">OPERATION MODE</p>
                </CardContent>
              </Card>
            </div>

            {/* AI Agents Grid */}
            <Card className="mb-10 overflow-hidden">
              <div className="bg-linear-to-r from-cyan-500/10 via-purple-500/10 to-cyan-500/10 p-6 border-b border-cyan-500/20">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-3 text-2xl font-bold text-cyan-300">
                      <Server className="w-6 h-6" />
                      AI AGENTS STATUS
                    </CardTitle>
                    <CardDescription className="mt-2 font-mono">Real-time monitoring of autonomous agents</CardDescription>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                    <span className="text-xs text-cyan-400 font-mono">LIVE</span>
                  </div>
                </div>
              </div>
              <CardContent className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {status?.agents && status.agents.map((agent, index) => (
                    <div
                      key={agent.agent_name}
                      className="group relative p-6 rounded-xl border border-cyan-500/30 bg-linear-to-br from-black via-cyan-950/10 to-black hover:border-cyan-400/50 transition-all duration-300 hover:shadow-lg hover:shadow-cyan-500/20 hover:-translate-y-1"
                      style={{ animationDelay: `${index * 0.1}s` }}
                    >
                      <div className="absolute top-0 right-0 w-20 h-20 bg-cyan-500/5 rounded-full blur-2xl group-hover:bg-cyan-500/10 transition-all"></div>

                      <div className="relative">
                        <div className="flex items-center justify-between mb-4">
                          <div className="flex items-center gap-3">
                            <div className={`w-3 h-3 rounded-full ${agent.status === 'healthy' ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`}></div>
                            <h4 className="font-bold text-lg capitalize text-cyan-300 font-mono">
                              {agent.agent_name}
                            </h4>
                          </div>
                          <Badge variant={getStatusColor(agent.status)} className="uppercase font-mono">
                            {agent.status}
                          </Badge>
                        </div>

                        <div className="space-y-2">
                          <p className="text-sm text-cyan-300/80">
                            {agent.agent_name === 'monitor' && '🔍 Detecting infrastructure issues'}
                            {agent.agent_name === 'diagnostic' && '🧠 Analyzing root causes'}
                            {agent.agent_name === 'remediation' && '⚡ Executing fixes'}
                          </p>

                          <div className="flex items-center gap-4 pt-3 border-t border-cyan-500/20">
                            <div className="flex items-center gap-2">
                              <div className="w-1.5 h-1.5 bg-cyan-400 rounded-full"></div>
                              <span className="text-xs text-cyan-400/70 font-mono">ONLINE</span>
                            </div>
                            <div className="flex items-center gap-2">
                              <Activity className="w-3 h-3 text-purple-400" />
                              <span className="text-xs text-purple-400/70 font-mono">READY</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Recent Activity */}
            <Card className="overflow-hidden">
              <div className="bg-gradient-to-r from-purple-500/10 via-cyan-500/10 to-purple-500/10 p-6 border-b border-cyan-500/20">
                <CardTitle className="flex items-center gap-3 text-2xl font-bold text-cyan-300">
                  <TrendingUp className="w-6 h-6" />
                  RECENT ACTIVITY
                </CardTitle>
                <CardDescription className="mt-2 font-mono">Latest incidents and remediations</CardDescription>
              </div>
              <CardContent className="p-6">
                {recentIncidents.length === 0 ? (
                  <div className="text-center py-12">
                    <div className="relative inline-block">
                      <div className="absolute inset-0 bg-green-500/20 blur-2xl rounded-full"></div>
                      <CheckCircle2 className="relative w-16 h-16 mx-auto mb-4 text-green-400" />
                    </div>
                    <p className="text-xl font-mono text-cyan-300 mb-2">SYSTEM HEALTHY</p>
                    <p className="text-sm text-cyan-400/60">No recent incidents detected</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {recentIncidents.map((incident, index) => (
                      <div
                        key={incident.id}
                        className="group p-5 rounded-xl border border-cyan-500/20 bg-gradient-to-r from-black via-cyan-950/5 to-black hover:border-cyan-400/40 transition-all duration-300 hover:shadow-lg hover:shadow-cyan-500/10 cursor-pointer"
                        style={{ animationDelay: `${index * 0.05}s` }}
                      >
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex items-center gap-3 flex-wrap">
                            <Badge variant={getSeverityColor(incident.severity)} className="uppercase font-mono">
                              {incident.severity}
                            </Badge>
                            <Badge variant={getStatusColor(incident.status)} className="uppercase font-mono">
                              {incident.status}
                            </Badge>
                            <span className="text-base font-bold text-cyan-300 font-mono">{incident.resource_name}</span>
                          </div>
                          <span className="text-xs text-cyan-300/50 font-mono whitespace-nowrap ml-4">
                            {new Date(incident.timestamp).toLocaleTimeString()}
                          </span>
                        </div>
                        <p className="text-sm text-cyan-300/80 leading-relaxed">{incident.description}</p>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </>
        )}
      </main>

      <footer className="border-t border-cyan-500/30 bg-linear-to-r from-black/80 via-cyan-950/20 to-black/80 backdrop-blur-xl mt-16">
        <div className="container mx-auto px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse"></div>
              <p className="text-sm text-cyan-400/70 font-mono">
                POWERED BY <span className="text-cyan-300 font-bold">DIGITALOCEAN GRADIENT AI</span> + <span className="text-purple-400 font-bold">MCP</span>
              </p>
            </div>
            <p className="text-sm text-cyan-400/70 font-mono italic">
              &quot;Rift through operational complexity&quot;
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}

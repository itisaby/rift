"use client"

import { useEffect, useState, useRef, useCallback } from "react"
import Link from "next/link"
import { useParams } from "next/navigation"
import { ArrowLeft, RefreshCw, ZoomIn, ZoomOut, Maximize2, Trash2, Loader2, Flame, Server, Database, Shield, HardDrive, Cloud } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface InfrastructureNode {
  id: string
  name: string
  type: string
  provider: string
  status: string
  region: string
  x?: number
  y?: number
  cost_per_month?: number
  tags: string[]
}

interface InfrastructureEdge {
  source: string
  target: string
  relationship: string
}

interface InfrastructureGraph {
  project_id: string
  nodes: InfrastructureNode[]
  edges: InfrastructureEdge[]
  generated_at: string
}

const NODE_WIDTH = 220
const NODE_HEIGHT = 90

export default function InfrastructureVisualizationPage() {
  const params = useParams()
  const projectId = params.project_id as string

  const [graph, setGraph] = useState<InfrastructureGraph | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedNode, setSelectedNode] = useState<InfrastructureNode | null>(null)
  const [zoom, setZoom] = useState(1)
  const [pan, setPan] = useState({ x: 0, y: 0 })
  const [isPanning, setIsPanning] = useState(false)
  const [panStart, setPanStart] = useState({ x: 0, y: 0 })
  const [destroyingInfra, setDestroyingInfra] = useState(false)
  const canvasRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (projectId) fetchInfrastructureGraph()
  }, [projectId])

  const fetchInfrastructureGraph = async () => {
    try {
      const response = await fetch(`${API_URL}/projects/${projectId}/infrastructure`)
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
      const data = await response.json()
      setGraph(data)
      setLoading(false)
    } catch (error) {
      console.error("Failed to fetch graph:", error)
      setLoading(false)
    }
  }

  const handleDestroyInfrastructure = async () => {
    if (!confirm(
      `Are you sure you want to destroy ALL infrastructure for this project?\n\n` +
      `This will run terraform destroy and permanently remove ${graph?.nodes.length || 0} resource(s) ` +
      `from your cloud provider.\n\nThis action cannot be undone.`
    )) return

    setDestroyingInfra(true)
    try {
      const response = await fetch(`${API_URL}/projects/${projectId}/infrastructure`, { method: "DELETE" })
      if (response.ok) {
        const data = await response.json()
        alert(`Infrastructure destroyed successfully.\n\n${data.message}`)
        setSelectedNode(null)
        fetchInfrastructureGraph()
      } else {
        const errorData = await response.json().catch(() => ({ detail: "Unknown error" }))
        alert(`Failed to destroy infrastructure: ${errorData.detail || "Unknown error"}`)
      }
    } catch (error) {
      alert("Failed to destroy infrastructure. Check console for details.")
    } finally {
      setDestroyingInfra(false)
    }
  }

  // Pan handlers
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (e.target === canvasRef.current || (e.target as HTMLElement).tagName === "svg") {
      setIsPanning(true)
      setPanStart({ x: e.clientX - pan.x, y: e.clientY - pan.y })
    }
  }, [pan])

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (isPanning) {
      setPan({ x: e.clientX - panStart.x, y: e.clientY - panStart.y })
    }
  }, [isPanning, panStart])

  const handleMouseUp = useCallback(() => setIsPanning(false), [])

  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault()
    const delta = e.deltaY > 0 ? -0.05 : 0.05
    setZoom(z => Math.min(2, Math.max(0.3, z + delta)))
  }, [])

  const resetView = () => { setZoom(1); setPan({ x: 0, y: 0 }) }

  const getNodeStyle = (type: string) => {
    switch (type.toLowerCase()) {
      case "droplet": case "vm": case "ec2_instance":
        return { bg: "from-blue-600 to-blue-700", border: "border-blue-400/50", icon: Server }
      case "database": case "rds_instance":
        return { bg: "from-emerald-600 to-emerald-700", border: "border-emerald-400/50", icon: Database }
      case "loadbalancer": case "alb": case "elb":
        return { bg: "from-purple-600 to-purple-700", border: "border-purple-400/50", icon: Cloud }
      case "storage": case "volume": case "s3_bucket":
        return { bg: "from-amber-600 to-amber-700", border: "border-amber-400/50", icon: HardDrive }
      case "security_group": case "firewall":
        return { bg: "from-orange-600 to-orange-700", border: "border-orange-400/50", icon: Shield }
      default:
        return { bg: "from-gray-600 to-gray-700", border: "border-gray-400/50", icon: Server }
    }
  }

  const getStatusDot = (status: string) => {
    switch (status.toLowerCase()) {
      case "active": case "running": return "bg-green-400"
      case "warning": return "bg-yellow-400"
      case "error": case "failed": return "bg-red-400"
      default: return "bg-gray-400"
    }
  }

  const getProviderLabel = (provider: string) => {
    switch (provider.toLowerCase()) {
      case "digitalocean": return { name: "DigitalOcean", color: "text-blue-300", bg: "bg-blue-500/10 border-blue-500/30" }
      case "aws": return { name: "AWS", color: "text-orange-300", bg: "bg-orange-500/10 border-orange-500/30" }
      case "azure": return { name: "Azure", color: "text-cyan-300", bg: "bg-cyan-500/10 border-cyan-500/30" }
      case "gcp": return { name: "GCP", color: "text-red-300", bg: "bg-red-500/10 border-red-500/30" }
      default: return { name: provider, color: "text-gray-300", bg: "bg-gray-500/10 border-gray-500/30" }
    }
  }

  // Compute provider groups for labels
  const providerGroups = graph ? (() => {
    const groups: Record<string, { minX: number; maxX: number; minY: number; maxY: number }> = {}
    for (const node of graph.nodes) {
      const p = node.provider
      const x = node.x || 0
      const y = node.y || 0
      if (!groups[p]) {
        groups[p] = { minX: x, maxX: x + NODE_WIDTH, minY: y, maxY: y + NODE_HEIGHT }
      } else {
        groups[p].minX = Math.min(groups[p].minX, x)
        groups[p].maxX = Math.max(groups[p].maxX, x + NODE_WIDTH)
        groups[p].minY = Math.min(groups[p].minY, y)
        groups[p].maxY = Math.max(groups[p].maxY, y + NODE_HEIGHT)
      }
    }
    return groups
  })() : {}

  // Compute canvas bounds
  const canvasBounds = graph ? (() => {
    let maxX = 0, maxY = 0
    for (const node of graph.nodes) {
      maxX = Math.max(maxX, (node.x || 0) + NODE_WIDTH + 80)
      maxY = Math.max(maxY, (node.y || 0) + NODE_HEIGHT + 80)
    }
    return { width: Math.max(800, maxX), height: Math.max(600, maxY) }
  })() : { width: 800, height: 600 }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 p-8">
        <div className="max-w-7xl mx-auto flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 text-blue-400 animate-spin mr-3" />
          <span className="text-gray-300 text-lg">Loading infrastructure graph...</span>
        </div>
      </div>
    )
  }

  if (!graph || graph.nodes.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="mb-8">
            <Link href="/projects">
              <Button variant="outline" className="bg-gray-800 border-gray-700 text-white hover:bg-gray-700 mb-4">
                <ArrowLeft className="w-4 h-4 mr-2" /> Back to Projects
              </Button>
            </Link>
          </div>
          <Card className="bg-gray-800/50 border-gray-700">
            <CardContent className="p-12 text-center">
              <Cloud className="w-16 h-16 text-gray-600 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-white mb-2">No infrastructure yet</h3>
              <p className="text-gray-400">Provision some resources to see them visualized here</p>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 p-6">
      <div className="max-w-[1600px] mx-auto">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link href="/projects">
                <Button variant="outline" size="sm" className="bg-gray-800 border-gray-700 text-white hover:bg-gray-700">
                  <ArrowLeft className="w-4 h-4" />
                </Button>
              </Link>
              <div>
                <h1 className="text-2xl font-bold text-white">Infrastructure</h1>
                <p className="text-sm text-gray-400">
                  {graph.nodes.length} resource{graph.nodes.length !== 1 ? "s" : ""} across {Object.keys(providerGroups).length} provider{Object.keys(providerGroups).length !== 1 ? "s" : ""}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className="flex items-center bg-gray-800/80 border border-gray-700 rounded-lg p-1 gap-1">
                <Button variant="ghost" size="sm" className="h-7 w-7 p-0 text-gray-400 hover:text-white hover:bg-gray-700" onClick={() => setZoom(z => Math.max(0.3, z - 0.1))}>
                  <ZoomOut className="w-3.5 h-3.5" />
                </Button>
                <span className="text-xs text-gray-400 w-10 text-center">{Math.round(zoom * 100)}%</span>
                <Button variant="ghost" size="sm" className="h-7 w-7 p-0 text-gray-400 hover:text-white hover:bg-gray-700" onClick={() => setZoom(z => Math.min(2, z + 0.1))}>
                  <ZoomIn className="w-3.5 h-3.5" />
                </Button>
                <Button variant="ghost" size="sm" className="h-7 w-7 p-0 text-gray-400 hover:text-white hover:bg-gray-700" onClick={resetView}>
                  <Maximize2 className="w-3.5 h-3.5" />
                </Button>
              </div>
              <Button variant="outline" size="sm" className="bg-gray-800 border-gray-700 text-white hover:bg-gray-700" onClick={() => fetchInfrastructureGraph()}>
                <RefreshCw className="w-3.5 h-3.5 mr-1.5" /> Refresh
              </Button>
              <Button
                variant="outline" size="sm"
                className="bg-red-950/50 border-red-500/30 text-red-400 hover:bg-red-950/80"
                onClick={handleDestroyInfrastructure}
                disabled={destroyingInfra}
              >
                {destroyingInfra ? (
                  <><Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" /> Destroying...</>
                ) : (
                  <><Flame className="w-3.5 h-3.5 mr-1.5" /> Destroy All</>
                )}
              </Button>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
          {/* Graph Canvas */}
          <div className="lg:col-span-3">
            <div
              ref={canvasRef}
              className="relative bg-gray-900/80 border border-gray-700/50 rounded-xl overflow-hidden h-[700px] cursor-grab active:cursor-grabbing"
              onMouseDown={handleMouseDown}
              onMouseMove={handleMouseMove}
              onMouseUp={handleMouseUp}
              onMouseLeave={handleMouseUp}
              onWheel={handleWheel}
              style={{ userSelect: "none" }}
            >
              {/* Dot grid background */}
              <div className="absolute inset-0 opacity-20" style={{
                backgroundImage: "radial-gradient(circle, #374151 1px, transparent 1px)",
                backgroundSize: "24px 24px",
              }} />

              {/* Pannable + zoomable layer */}
              <div style={{
                transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
                transformOrigin: "0 0",
                width: canvasBounds.width,
                height: canvasBounds.height,
                position: "relative",
              }}>
                {/* Provider group backgrounds */}
                {Object.entries(providerGroups).map(([provider, bounds]) => {
                  const pl = getProviderLabel(provider)
                  const pad = 20
                  return (
                    <div key={`group-${provider}`} className={`absolute rounded-xl border ${pl.bg}`} style={{
                      left: bounds.minX - pad,
                      top: bounds.minY - 40,
                      width: bounds.maxX - bounds.minX + pad * 2,
                      height: bounds.maxY - bounds.minY + 40 + pad,
                    }}>
                      <div className={`px-3 py-1.5 text-xs font-medium ${pl.color} tracking-wide uppercase`}>
                        {pl.name}
                      </div>
                    </div>
                  )
                })}

                {/* SVG edges */}
                <svg
                  className="absolute inset-0"
                  width={canvasBounds.width}
                  height={canvasBounds.height}
                  style={{ pointerEvents: "none" }}
                >
                  <defs>
                    <marker id="arrowhead" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
                      <polygon points="0 0, 8 3, 0 6" fill="#6B7280" />
                    </marker>
                  </defs>
                  {graph.edges.map((edge, idx) => {
                    const src = graph.nodes.find(n => n.id === edge.source)
                    const tgt = graph.nodes.find(n => n.id === edge.target)
                    if (!src || !tgt) return null

                    const x1 = (src.x || 0) + NODE_WIDTH / 2
                    const y1 = (src.y || 0) + NODE_HEIGHT / 2
                    const x2 = (tgt.x || 0) + NODE_WIDTH / 2
                    const y2 = (tgt.y || 0) + NODE_HEIGHT / 2

                    // Curved path
                    const midX = (x1 + x2) / 2
                    const midY = (y1 + y2) / 2
                    const dx = x2 - x1
                    const curveOffset = Math.abs(dx) < 50 ? 40 : 0

                    return (
                      <path
                        key={idx}
                        d={`M ${x1} ${y1} Q ${midX + curveOffset} ${midY} ${x2} ${y2}`}
                        fill="none"
                        stroke="#4B5563"
                        strokeWidth="1.5"
                        strokeDasharray="6 3"
                        markerEnd="url(#arrowhead)"
                      />
                    )
                  })}
                </svg>

                {/* Nodes */}
                {graph.nodes.map((node) => {
                  const style = getNodeStyle(node.type)
                  const Icon = style.icon
                  const isSelected = selectedNode?.id === node.id
                  return (
                    <div
                      key={node.id}
                      className={`absolute transition-all duration-150 ${isSelected ? "z-20 scale-105" : "z-10 hover:scale-[1.03]"}`}
                      style={{ left: node.x || 0, top: node.y || 0, width: NODE_WIDTH }}
                      onClick={(e) => { e.stopPropagation(); setSelectedNode(node) }}
                    >
                      <div className={`
                        bg-gradient-to-br ${style.bg} ${style.border} border rounded-lg p-3
                        shadow-lg shadow-black/30 cursor-pointer
                        ${isSelected ? "ring-2 ring-white/40 shadow-xl shadow-black/50" : ""}
                      `}>
                        <div className="flex items-start gap-2.5">
                          <div className="bg-black/20 rounded-md p-1.5 mt-0.5">
                            <Icon className="w-4 h-4 text-white/80" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="text-white font-medium text-sm truncate">{node.name}</div>
                            <div className="text-white/60 text-xs mt-0.5">{node.type}</div>
                          </div>
                          <div className={`w-2 h-2 rounded-full mt-1.5 ${getStatusDot(node.status)} shrink-0`} />
                        </div>
                        <div className="flex items-center gap-1.5 mt-2">
                          <Badge variant="secondary" className="bg-black/20 text-white/70 text-[10px] px-1.5 py-0 border-0">
                            {node.region}
                          </Badge>
                          {node.cost_per_month != null && (
                            <span className="text-[10px] text-white/50 ml-auto">${node.cost_per_month}/mo</span>
                          )}
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>

          {/* Side Panel */}
          <div className="lg:col-span-1">
            <div className="sticky top-6 space-y-4">
              {/* Resource details */}
              <Card className="bg-gray-800/60 border-gray-700/50">
                <CardHeader className="pb-3">
                  <CardTitle className="text-white text-sm">
                    {selectedNode ? "Resource Details" : "Select a Resource"}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {selectedNode ? (
                    <div className="space-y-3">
                      <div>
                        <div className="text-[11px] text-gray-500 uppercase tracking-wider mb-1">Name</div>
                        <div className="text-white text-sm font-medium">{selectedNode.name}</div>
                      </div>
                      <div className="flex gap-4">
                        <div>
                          <div className="text-[11px] text-gray-500 uppercase tracking-wider mb-1">Type</div>
                          <Badge className={`bg-gradient-to-r ${getNodeStyle(selectedNode.type).bg} text-white text-xs border-0`}>
                            {selectedNode.type}
                          </Badge>
                        </div>
                        <div>
                          <div className="text-[11px] text-gray-500 uppercase tracking-wider mb-1">Status</div>
                          <div className="flex items-center gap-1.5">
                            <div className={`w-2 h-2 rounded-full ${getStatusDot(selectedNode.status)}`} />
                            <span className="text-white text-sm capitalize">{selectedNode.status}</span>
                          </div>
                        </div>
                      </div>
                      <div>
                        <div className="text-[11px] text-gray-500 uppercase tracking-wider mb-1">Provider</div>
                        <div className={`text-sm ${getProviderLabel(selectedNode.provider).color}`}>
                          {getProviderLabel(selectedNode.provider).name}
                        </div>
                      </div>
                      <div>
                        <div className="text-[11px] text-gray-500 uppercase tracking-wider mb-1">Region</div>
                        <div className="text-white text-sm">{selectedNode.region}</div>
                      </div>
                      {selectedNode.cost_per_month != null && (
                        <div>
                          <div className="text-[11px] text-gray-500 uppercase tracking-wider mb-1">Monthly Cost</div>
                          <div className="text-green-400 font-semibold">${selectedNode.cost_per_month.toFixed(2)}</div>
                        </div>
                      )}
                      {selectedNode.tags.length > 0 && (
                        <div>
                          <div className="text-[11px] text-gray-500 uppercase tracking-wider mb-1.5">Tags</div>
                          <div className="flex flex-wrap gap-1.5">
                            {selectedNode.tags.map((tag, idx) => (
                              <Badge key={idx} variant="secondary" className="bg-gray-700/50 text-gray-300 text-xs border-gray-600/50">
                                {tag}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                      <div className="pt-2 border-t border-gray-700/50">
                        <Button
                          variant="outline" size="sm"
                          className="w-full bg-red-950/30 border-red-500/30 text-red-400 hover:bg-red-950/50 text-xs"
                          onClick={handleDestroyInfrastructure}
                          disabled={destroyingInfra}
                        >
                          {destroyingInfra ? (
                            <><Loader2 className="w-3 h-3 mr-1.5 animate-spin" /> Destroying...</>
                          ) : (
                            <><Trash2 className="w-3 h-3 mr-1.5" /> Destroy Infrastructure</>
                          )}
                        </Button>
                        <p className="text-[10px] text-gray-600 mt-1.5">
                          Runs <code className="text-gray-500">terraform destroy</code>
                        </p>
                      </div>
                    </div>
                  ) : (
                    <div className="text-gray-500 text-center py-6 text-sm">
                      Click a resource node to view details
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Legend */}
              <Card className="bg-gray-800/60 border-gray-700/50">
                <CardHeader className="pb-2">
                  <CardTitle className="text-white text-sm">Legend</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {[
                    { label: "VM / Compute", color: "bg-blue-600" },
                    { label: "Database", color: "bg-emerald-600" },
                    { label: "Load Balancer", color: "bg-purple-600" },
                    { label: "Storage", color: "bg-amber-600" },
                    { label: "Security", color: "bg-orange-600" },
                  ].map(item => (
                    <div key={item.label} className="flex items-center gap-2">
                      <div className={`w-3 h-3 rounded ${item.color}`} />
                      <span className="text-xs text-gray-400">{item.label}</span>
                    </div>
                  ))}
                  <div className="border-t border-gray-700/50 pt-2 mt-2 space-y-1.5">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-green-400" />
                      <span className="text-xs text-gray-400">Active</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-yellow-400" />
                      <span className="text-xs text-gray-400">Warning</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-red-400" />
                      <span className="text-xs text-gray-400">Error</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

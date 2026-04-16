"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { useParams } from "next/navigation"
import { ArrowLeft, RefreshCw, ZoomIn, ZoomOut, Maximize2, Trash2, Loader2, Flame } from "lucide-react"
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

export default function InfrastructureVisualizationPage() {
  const params = useParams()
  const projectId = params.project_id as string

  const [graph, setGraph] = useState<InfrastructureGraph | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedNode, setSelectedNode] = useState<InfrastructureNode | null>(null)
  const [zoom, setZoom] = useState(1)
  const [destroyingInfra, setDestroyingInfra] = useState(false)

  useEffect(() => {
    if (projectId) {
      fetchInfrastructureGraph()
    }
  }, [projectId])

  const fetchInfrastructureGraph = async () => {
    try {
      console.log("Fetching graph from:", `${API_URL}/projects/${projectId}/infrastructure`)
      const response = await fetch(`${API_URL}/projects/${projectId}/infrastructure`)

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      console.log("✅ Graph received:", data)
      setGraph(data)
      setLoading(false)
    } catch (error) {
      console.error("❌ Failed to fetch graph:", error)
      setLoading(false)
    }
  }

  const handleDestroyInfrastructure = async () => {
    if (!confirm(
      `Are you sure you want to destroy ALL infrastructure for this project?\n\n` +
      `This will run terraform destroy and permanently remove ${graph?.nodes.length || 0} resource(s) ` +
      `from your cloud provider.\n\nThis action cannot be undone.`
    )) {
      return
    }

    setDestroyingInfra(true)
    try {
      const response = await fetch(`${API_URL}/projects/${projectId}/infrastructure`, {
        method: "DELETE",
      })

      if (response.ok) {
        const data = await response.json()
        alert(`Infrastructure destroyed successfully.\n\n${data.message}`)
        setSelectedNode(null)
        fetchInfrastructureGraph() // Refresh — should now show empty
      } else {
        const errorData = await response.json().catch(() => ({ detail: "Unknown error" }))
        alert(`Failed to destroy infrastructure: ${errorData.detail || "Unknown error"}`)
      }
    } catch (error) {
      console.error("Failed to destroy infrastructure:", error)
      alert("Failed to destroy infrastructure. Check console for details.")
    } finally {
      setDestroyingInfra(false)
    }
  }

  const getNodeColor = (type: string) => {
    switch (type.toLowerCase()) {
      case "droplet":
      case "vm":
      case "ec2_instance":
        return "bg-blue-600"
      case "database":
      case "rds_instance":
        return "bg-green-600"
      case "loadbalancer":
      case "alb":
      case "elb":
        return "bg-purple-600"
      case "storage":
      case "volume":
      case "s3_bucket":
        return "bg-yellow-600"
      case "kubernetes":
      case "ecs":
      case "eks":
        return "bg-cyan-600"
      case "security_group":
      case "firewall":
        return "bg-orange-600"
      default:
        return "bg-gray-600"
    }
  }

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case "active":
      case "running":
        return "border-green-500"
      case "warning":
        return "border-yellow-500"
      case "error":
      case "failed":
        return "border-red-500"
      default:
        return "border-gray-500"
    }
  }

  const getProviderIcon = (provider: string) => {
    switch (provider.toLowerCase()) {
      case "digitalocean":
        return "🌊"
      case "aws":
        return "☁️"
      case "azure":
        return "🔷"
      case "gcp":
        return "🟦"
      default:
        return "☁️"
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-center h-64">
            <div className="text-white text-xl">Loading infrastructure graph...</div>
          </div>
        </div>
      </div>
    )
  }

  if (!graph || graph.nodes.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="mb-8">
            <Link href="/projects">
              <Button variant="outline" className="bg-gray-800 border-gray-700 text-white hover:bg-gray-700 mb-4">
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back to Projects
              </Button>
            </Link>
          </div>
          <Card className="bg-gray-800/50 border-gray-700">
            <CardContent className="p-12 text-center">
              <h3 className="text-xl font-semibold text-white mb-2">No infrastructure yet</h3>
              <p className="text-gray-400">Provision some resources to see them visualized here</p>
            </CardContent>
          </Card>
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
              <Link href="/projects">
                <Button variant="outline" className="bg-gray-800 border-gray-700 text-white hover:bg-gray-700 mb-4">
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Back to Projects
                </Button>
              </Link>
              <h1 className="text-4xl font-bold text-white mb-2">Infrastructure Visualization</h1>
              <p className="text-gray-300">
                {graph.nodes.length} resources · {graph.edges.length} connections
              </p>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                className="bg-gray-800 border-gray-700 text-white hover:bg-gray-700"
                onClick={() => fetchInfrastructureGraph()}
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Refresh
              </Button>
              <Button
                variant="outline"
                className="bg-gray-800 border-gray-700 text-white hover:bg-gray-700"
                onClick={() => setZoom(Math.max(0.5, zoom - 0.1))}
              >
                <ZoomOut className="w-4 h-4" />
              </Button>
              <Button
                variant="outline"
                className="bg-gray-800 border-gray-700 text-white hover:bg-gray-700"
                onClick={() => setZoom(Math.min(2, zoom + 0.1))}
              >
                <ZoomIn className="w-4 h-4" />
              </Button>
              <Button
                variant="outline"
                className="bg-gray-800 border-gray-700 text-white hover:bg-gray-700"
                onClick={() => setZoom(1)}
              >
                <Maximize2 className="w-4 h-4" />
              </Button>
              <Button
                variant="outline"
                className="bg-red-600/20 border-red-500/50 text-red-400 hover:bg-red-600/30"
                onClick={handleDestroyInfrastructure}
                disabled={destroyingInfra}
              >
                {destroyingInfra ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Destroying...
                  </>
                ) : (
                  <>
                    <Flame className="w-4 h-4 mr-2" />
                    Destroy All
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Graph Visualization */}
          <div className="lg:col-span-3">
            <Card className="bg-gray-800/50 border-gray-700 h-[800px]">
              <CardContent className="p-6 h-full">
                <div 
                  className="relative w-full h-full bg-gray-900/50 rounded-lg overflow-auto"
                  style={{ transform: `scale(${zoom})`, transformOrigin: 'top left' }}
                >
                  <svg className="w-full h-full min-w-[1000px] min-h-[800px]">
                    {/* Draw edges */}
                    {graph.edges.map((edge, idx) => {
                      const sourceNode = graph.nodes.find(n => n.id === edge.source)
                      const targetNode = graph.nodes.find(n => n.id === edge.target)
                      
                      if (!sourceNode || !targetNode) return null
                      
                      const x1 = (sourceNode.x || 0) + 75
                      const y1 = (sourceNode.y || 0) + 50
                      const x2 = (targetNode.x || 0) + 75
                      const y2 = (targetNode.y || 0) + 50
                      
                      return (
                        <g key={idx}>
                          <line
                            x1={x1}
                            y1={y1}
                            x2={x2}
                            y2={y2}
                            stroke="#4B5563"
                            strokeWidth="2"
                            markerEnd="url(#arrowhead)"
                          />
                        </g>
                      )
                    })}
                    
                    {/* Arrow marker */}
                    <defs>
                      <marker
                        id="arrowhead"
                        markerWidth="10"
                        markerHeight="10"
                        refX="9"
                        refY="3"
                        orient="auto"
                      >
                        <polygon points="0 0, 10 3, 0 6" fill="#4B5563" />
                      </marker>
                    </defs>
                  </svg>

                  {/* Draw nodes */}
                  <div className="absolute inset-0">
                    {graph.nodes.map((node) => (
                      <div
                        key={node.id}
                        className={`absolute cursor-pointer transition-transform hover:scale-110 ${
                          selectedNode?.id === node.id ? 'scale-110 z-10' : ''
                        }`}
                        style={{
                          left: `${node.x || 0}px`,
                          top: `${node.y || 0}px`,
                          width: '150px',
                        }}
                        onClick={() => setSelectedNode(node)}
                      >
                        <div className={`${getNodeColor(node.type)} ${getStatusColor(node.status)} border-2 rounded-lg p-3 shadow-lg`}>
                          <div className="text-white font-semibold text-sm mb-1 truncate">
                            {getProviderIcon(node.provider)} {node.name}
                          </div>
                          <div className="text-gray-200 text-xs mb-2">{node.type}</div>
                          <Badge variant="secondary" className="bg-gray-800/50 text-white text-xs">
                            {node.region}
                          </Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Node Details Panel */}
          <div className="lg:col-span-1">
            <Card className="bg-gray-800/50 border-gray-700 sticky top-8">
              <CardHeader>
                <CardTitle className="text-white">
                  {selectedNode ? "Resource Details" : "Select a Resource"}
                </CardTitle>
                <CardDescription className="text-gray-400">
                  {selectedNode ? "Click to view details" : "Click on a node to see details"}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {selectedNode ? (
                  <div className="space-y-4">
                    <div>
                      <div className="text-sm text-gray-400 mb-1">Name</div>
                      <div className="text-white font-semibold">{selectedNode.name}</div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-400 mb-1">Type</div>
                      <Badge className={`${getNodeColor(selectedNode.type)} text-white`}>
                        {selectedNode.type}
                      </Badge>
                    </div>
                    <div>
                      <div className="text-sm text-gray-400 mb-1">Provider</div>
                      <div className="text-white">
                        {getProviderIcon(selectedNode.provider)} {selectedNode.provider}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-400 mb-1">Region</div>
                      <div className="text-white">{selectedNode.region}</div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-400 mb-1">Status</div>
                      <Badge className={`${getStatusColor(selectedNode.status)} bg-gray-700 text-white`}>
                        {selectedNode.status}
                      </Badge>
                    </div>
                    {selectedNode.cost_per_month && (
                      <div>
                        <div className="text-sm text-gray-400 mb-1">Monthly Cost</div>
                        <div className="text-green-400 font-bold">
                          ${selectedNode.cost_per_month.toFixed(2)}
                        </div>
                      </div>
                    )}
                    {selectedNode.tags.length > 0 && (
                      <div>
                        <div className="text-sm text-gray-400 mb-2">Tags</div>
                        <div className="flex flex-wrap gap-2">
                          {selectedNode.tags.map((tag, idx) => (
                            <Badge key={idx} variant="secondary" className="bg-gray-700 text-white">
                              {tag}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                    {/* Destroy action */}
                    <div className="pt-3 border-t border-gray-700">
                      <Button
                        variant="outline"
                        className="w-full bg-red-600/20 border-red-500/50 text-red-400 hover:bg-red-600/30"
                        onClick={handleDestroyInfrastructure}
                        disabled={destroyingInfra}
                      >
                        {destroyingInfra ? (
                          <>
                            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                            Destroying...
                          </>
                        ) : (
                          <>
                            <Trash2 className="w-4 h-4 mr-2" />
                            Destroy Infrastructure
                          </>
                        )}
                      </Button>
                      <p className="text-xs text-gray-500 mt-2">
                        Runs <code className="text-gray-400">terraform destroy</code> to remove all resources from your cloud provider.
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="text-gray-400 text-center py-8">
                    Click on a resource node to view details
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}

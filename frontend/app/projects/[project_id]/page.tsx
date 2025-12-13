"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { useParams, useRouter } from "next/navigation"
import { ArrowLeft, Edit, Trash2, Activity, AlertTriangle, DollarSign, Server, Eye, Zap, RefreshCw } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface CloudProvider {
  provider: string
  region: string
  credentials?: any
}

interface Project {
  project_id: string
  name: string
  description: string
  user_id: string
  cloud_providers: CloudProvider[]
  resources: any[]
  monitoring_enabled: boolean
  auto_remediation: boolean
  status: string
  created_at: string
  updated_at: string
  tags: string[]
  total_resources: number
  active_incidents: number
  total_cost: number
}

interface Incident {
  id: string
  resource_name: string
  severity: string
  description: string
  status: string
  timestamp: string
}

export default function ProjectDetailsPage() {
  const params = useParams()
  const router = useRouter()
  const projectId = params.project_id as string

  const [project, setProject] = useState<Project | null>(null)
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (projectId) {
      fetchProjectDetails()
      fetchIncidents()
    }
  }, [projectId])

  const fetchProjectDetails = async () => {
    try {
      const response = await fetch(`${API_URL}/projects/${projectId}`)
      if (!response.ok) throw new Error("Failed to fetch project")
      const data = await response.json()
      setProject(data)
      setLoading(false)
    } catch (error) {
      console.error("Failed to fetch project:", error)
      setLoading(false)
    }
  }

  const fetchIncidents = async () => {
    try {
      const response = await fetch(`${API_URL}/incidents?limit=10`)
      if (!response.ok) throw new Error("Failed to fetch incidents")
      const data = await response.json()
      // Filter incidents for this project if needed
      setIncidents(data.incidents || [])
    } catch (error) {
      console.error("Failed to fetch incidents:", error)
    }
  }

  const handleDelete = async () => {
    if (!confirm(`Are you sure you want to delete project "${project?.name}"?`)) {
      return
    }

    try {
      const response = await fetch(`${API_URL}/projects/${projectId}`, {
        method: "DELETE",
      })

      if (response.ok) {
        router.push("/projects")
      } else {
        alert("Failed to delete project")
      }
    } catch (error) {
      console.error("Failed to delete project:", error)
      alert("Failed to delete project")
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-center h-64">
            <div className="text-white text-xl">Loading project...</div>
          </div>
        </div>
      </div>
    )
  }

  if (!project) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 p-8">
        <div className="max-w-7xl mx-auto">
          <Card className="bg-gray-800/50 border-gray-700">
            <CardContent className="p-12 text-center">
              <h3 className="text-xl font-semibold text-white mb-2">Project not found</h3>
              <Link href="/projects">
                <Button className="mt-4">Back to Projects</Button>
              </Link>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  const getSeverityColor = (severity: string | undefined) => {
    if (!severity) return "text-gray-500 bg-gray-500/10 border-gray-500"
    
    switch (severity.toLowerCase()) {
      case "critical": return "text-red-500 bg-red-500/10 border-red-500"
      case "high": return "text-orange-500 bg-orange-500/10 border-orange-500"
      case "medium": return "text-yellow-500 bg-yellow-500/10 border-yellow-500"
      case "low": return "text-blue-500 bg-blue-500/10 border-blue-500"
      default: return "text-gray-500 bg-gray-500/10 border-gray-500"
    }
  }

  const getStatusColor = (status: string | undefined) => {
    if (!status) return "bg-gray-500/20 text-gray-400 border-gray-500/50"
    
    switch (status.toLowerCase()) {
      case "active": return "bg-green-500/20 text-green-400 border-green-500/50"
      case "inactive": return "bg-gray-500/20 text-gray-400 border-gray-500/50"
      case "error": return "bg-red-500/20 text-red-400 border-red-500/50"
      default: return "bg-blue-500/20 text-blue-400 border-blue-500/50"
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <Link href="/projects">
            <Button variant="outline" className="bg-gray-800 border-gray-700 text-white hover:bg-gray-700 mb-4">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Projects
            </Button>
          </Link>

          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-4xl font-bold text-white mb-2">{project.name}</h1>
              <p className="text-gray-300 text-lg">{project.description}</p>
              <div className="flex gap-2 mt-3">
                {project.tags.map((tag) => (
                  <Badge key={tag} variant="outline" className="border-blue-500/50 text-blue-400">
                    {tag}
                  </Badge>
                ))}
                <Badge className={getStatusColor(project.status)}>
                  {project.status}
                </Badge>
              </div>
            </div>

            <div className="flex gap-2">
              <Button
                variant="outline"
                className="bg-purple-600/20 border-purple-500/50 text-purple-400 hover:bg-purple-600/30"
                onClick={async () => {
                  try {
                    const response = await fetch(`${API_URL}/projects/${projectId}/sync-resources`, {
                      method: "POST",
                    })
                    if (response.ok) {
                      const data = await response.json()
                      alert(data.message)
                      fetchProjectDetails() // Refresh
                    } else {
                      alert("Failed to sync resources")
                    }
                  } catch (error) {
                    console.error("Sync failed:", error)
                    alert("Failed to sync resources")
                  }
                }}
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Sync Resources
              </Button>
              <Link href={`/projects/${projectId}/infrastructure`}>
                <Button variant="outline" className="bg-gray-800 border-gray-700 text-white hover:bg-gray-700">
                  <Eye className="w-4 h-4 mr-2" />
                  View Infrastructure
                </Button>
              </Link>
              <Link href={`/provision?project=${projectId}`}>
                <Button variant="outline" className="bg-blue-600 border-blue-500 text-white hover:bg-blue-700">
                  <Zap className="w-4 h-4 mr-2" />
                  Provision Resources
                </Button>
              </Link>
              <Button
                variant="outline"
                className="bg-red-600/20 border-red-500/50 text-red-400 hover:bg-red-600/30"
                onClick={handleDelete}
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Delete
              </Button>
            </div>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <Card className="bg-gray-800/50 border-gray-700">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium text-gray-400">Resources</CardTitle>
                <Server className="w-4 h-4 text-blue-400" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-white">{project.total_resources}</div>
              <p className="text-xs text-gray-400 mt-1">Provisioned resources</p>
            </CardContent>
          </Card>

          <Card className="bg-gray-800/50 border-gray-700">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium text-gray-400">Active Incidents</CardTitle>
                <AlertTriangle className="w-4 h-4 text-yellow-400" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-white">{project.active_incidents}</div>
              <p className="text-xs text-gray-400 mt-1">Requires attention</p>
            </CardContent>
          </Card>

          <Card className="bg-gray-800/50 border-gray-700">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium text-gray-400">Monthly Cost</CardTitle>
                <DollarSign className="w-4 h-4 text-green-400" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-white">${project.total_cost.toFixed(2)}</div>
              <p className="text-xs text-gray-400 mt-1">Estimated per month</p>
            </CardContent>
          </Card>

          <Card className="bg-gray-800/50 border-gray-700">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium text-gray-400">Monitoring</CardTitle>
                <Activity className="w-4 h-4 text-purple-400" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-lg font-bold text-white">
                {project.monitoring_enabled ? "Enabled" : "Disabled"}
              </div>
              <p className="text-xs text-gray-400 mt-1">
                Auto-remediation: {project.auto_remediation ? "On" : "Off"}
              </p>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Cloud Providers */}
          <Card className="bg-gray-800/50 border-gray-700">
            <CardHeader>
              <CardTitle className="text-white">Cloud Providers</CardTitle>
              <CardDescription className="text-gray-400">Configured cloud accounts</CardDescription>
            </CardHeader>
            <CardContent>
              {project.cloud_providers.length === 0 ? (
                <p className="text-gray-400 text-sm">No cloud providers configured</p>
              ) : (
                <div className="space-y-4">
                  {project.cloud_providers.map((provider, idx) => (
                    <div key={idx} className="flex items-center justify-between p-4 bg-gray-900/50 rounded-lg">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-blue-500/20 flex items-center justify-center">
                          {provider.provider === "digitalocean" && "🌊"}
                          {provider.provider === "aws" && "☁️"}
                          {provider.provider === "azure" && "🔷"}
                          {provider.provider === "gcp" && "🟦"}
                        </div>
                        <div>
                          <div className="text-white font-medium capitalize">{provider.provider}</div>
                          <div className="text-gray-400 text-sm">{provider.region}</div>
                        </div>
                      </div>
                      <Badge variant="outline" className="border-green-500/50 text-green-400">
                        Connected
                      </Badge>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Recent Incidents */}
          <Card className="bg-gray-800/50 border-gray-700">
            <CardHeader>
              <CardTitle className="text-white">Recent Incidents</CardTitle>
              <CardDescription className="text-gray-400">Latest detected issues</CardDescription>
            </CardHeader>
            <CardContent>
              {incidents.length === 0 ? (
                <div className="text-center py-8">
                  <div className="text-gray-400 text-sm mb-2">No incidents detected</div>
                  <div className="text-gray-500 text-xs">Your infrastructure is running smoothly</div>
                </div>
              ) : (
                <div className="space-y-3">
                  {incidents.slice(0, 5).map((incident) => (
                    <div
                      key={incident.id}
                      className="p-3 bg-gray-900/50 rounded-lg border border-gray-700 hover:border-gray-600 transition-colors"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <div className="text-white text-sm font-medium">{incident.resource_name}</div>
                          <div className="text-gray-400 text-xs mt-1">{incident.description}</div>
                        </div>
                        <Badge className={getSeverityColor(incident.severity)} variant="outline">
                          {incident.severity || 'Unknown'}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-2 text-xs text-gray-500">
                        <span>{new Date(incident.timestamp).toLocaleString()}</span>
                        <span>•</span>
                        <span>{incident.status}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
              {incidents.length > 5 && (
                <Link href="/incidents">
                  <Button variant="outline" className="w-full mt-4 bg-gray-900 border-gray-700 text-white hover:bg-gray-800">
                    View All Incidents
                  </Button>
                </Link>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Resources Section */}
        <Card className="bg-gray-800/50 border-gray-700 mt-6">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-white">Resources</CardTitle>
                <CardDescription className="text-gray-400">
                  {project.total_resources} total resources
                </CardDescription>
              </div>
              <Link href={`/provision?project=${projectId}`}>
                <Button className="bg-blue-600 hover:bg-blue-700 text-white">
                  <Zap className="w-4 h-4 mr-2" />
                  Provision New
                </Button>
              </Link>
            </div>
          </CardHeader>
          <CardContent>
            {project.resources.length === 0 ? (
              <div className="text-center py-12">
                <Server className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-white mb-2">No resources yet</h3>
                <p className="text-gray-400 mb-6">Start by provisioning your first infrastructure resource</p>
                <Link href={`/provision?project=${projectId}`}>
                  <Button className="bg-blue-600 hover:bg-blue-700 text-white">
                    <Zap className="w-4 h-4 mr-2" />
                    Provision Resources
                  </Button>
                </Link>
              </div>
            ) : (
              <div className="space-y-3">
                {project.resources.map((resource: any, idx: number) => (
                  <div
                    key={idx}
                    className="p-4 bg-gray-900/50 rounded-lg border border-gray-700 hover:border-gray-600 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-white font-medium">{resource.name}</div>
                        <div className="text-gray-400 text-sm">{resource.type}</div>
                      </div>
                      <Badge variant="outline" className={getStatusColor(resource.status || "active")}>
                        {resource.status || "active"}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Metadata */}
        <Card className="bg-gray-800/50 border-gray-700 mt-6">
          <CardHeader>
            <CardTitle className="text-white">Project Information</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <div className="text-gray-400">Project ID</div>
                <div className="text-white font-mono">{project.project_id}</div>
              </div>
              <div>
                <div className="text-gray-400">User ID</div>
                <div className="text-white font-mono">{project.user_id}</div>
              </div>
              <div>
                <div className="text-gray-400">Created</div>
                <div className="text-white">{new Date(project.created_at).toLocaleString()}</div>
              </div>
              <div>
                <div className="text-gray-400">Last Updated</div>
                <div className="text-white">{new Date(project.updated_at).toLocaleString()}</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

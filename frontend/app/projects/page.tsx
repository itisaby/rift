"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { Plus, Settings, Trash2, Activity, DollarSign, Server, Cloud } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface CloudProvider {
  provider: string
  region?: string
}

interface Project {
  project_id: string
  name: string
  description?: string
  user_id: string
  cloud_providers: CloudProvider[]
  total_resources: number
  active_incidents: number
  total_cost: number
  status: string
  monitoring_enabled: boolean
  auto_remediation: boolean
  created_at: string
  tags: string[]
}

interface CreateProjectModalProps {
  apiUrl: string
  onClose: () => void
  onSuccess: () => void
}

function CreateProjectModal({ apiUrl, onClose, onSuccess }: CreateProjectModalProps) {
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    selectedProviders: ["digitalocean"] as string[],
    doToken: "",
    doRegion: "nyc3",
    awsAccessKey: "",
    awsSecretKey: "",
    awsRegion: "us-east-1",
    tags: ""
  })
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const toggleProvider = (provider: string) => {
    setFormData(prev => ({
      ...prev,
      selectedProviders: prev.selectedProviders.includes(provider)
        ? prev.selectedProviders.filter(p => p !== provider)
        : [...prev.selectedProviders, provider]
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setCreating(true)
    setError(null)

    try {
      // Build cloud providers array
      const cloudProviders = []
      
      if (formData.selectedProviders.includes("digitalocean")) {
        cloudProviders.push({
          provider: "digitalocean",
          credentials: {
            api_token: formData.doToken
          },
          region: formData.doRegion
        })
      }
      
      if (formData.selectedProviders.includes("aws")) {
        cloudProviders.push({
          provider: "aws",
          credentials: {
            access_key_id: formData.awsAccessKey,
            secret_access_key: formData.awsSecretKey
          },
          region: formData.awsRegion
        })
      }

      const requestBody = {
        name: formData.name,
        description: formData.description,
        user_id: "frontend-user-" + Date.now(),
        cloud_providers: cloudProviders,
        tags: formData.tags.split(",").map(t => t.trim()).filter(t => t)
      }

      const response = await fetch(`${apiUrl}/projects`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(requestBody)
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: "Unknown error" }))
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      console.log("✅ Project created:", data)
      onSuccess()
    } catch (err) {
      console.error("❌ Failed to create project:", err)
      setError(err instanceof Error ? err.message : "Failed to create project")
    } finally {
      setCreating(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <Card className="bg-gray-800 border-gray-700 w-full max-w-2xl">
        <CardHeader>
          <CardTitle className="text-white">Create New Project</CardTitle>
          <CardDescription className="text-gray-400">
            Set up a new infrastructure workspace
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="bg-red-900/50 border border-red-500 text-red-200 px-4 py-3 rounded">
                {error}
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Project Name *
              </label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full bg-gray-900 border border-gray-700 text-white rounded px-3 py-2 focus:border-blue-500 focus:outline-none"
                placeholder="Production Environment"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Description
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full bg-gray-900 border border-gray-700 text-white rounded px-3 py-2 focus:border-blue-500 focus:outline-none"
                placeholder="Main production infrastructure"
                rows={3}
              />
            </div>

            {/* Multi-Cloud Provider Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-3">
                Cloud Providers * <Badge className="ml-2 bg-blue-500">Multi-Cloud</Badge>
              </label>
              <div className="space-y-3">
                {/* DigitalOcean */}
                <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
                  <div className="flex items-center mb-3">
                    <input
                      type="checkbox"
                      id="provider-do"
                      checked={formData.selectedProviders.includes("digitalocean")}
                      onChange={() => toggleProvider("digitalocean")}
                      className="w-4 h-4 text-blue-600 rounded"
                    />
                    <label htmlFor="provider-do" className="ml-3 text-white font-medium cursor-pointer">
                      🌊 DigitalOcean
                    </label>
                  </div>
                  {formData.selectedProviders.includes("digitalocean") && (
                    <div className="ml-7 space-y-3">
                      <div>
                        <input
                          type="password"
                          required
                          value={formData.doToken}
                          onChange={(e) => setFormData({ ...formData, doToken: e.target.value })}
                          className="w-full bg-gray-800 border border-gray-600 text-white rounded px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                          placeholder="API Token: dop_v1_xxxxx..."
                        />
                      </div>
                      <div>
                        <select
                          required
                          value={formData.doRegion}
                          onChange={(e) => setFormData({ ...formData, doRegion: e.target.value })}
                          className="w-full bg-gray-800 border border-gray-600 text-white rounded px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                        >
                          <option value="nyc3">NYC3 (New York)</option>
                          <option value="nyc1">NYC1 (New York)</option>
                          <option value="sfo3">SFO3 (San Francisco)</option>
                          <option value="lon1">LON1 (London)</option>
                          <option value="fra1">FRA1 (Frankfurt)</option>
                          <option value="sgp1">SGP1 (Singapore)</option>
                        </select>
                      </div>
                    </div>
                  )}
                </div>

                {/* AWS */}
                <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
                  <div className="flex items-center mb-3">
                    <input
                      type="checkbox"
                      id="provider-aws"
                      checked={formData.selectedProviders.includes("aws")}
                      onChange={() => toggleProvider("aws")}
                      className="w-4 h-4 text-blue-600 rounded"
                    />
                    <label htmlFor="provider-aws" className="ml-3 text-white font-medium cursor-pointer">
                      ☁️ AWS
                    </label>
                    <Badge className="ml-2 bg-green-500 text-xs">Available</Badge>
                  </div>
                  {formData.selectedProviders.includes("aws") && (
                    <div className="ml-7 space-y-3">
                      <div>
                        <input
                          type="password"
                          required
                          value={formData.awsAccessKey}
                          onChange={(e) => setFormData({ ...formData, awsAccessKey: e.target.value })}
                          className="w-full bg-gray-800 border border-gray-600 text-white rounded px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                          placeholder="AWS Access Key ID"
                        />
                      </div>
                      <div>
                        <input
                          type="password"
                          required
                          value={formData.awsSecretKey}
                          onChange={(e) => setFormData({ ...formData, awsSecretKey: e.target.value })}
                          className="w-full bg-gray-800 border border-gray-600 text-white rounded px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                          placeholder="AWS Secret Access Key"
                        />
                      </div>
                      <div>
                        <select
                          required
                          value={formData.awsRegion}
                          onChange={(e) => setFormData({ ...formData, awsRegion: e.target.value })}
                          className="w-full bg-gray-800 border border-gray-600 text-white rounded px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                        >
                          <option value="us-east-1">us-east-1 (N. Virginia)</option>
                          <option value="us-west-2">us-west-2 (Oregon)</option>
                          <option value="eu-west-1">eu-west-1 (Ireland)</option>
                          <option value="ap-southeast-1">ap-southeast-1 (Singapore)</option>
                          <option value="ap-northeast-1">ap-northeast-1 (Tokyo)</option>
                        </select>
                      </div>
                    </div>
                  )}
                </div>
              </div>
              <p className="text-xs text-gray-500 mt-2">
                Select one or more cloud providers. You can provision resources across multiple clouds in a single project.
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Tags (comma-separated)
              </label>
              <input
                type="text"
                value={formData.tags}
                onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
                className="w-full bg-gray-900 border border-gray-700 text-white rounded px-3 py-2 focus:border-blue-500 focus:outline-none"
                placeholder="production, critical, web-app"
              />
            </div>

            <div className="flex justify-end gap-3 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={onClose}
                disabled={creating}
                className="bg-gray-700 border-gray-600 text-white hover:bg-gray-600"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={creating}
                className="bg-blue-600 hover:bg-blue-700 text-white"
              >
                {creating ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2"></div>
                    Creating...
                  </>
                ) : (
                  <>
                    <Plus className="w-4 h-4 mr-2" />
                    Create Project
                  </>
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [deletingProject, setDeletingProject] = useState<string | null>(null)

  useEffect(() => {
    fetchProjects()
  }, [])

  const fetchProjects = async () => {
    try {
      console.log("Fetching projects from:", `${API_URL}/projects`)
      const response = await fetch(`${API_URL}/projects`)

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      console.log("✅ Projects received:", data)
      setProjects(data)
      setLoading(false)
    } catch (error) {
      console.error("❌ Failed to fetch projects:", error)
      setLoading(false)
    }
  }

  const handleDeleteProject = async (projectId: string, projectName: string) => {
    if (!confirm(`Are you sure you want to delete project "${projectName}"? This action cannot be undone.`)) {
      return
    }

    setDeletingProject(projectId)
    try {
      const response = await fetch(`${API_URL}/projects/${projectId}`, {
        method: "DELETE"
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: "Unknown error" }))
        throw new Error(errorData.detail || `Failed to delete project`)
      }

      console.log("✅ Project deleted successfully")
      // Refresh projects list
      await fetchProjects()
    } catch (error) {
      console.error("❌ Failed to delete project:", error)
      alert(`Error deleting project: ${error instanceof Error ? error.message : 'Unknown error'}`)
    } finally {
      setDeletingProject(null)
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

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case "active":
        return "bg-green-500"
      case "paused":
        return "bg-yellow-500"
      case "archived":
        return "bg-gray-500"
      default:
        return "bg-gray-500"
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-center h-64">
            <div className="text-white text-xl">Loading projects...</div>
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
              <h1 className="text-4xl font-bold text-white mb-2">Projects</h1>
              <p className="text-gray-300">Manage your infrastructure workspaces</p>
            </div>
            <div className="flex gap-4">
              <Link href="/">
                <Button variant="outline" className="bg-gray-800 border-gray-700 text-white hover:bg-gray-700">
                  Dashboard
                </Button>
              </Link>
              <Button 
                className="bg-blue-600 hover:bg-blue-700 text-white"
                onClick={() => setShowCreateModal(true)}
              >
                <Plus className="w-4 h-4 mr-2" />
                New Project
              </Button>
            </div>
          </div>
        </div>

        {/* Projects Grid */}
        {projects.length === 0 ? (
          <Card className="bg-gray-800/50 border-gray-700">
            <CardContent className="p-12 text-center">
              <Cloud className="w-16 h-16 text-gray-500 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-white mb-2">No projects yet</h3>
              <p className="text-gray-400 mb-6">Create your first project to get started</p>
              <Button 
                className="bg-blue-600 hover:bg-blue-700 text-white"
                onClick={() => setShowCreateModal(true)}
              >
                <Plus className="w-4 h-4 mr-2" />
                Create Project
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {projects.map((project) => (
              <Card key={project.project_id} className="bg-gray-800/50 border-gray-700 hover:bg-gray-800/70 transition-all">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-white mb-2 flex items-center gap-2">
                        {project.name}
                        <div className={`w-2 h-2 rounded-full ${getStatusColor(project.status)}`} />
                      </CardTitle>
                      <CardDescription className="text-gray-400">
                        {project.description || "No description"}
                      </CardDescription>
                    </div>
                    <div className="flex gap-2">
                      <Link href={`/projects/${project.project_id}/settings`}>
                        <Button variant="ghost" size="sm" className="text-gray-400 hover:text-white">
                          <Settings className="w-4 h-4" />
                        </Button>
                      </Link>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-gray-400 hover:text-red-400"
                        onClick={() => handleDeleteProject(project.project_id, project.name)}
                        disabled={deletingProject === project.project_id}
                      >
                        {deletingProject === project.project_id ? (
                          <div className="w-4 h-4 border-2 border-gray-400/30 border-t-gray-400 rounded-full animate-spin" />
                        ) : (
                          <Trash2 className="w-4 h-4" />
                        )}
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  {/* Cloud Providers */}
                  <div className="mb-4">
                    <div className="text-sm text-gray-400 mb-2">Cloud Providers</div>
                    <div className="flex gap-2 flex-wrap">
                      {project.cloud_providers.map((cp, idx) => (
                        <Badge key={idx} variant="secondary" className="bg-gray-700 text-white">
                          {getProviderIcon(cp.provider)} {cp.provider}
                        </Badge>
                      ))}
                    </div>
                  </div>

                  {/* Stats */}
                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div className="bg-gray-900/50 rounded-lg p-3">
                      <div className="flex items-center gap-2 text-gray-400 text-sm mb-1">
                        <Server className="w-4 h-4" />
                        Resources
                      </div>
                      <div className="text-2xl font-bold text-white">{project.total_resources}</div>
                    </div>
                    <div className="bg-gray-900/50 rounded-lg p-3">
                      <div className="flex items-center gap-2 text-gray-400 text-sm mb-1">
                        <Activity className="w-4 h-4" />
                        Incidents
                      </div>
                      <div className="text-2xl font-bold text-white">{project.active_incidents}</div>
                    </div>
                  </div>

                  {/* Cost */}
                  <div className="bg-gray-900/50 rounded-lg p-3 mb-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 text-gray-400 text-sm">
                        <DollarSign className="w-4 h-4" />
                        Est. Monthly Cost
                      </div>
                      <div className="text-xl font-bold text-green-400">
                        ${project.total_cost.toFixed(2)}
                      </div>
                    </div>
                  </div>

                  {/* Features */}
                  <div className="flex gap-2 mb-4">
                    {project.monitoring_enabled && (
                      <Badge variant="secondary" className="bg-blue-900/50 text-blue-300">
                        Monitoring
                      </Badge>
                    )}
                    {project.auto_remediation && (
                      <Badge variant="secondary" className="bg-green-900/50 text-green-300">
                        Auto-fix
                      </Badge>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2">
                    <Link href={`/projects/${project.project_id}`} className="flex-1">
                      <Button className="w-full bg-blue-600 hover:bg-blue-700 text-white">
                        View Details
                      </Button>
                    </Link>
                    <Link href={`/projects/${project.project_id}/infrastructure`}>
                      <Button variant="outline" className="bg-gray-700 border-gray-600 text-white hover:bg-gray-600">
                        Visualize
                      </Button>
                    </Link>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Create Project Modal */}
        {showCreateModal && (
          <CreateProjectModal 
            apiUrl={API_URL}
            onClose={() => setShowCreateModal(false)}
            onSuccess={() => {
              setShowCreateModal(false)
              fetchProjects()
            }}
          />
        )}
      </div>
    </div>
  )
}

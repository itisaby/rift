"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import Link from "next/link"
import { ArrowLeft, Activity, Clock, AlertTriangle, CheckCircle2, Zap, TrendingUp } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { useWebSocket } from "@/lib/useWebSocket"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface Incident {
  id: string
  resource_name: string
  resource_type: string
  metric: string
  current_value: number
  threshold_value: number
  severity: string
  status: string
  description: string
  timestamp: string
  metadata?: Record<string, any>
}

interface Diagnosis {
  id: string
  root_cause: string
  root_cause_category: string
  confidence: number
  reasoning: string
  recommendations: string[]
  estimated_cost?: number
  estimated_duration?: number
  timestamp: string
}

interface RemediationResult {
  id: string
  status: string
  success: boolean
  action_taken: string
  duration: number
  verification_passed: boolean
  logs: string[]
  timestamp: string
}

interface IncidentDetail {
  incident: Incident
  diagnosis?: Diagnosis
  remediation?: RemediationResult
  has_diagnosis: boolean
  has_remediation: boolean
}

export default function IncidentDetailPage() {
  const params = useParams()
  const router = useRouter()
  const incident_id = params.incident_id as string

  const [data, setData] = useState<IncidentDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchIncidentDetail = async () => {
    try {
      const response = await fetch(`${API_URL}/incidents/${incident_id}`)

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result = await response.json()
      setData(result)
      setLoading(false)
    } catch (err) {
      console.error("Failed to fetch incident detail:", err)
      setError(err instanceof Error ? err.message : "Unknown error")
      setLoading(false)
    }
  }

  // WebSocket for real-time updates
  const WS_URL = API_URL.replace('http://', 'ws://').replace('https://', 'wss://')
  const { lastMessage } = useWebSocket(`${WS_URL}/ws/events`, {
    onMessage: (message) => {
      // Update when diagnosis completes for this incident
      if (message.type === 'diagnosis_completed' && message.incident_id === incident_id) {
        console.log('Diagnosis completed, refreshing...', message)
        fetchIncidentDetail()
      }
      
      // Update when remediation completes for this incident
      if (message.type === 'remediation_completed' && message.incident_id === incident_id) {
        console.log('Remediation completed, refreshing...', message)
        fetchIncidentDetail()
      }
      
      // Update when incident is detected (initial creation)
      if (message.type === 'incident_detected' && message.incident?.id === incident_id) {
        console.log('Incident updated, refreshing...', message)
        fetchIncidentDetail()
      }
    }
  })

  useEffect(() => {
    fetchIncidentDetail()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [incident_id])

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical': return 'bg-red-500'
      case 'high': return 'bg-orange-500'
      case 'medium': return 'bg-yellow-500'
      case 'low': return 'bg-blue-500'
      default: return 'bg-gray-500'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'resolved': return 'bg-green-500'
      case 'remediating': return 'bg-yellow-500'
      case 'detected': return 'bg-red-500'
      case 'diagnosing': return 'bg-blue-500'
      case 'diagnosed': return 'bg-purple-500'
      default: return 'bg-gray-500'
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 p-8">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center justify-center h-64">
            <div className="text-white text-xl">Loading incident details...</div>
          </div>
        </div>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 p-8">
        <div className="max-w-6xl mx-auto">
          <Card className="bg-gray-800/50 border-gray-700">
            <CardContent className="p-12 text-center">
              <AlertTriangle className="w-16 h-16 text-red-500 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-white mb-2">Error Loading Incident</h3>
              <p className="text-gray-400 mb-6">{error || "Incident not found"}</p>
              <Link href="/incidents">
                <Button className="bg-blue-600 hover:bg-blue-700 text-white">
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Back to Incidents
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  const { incident, diagnosis, remediation, has_diagnosis, has_remediation } = data

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <Link href="/incidents">
            <Button variant="outline" className="bg-gray-800 border-gray-700 text-white hover:bg-gray-700 mb-4">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Incidents
            </Button>
          </Link>

          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-4xl font-bold text-white mb-2">Incident Details</h1>
              <p className="text-gray-300">ID: {incident.id}</p>
            </div>
            <div className="flex gap-2">
              <Badge className={`${getSeverityColor(incident.severity)} text-white`}>
                {incident.severity}
              </Badge>
              <Badge className={`${getStatusColor(incident.status)} text-white`}>
                {incident.status}
              </Badge>
            </div>
          </div>
        </div>

        {/* Incident Overview */}
        <Card className="bg-gray-800/50 border-gray-700 mb-6">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Activity className="w-5 h-5" />
              Incident Overview
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-sm text-gray-400 mb-1">Resource Name</div>
                <div className="text-white font-semibold">{incident.resource_name}</div>
              </div>
              <div>
                <div className="text-sm text-gray-400 mb-1">Resource Type</div>
                <div className="text-white font-semibold">{incident.resource_type}</div>
              </div>
              <div>
                <div className="text-sm text-gray-400 mb-1">Metric</div>
                <div className="text-white font-semibold">{incident.metric}</div>
              </div>
              <div>
                <div className="text-sm text-gray-400 mb-1">Detected At</div>
                <div className="text-white font-semibold">
                  {new Date(incident.timestamp).toLocaleString()}
                </div>
              </div>
            </div>

            <div className="bg-gray-900/50 rounded-lg p-4">
              <div className="text-sm text-gray-400 mb-2">Description</div>
              <div className="text-white">{incident.description}</div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-900/50 rounded-lg p-4">
                <div className="text-sm text-gray-400 mb-1">Current Value</div>
                <div className="text-2xl font-bold text-red-400">{incident.current_value.toFixed(2)}</div>
              </div>
              <div className="bg-gray-900/50 rounded-lg p-4">
                <div className="text-sm text-gray-400 mb-1">Threshold Value</div>
                <div className="text-2xl font-bold text-yellow-400">{incident.threshold_value.toFixed(2)}</div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Diagnosis */}
        {has_diagnosis && diagnosis ? (
          <Card className="bg-gray-800/50 border-gray-700 mb-6">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <TrendingUp className="w-5 h-5" />
                Diagnosis
              </CardTitle>
              <CardDescription className="text-gray-400">
                AI-powered root cause analysis
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="bg-gray-900/50 rounded-lg p-4">
                <div className="text-sm text-gray-400 mb-2">Root Cause</div>
                <div className="text-white font-semibold text-lg">{diagnosis.root_cause}</div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="bg-gray-900/50 rounded-lg p-4">
                  <div className="text-sm text-gray-400 mb-1">Category</div>
                  <div className="text-white font-semibold">{diagnosis.root_cause_category}</div>
                </div>
                <div className="bg-gray-900/50 rounded-lg p-4">
                  <div className="text-sm text-gray-400 mb-1">Confidence</div>
                  <div className="text-white font-semibold">
                    {(diagnosis.confidence * 100).toFixed(0)}%
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2 mt-2">
                    <div
                      className="bg-green-500 h-2 rounded-full"
                      style={{ width: `${diagnosis.confidence * 100}%` }}
                    />
                  </div>
                </div>
              </div>

              <div className="bg-gray-900/50 rounded-lg p-4">
                <div className="text-sm text-gray-400 mb-2">Reasoning</div>
                <div className="text-white">{diagnosis.reasoning}</div>
              </div>

              <div className="bg-gray-900/50 rounded-lg p-4">
                <div className="text-sm text-gray-400 mb-2">Recommendations</div>
                <ul className="list-disc list-inside space-y-1">
                  {diagnosis.recommendations.map((rec, idx) => (
                    <li key={idx} className="text-white">{rec}</li>
                  ))}
                </ul>
              </div>

              {(diagnosis.estimated_cost || diagnosis.estimated_duration) && (
                <div className="grid grid-cols-2 gap-4">
                  {diagnosis.estimated_cost && (
                    <div className="bg-gray-900/50 rounded-lg p-4">
                      <div className="text-sm text-gray-400 mb-1">Estimated Cost</div>
                      <div className="text-white font-semibold">${diagnosis.estimated_cost.toFixed(2)}</div>
                    </div>
                  )}
                  {diagnosis.estimated_duration && (
                    <div className="bg-gray-900/50 rounded-lg p-4">
                      <div className="text-sm text-gray-400 mb-1">Estimated Duration</div>
                      <div className="text-white font-semibold">
                        {Math.round(diagnosis.estimated_duration / 60)} minutes
                      </div>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        ) : (
          <Card className="bg-gray-800/50 border-gray-700 mb-6">
            <CardContent className="p-8 text-center">
              <Clock className="w-12 h-12 text-gray-500 mx-auto mb-3" />
              <p className="text-gray-400">No diagnosis available yet</p>
            </CardContent>
          </Card>
        )}

        {/* Remediation */}
        {has_remediation && remediation ? (
          <Card className="bg-gray-800/50 border-gray-700">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Zap className="w-5 h-5" />
                Remediation
              </CardTitle>
              <CardDescription className="text-gray-400">
                Automated fix execution
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-gray-900/50 rounded-lg p-4">
                  <div className="text-sm text-gray-400 mb-1">Status</div>
                  <div className="flex items-center gap-2">
                    {remediation.success ? (
                      <CheckCircle2 className="w-5 h-5 text-green-500" />
                    ) : (
                      <AlertTriangle className="w-5 h-5 text-red-500" />
                    )}
                    <span className="text-white font-semibold">{remediation.status}</span>
                  </div>
                </div>
                <div className="bg-gray-900/50 rounded-lg p-4">
                  <div className="text-sm text-gray-400 mb-1">Duration</div>
                  <div className="text-white font-semibold">{remediation.duration}s</div>
                </div>
                <div className="bg-gray-900/50 rounded-lg p-4">
                  <div className="text-sm text-gray-400 mb-1">Verification</div>
                  <div className="text-white font-semibold">
                    {remediation.verification_passed ? "Passed" : "Failed"}
                  </div>
                </div>
              </div>

              <div className="bg-gray-900/50 rounded-lg p-4">
                <div className="text-sm text-gray-400 mb-2">Action Taken</div>
                <div className="text-white">{remediation.action_taken}</div>
              </div>

              {remediation.logs && remediation.logs.length > 0 && (
                <div className="bg-gray-900/50 rounded-lg p-4">
                  <div className="text-sm text-gray-400 mb-2">Execution Logs</div>
                  <div className="bg-black/50 rounded p-3 font-mono text-xs text-green-400 max-h-64 overflow-y-auto">
                    {remediation.logs.map((log, idx) => (
                      <div key={idx}>{log}</div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        ) : has_diagnosis ? (
          <Card className="bg-gray-800/50 border-gray-700">
            <CardContent className="p-8 text-center">
              <Clock className="w-12 h-12 text-gray-500 mx-auto mb-3" />
              <p className="text-gray-400">No remediation performed yet</p>
            </CardContent>
          </Card>
        ) : null}
      </div>
    </div>
  )
}

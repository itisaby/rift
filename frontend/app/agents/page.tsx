"use client"

import { useState } from "react"
import Link from "next/link"
import { ArrowLeft, Activity, Search, Wrench, Play, CheckCircle2, XCircle, Clock, AlertTriangle } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export default function AgentsTestPage() {
  const [monitoring, setMonitoring] = useState(false)
  const [diagnosing, setDiagnosing] = useState(false)
  const [remediating, setRemediating] = useState(false)

  const [monitorResult, setMonitorResult] = useState<any>(null)
  const [diagnosisResult, setDiagnosisResult] = useState<any>(null)
  const [remediationResult, setRemediationResult] = useState<any>(null)

  const [selectedIncident, setSelectedIncident] = useState<string | null>(null)

  // Test Monitor Agent - Detect incidents
  const testMonitorAgent = async () => {
    setMonitoring(true)
    setMonitorResult(null)

    try {
      console.log("Testing Monitor Agent...")
      const response = await fetch(`${API_URL}/incidents/detect`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      console.log("✅ Monitor Agent response:", data)
      setMonitorResult(data)

      // Auto-select first incident for diagnosis
      if (data.incidents && data.incidents.length > 0) {
        setSelectedIncident(data.incidents[0].id)
      }
    } catch (error) {
      console.error("❌ Monitor Agent failed:", error)
      setMonitorResult({ error: error instanceof Error ? error.message : 'Unknown error' })
    } finally {
      setMonitoring(false)
    }
  }

  // Test Diagnostic Agent - Diagnose an incident
  const testDiagnosticAgent = async () => {
    if (!selectedIncident) {
      alert("Please run Monitor Agent first to detect incidents, or select an incident ID")
      return
    }

    setDiagnosing(true)
    setDiagnosisResult(null)

    try {
      console.log("Testing Diagnostic Agent for incident:", selectedIncident)
      const response = await fetch(`${API_URL}/incidents/diagnose`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          incident_id: selectedIncident
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      console.log("✅ Diagnostic Agent response:", data)
      setDiagnosisResult(data)
    } catch (error) {
      console.error("❌ Diagnostic Agent failed:", error)
      setDiagnosisResult({ error: error instanceof Error ? error.message : 'Unknown error' })
    } finally {
      setDiagnosing(false)
    }
  }

  // Test Remediation Agent - Fix the issue
  const testRemediationAgent = async (autoApprove: boolean = false) => {
    if (!selectedIncident) {
      alert("Please run Monitor and Diagnostic agents first")
      return
    }

    if (!autoApprove && !confirm("Are you sure you want to execute remediation? This will make actual infrastructure changes!")) {
      return
    }

    setRemediating(true)
    setRemediationResult(null)

    try {
      console.log("Testing Remediation Agent for incident:", selectedIncident)
      const response = await fetch(`${API_URL}/incidents/remediate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          incident_id: selectedIncident,
          auto_approve: autoApprove
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      console.log("✅ Remediation Agent response:", data)
      setRemediationResult(data)
    } catch (error) {
      console.error("❌ Remediation Agent failed:", error)
      setRemediationResult({ error: error instanceof Error ? error.message : 'Unknown error' })
    } finally {
      setRemediating(false)
    }
  }

  const getStatusIcon = (result: any) => {
    if (!result) return <Clock className="w-5 h-5 text-gray-400" />
    if (result.error) return <XCircle className="w-5 h-5 text-red-500" />
    return <CheckCircle2 className="w-5 h-5 text-green-500" />
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <Link href="/">
            <Button variant="outline" className="bg-gray-800 border-gray-700 text-white hover:bg-gray-700 mb-4">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Dashboard
            </Button>
          </Link>

          <h1 className="text-4xl font-bold text-white mb-2">Agent Testing</h1>
          <p className="text-gray-300">Test Monitor, Diagnostic, and Remediation agents end-to-end</p>
        </div>

        {/* Incident Selection */}
        <Card className="bg-gray-800/50 border-gray-700 mb-6">
          <CardHeader>
            <CardTitle className="text-white">Selected Incident</CardTitle>
            <CardDescription className="text-gray-400">
              Run Monitor Agent first, or enter an incident ID manually
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex gap-4">
              <input
                type="text"
                value={selectedIncident || ""}
                onChange={(e) => setSelectedIncident(e.target.value)}
                placeholder="Incident ID (auto-filled after monitoring)"
                className="flex-1 bg-gray-900 border border-gray-700 text-white rounded px-3 py-2 focus:border-blue-500 focus:outline-none"
              />
              {selectedIncident && (
                <Badge className="bg-blue-600 text-white px-4 py-2">
                  ID: {selectedIncident.substring(0, 8)}...
                </Badge>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Agent Testing Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          {/* Monitor Agent */}
          <Card className="bg-gray-800/50 border-gray-700">
            <CardHeader>
              <div className="flex items-center gap-2">
                <Activity className="w-5 h-5 text-cyan-400" />
                <CardTitle className="text-white">Monitor Agent</CardTitle>
              </div>
              <CardDescription className="text-gray-400">
                Detect infrastructure incidents
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button
                onClick={testMonitorAgent}
                disabled={monitoring}
                className="w-full bg-cyan-600 hover:bg-cyan-700 text-white"
              >
                {monitoring ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2"></div>
                    Scanning...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 mr-2" />
                    Run Detection
                  </>
                )}
              </Button>

              {monitorResult && (
                <div className="mt-4 p-3 bg-gray-900/50 rounded border border-gray-700">
                  <div className="flex items-center gap-2 mb-2">
                    {getStatusIcon(monitorResult)}
                    <span className="text-sm font-semibold text-white">
                      {monitorResult.error ? 'Failed' : 'Success'}
                    </span>
                  </div>
                  {monitorResult.error ? (
                    <p className="text-xs text-red-400">{monitorResult.error}</p>
                  ) : (
                    <>
                      <p className="text-xs text-gray-400 mb-2">
                        Found {monitorResult.incidents?.length || 0} incident(s)
                      </p>
                      {monitorResult.incidents?.slice(0, 2).map((inc: any, idx: number) => (
                        <div key={idx} className="text-xs text-cyan-300 mb-1">
                          • {inc.resource_name} - {inc.severity}
                        </div>
                      ))}
                    </>
                  )}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Diagnostic Agent */}
          <Card className="bg-gray-800/50 border-gray-700">
            <CardHeader>
              <div className="flex items-center gap-2">
                <Search className="w-5 h-5 text-purple-400" />
                <CardTitle className="text-white">Diagnostic Agent</CardTitle>
              </div>
              <CardDescription className="text-gray-400">
                Analyze root cause with AI
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button
                onClick={testDiagnosticAgent}
                disabled={diagnosing || !selectedIncident}
                className="w-full bg-purple-600 hover:bg-purple-700 text-white"
              >
                {diagnosing ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2"></div>
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 mr-2" />
                    Run Diagnosis
                  </>
                )}
              </Button>

              {diagnosisResult && (
                <div className="mt-4 p-3 bg-gray-900/50 rounded border border-gray-700">
                  <div className="flex items-center gap-2 mb-2">
                    {getStatusIcon(diagnosisResult)}
                    <span className="text-sm font-semibold text-white">
                      {diagnosisResult.error ? 'Failed' : 'Diagnosed'}
                    </span>
                  </div>
                  {diagnosisResult.error ? (
                    <p className="text-xs text-red-400">{diagnosisResult.error}</p>
                  ) : (
                    <>
                      <p className="text-xs text-gray-400 mb-1">
                        Confidence: {(diagnosisResult.diagnosis?.confidence * 100).toFixed(0)}%
                      </p>
                      <p className="text-xs text-purple-300">
                        {diagnosisResult.diagnosis?.root_cause}
                      </p>
                    </>
                  )}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Remediation Agent */}
          <Card className="bg-gray-800/50 border-gray-700">
            <CardHeader>
              <div className="flex items-center gap-2">
                <Wrench className="w-5 h-5 text-green-400" />
                <CardTitle className="text-white">Remediation Agent</CardTitle>
              </div>
              <CardDescription className="text-gray-400">
                Automatically fix the issue
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <Button
                  onClick={() => testRemediationAgent(false)}
                  disabled={remediating || !selectedIncident}
                  className="w-full bg-green-600 hover:bg-green-700 text-white"
                >
                  {remediating ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2"></div>
                      Fixing...
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4 mr-2" />
                      Manual Approve
                    </>
                  )}
                </Button>

                <Button
                  onClick={() => testRemediationAgent(true)}
                  disabled={remediating || !selectedIncident}
                  variant="outline"
                  className="w-full bg-gray-700 border-gray-600 text-white hover:bg-gray-600"
                >
                  <AlertTriangle className="w-4 h-4 mr-2" />
                  Auto-Approve
                </Button>
              </div>

              {remediationResult && (
                <div className="mt-4 p-3 bg-gray-900/50 rounded border border-gray-700">
                  <div className="flex items-center gap-2 mb-2">
                    {getStatusIcon(remediationResult)}
                    <span className="text-sm font-semibold text-white">
                      {remediationResult.error ? 'Failed' : remediationResult.result?.success ? 'Fixed' : 'Pending'}
                    </span>
                  </div>
                  {remediationResult.error ? (
                    <p className="text-xs text-red-400">{remediationResult.error}</p>
                  ) : (
                    <>
                      <p className="text-xs text-gray-400 mb-1">
                        Status: {remediationResult.result?.status}
                      </p>
                      <p className="text-xs text-green-300">
                        {remediationResult.result?.action_taken}
                      </p>
                    </>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Workflow Steps */}
        <Card className="bg-gray-800/50 border-gray-700">
          <CardHeader>
            <CardTitle className="text-white">Testing Workflow</CardTitle>
            <CardDescription className="text-gray-400">
              Follow these steps to test the complete agent pipeline
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-cyan-600 flex items-center justify-center text-white font-bold">
                  1
                </div>
                <div>
                  <h3 className="text-white font-semibold mb-1">Run Monitor Agent</h3>
                  <p className="text-sm text-gray-400">
                    Click "Run Detection" to scan your infrastructure for issues. The agent will check CPU, memory, and disk usage across all resources.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-purple-600 flex items-center justify-center text-white font-bold">
                  2
                </div>
                <div>
                  <h3 className="text-white font-semibold mb-1">Run Diagnostic Agent</h3>
                  <p className="text-sm text-gray-400">
                    After detection, the incident ID will be auto-filled. Click "Run Diagnosis" to get AI-powered root cause analysis with recommendations.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-green-600 flex items-center justify-center text-white font-bold">
                  3
                </div>
                <div>
                  <h3 className="text-white font-semibold mb-1">Run Remediation Agent</h3>
                  <p className="text-sm text-gray-400">
                    Choose "Manual Approve" to review the fix first, or "Auto-Approve" to let the agent fix it automatically.
                    <span className="text-yellow-400 font-semibold"> Warning: This will make actual infrastructure changes!</span>
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Alternative: Use Demo Data */}
        <Card className="bg-gray-800/50 border-gray-700 mt-6">
          <CardHeader>
            <CardTitle className="text-white">Quick Test with Demo Data</CardTitle>
            <CardDescription className="text-gray-400">
              Don't have real incidents? Use the demo failure injector
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex gap-4">
              <Link href="/" className="flex-1">
                <Button className="w-full bg-red-600 hover:bg-red-700 text-white">
                  <Activity className="w-4 h-4 mr-2" />
                  Go to Dashboard & Inject Demo Failure
                </Button>
              </Link>
              <Link href="/incidents" className="flex-1">
                <Button variant="outline" className="w-full bg-gray-700 border-gray-600 text-white hover:bg-gray-600">
                  View All Incidents
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

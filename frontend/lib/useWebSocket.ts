import { useEffect, useRef, useState } from 'react'

interface WebSocketMessage {
  type: string
  [key: string]: any
}

interface UseWebSocketOptions {
  onMessage?: (message: WebSocketMessage) => void
  onConnect?: () => void
  onDisconnect?: () => void
  onError?: (error: Event) => void
  reconnectInterval?: number
  maxReconnectAttempts?: number
}

export function useWebSocket(url: string, options: UseWebSocketOptions = {}) {
  const {
    onMessage,
    onConnect,
    onDisconnect,
    onError,
    reconnectInterval = 5000,
    maxReconnectAttempts = 5
  } = options

  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectAttemptsRef = useRef(0)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>()

  const connect = () => {
    try {
      // Validate WebSocket URL
      if (!url || !url.startsWith('ws://') && !url.startsWith('wss://')) {
        console.error('Invalid WebSocket URL:', url)
        return
      }

      console.log('🔌 Attempting WebSocket connection to:', url)
      const ws = new WebSocket(url)

      ws.onopen = () => {
        console.log('✅ WebSocket connected successfully')
        setIsConnected(true)
        reconnectAttemptsRef.current = 0
        onConnect?.()
      }

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data) as WebSocketMessage
          console.log('📨 WebSocket message:', message.type)
          setLastMessage(message)
          onMessage?.(message)
        } catch (error) {
          console.error('❌ Failed to parse WebSocket message:', error)
        }
      }

      ws.onerror = (error) => {
        console.error('❌ WebSocket connection error - this is normal if backend is not running')
        // Don't call onError to avoid spamming console
        // The connection will retry automatically
      }

      ws.onclose = (event) => {
        console.log('⚠️ WebSocket disconnected:', event.code, event.reason)
        setIsConnected(false)
        onDisconnect?.()

        // Attempt to reconnect
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++
          console.log(`🔄 Reconnecting... Attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts}`)
          reconnectTimeoutRef.current = setTimeout(connect, reconnectInterval)
        } else {
          console.log('⛔ Max reconnection attempts reached. Falling back to polling.')
        }
      }

      wsRef.current = ws
    } catch (error) {
      console.error('❌ Failed to create WebSocket connection:', error)
    }
  }

  useEffect(() => {
    connect()

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [url])

  const sendMessage = (message: WebSocketMessage) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket is not connected')
    }
  }

  return {
    isConnected,
    lastMessage,
    sendMessage
  }
}

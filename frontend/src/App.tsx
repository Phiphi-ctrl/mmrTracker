import { useEffect, useState } from 'react'
import './App.css'

const LOBBY_REFRESH_MS = 3000

type Rating = {
  mmr: number | null
  rank: string | null
  division: string | null
  matches_played: number | null
}

type Player = {
  name: string
  platform: string | null
  ratings: Record<string, Rating>
  error: string | null
  is_trackable: boolean
}

type Team = {
  team_num: number
  name: string
  players: Player[]
}

type LobbyPayload = {
  mode: string
  teams: Record<string, Team>
}

function App() {
  const [lobby, setLobby] = useState<LobbyPayload | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

  useEffect(() => {
    let isActive = true
    let controller: AbortController | null = null

    async function loadLobby(isInitialLoad = false) {
      controller?.abort()
      controller = new AbortController()

      if (!isInitialLoad) {
        setIsRefreshing(true)
      }

      try {
        const response = await fetch('/api/lobby/current', {
          signal: controller.signal,
        })

        if (!response.ok) {
          throw new Error(`API returned ${response.status}`)
        }

        const payload = await response.json()

        if (!isActive) {
          return
        }

        setLobby(payload)
        setError(null)
        setLastUpdated(new Date())
      } catch (caught) {
        if (!isActive || (caught instanceof DOMException && caught.name === 'AbortError')) {
          return
        }

        setError(caught instanceof Error ? caught.message : 'Unknown API error')
      } finally {
        if (isActive) {
          setIsLoading(false)
          setIsRefreshing(false)
        }
      }
    }

    loadLobby(true)
    const intervalId = window.setInterval(() => loadLobby(), LOBBY_REFRESH_MS)

    return () => {
      isActive = false
      controller?.abort()
      window.clearInterval(intervalId)
    }
  }, [])

  return (
    <main className="app-shell">
      <header className="top-bar">
        <div>
          <p className="eyebrow">Rocket League MMR Tracker</p>
          <h1>Lobby Overview</h1>
        </div>
        <div className="header-status">
          <div className="mode-pill">{lobby?.mode ?? 'loading'}</div>
          <span className="refresh-state">
            {isRefreshing ? 'Refreshing...' : formatLastUpdated(lastUpdated)}
          </span>
        </div>
      </header>

      {isLoading && <p className="status">Loading lobby data...</p>}
      {error && <p className="status error">Backend unavailable: {error}</p>}

      {lobby && (
        <section className="teams-grid">
          {Object.entries(lobby.teams).map(([teamKey, team]) => (
            <article className="team-panel" data-team={team.team_num} key={teamKey}>
              <header className="team-header">
                <h2>{team.name}</h2>
                <span>{team.players.length} players</span>
              </header>

              <div className="player-list">
                {team.players.map((player) => (
                  <section className="player-row" key={player.name}>
                    <div className="player-meta">
                      <h3>{player.name}</h3>
                      <span>{player.platform ?? 'unknown'}</span>
                    </div>

                    {player.error && <p className="player-error">{player.error}</p>}

                    <div className="ratings-grid">
                      {Object.entries(player.ratings).map(([mode, rating]) => (
                        <div className="rating-cell" key={mode}>
                          <span className="playlist">{mode}</span>
                          <strong>{rating.mmr ?? 'N/A'}</strong>
                          <span>{rating.rank ?? 'Unranked'}</span>
                          <span>{rating.division ?? ''}</span>
                        </div>
                      ))}
                    </div>
                  </section>
                ))}
              </div>
            </article>
          ))}
        </section>
      )}
    </main>
  )
}

function formatLastUpdated(lastUpdated: Date | null) {
  if (lastUpdated === null) {
    return 'Waiting for data'
  }

  return `Updated ${lastUpdated.toLocaleTimeString()}`
}

export default App

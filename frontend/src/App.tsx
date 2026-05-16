import { useEffect, useMemo, useRef, useState } from 'react'
import bronze1Icon from './assets/bronze1.png'
import bronze2Icon from './assets/bronze2.png'
import bronze3Icon from './assets/bronze3.png'
import champ1Icon from './assets/champ1.png'
import champ2Icon from './assets/champ2.png'
import champ3Icon from './assets/champ3.png'
import diamond1Icon from './assets/dia1.png'
import diamond2Icon from './assets/dia2.png'
import diamond3Icon from './assets/dia3.png'
import gc1Icon from './assets/grandchamp1.png'
import gc2Icon from './assets/grandchamp2.png'
import gc3Icon from './assets/grandchamp3.png'
import gold1Icon from './assets/gold1.png'
import gold2Icon from './assets/gold2.png'
import gold3Icon from './assets/gold3.png'
import plat1Icon from './assets/plat1.png'
import plat2Icon from './assets/plat2.png'
import plat3Icon from './assets/plat3.png'
import silver1Icon from './assets/silver1.png'
import silver2Icon from './assets/silver2.png'
import silver3Icon from './assets/silver3.png'
import sslIcon from './assets/ssl.png'
import unrankedIcon from './assets/unranked.png'
import './App.css'

const LOBBY_REFRESH_MS = 3000
const MATCH_STABLE_MS = 60_000
const MAX_MATCH_HISTORY = 18
const HIDDEN_TRENDS_STORAGE_KEY = 'mmr-tracker-hidden-trends'
const MATCH_HISTORY_STORAGE_KEY = 'mmr-tracker-match-history'
const PLAYLIST_ORDER = ['1v1', '2v2', '3v3', '4v4']
const SAVEABLE_MATCH_MODES = new Set(PLAYLIST_ORDER)

const RANK_ICONS: Record<string, string> = {
  bronze1: bronze1Icon,
  bronze2: bronze2Icon,
  bronze3: bronze3Icon,
  silver1: silver1Icon,
  silver2: silver2Icon,
  silver3: silver3Icon,
  gold1: gold1Icon,
  gold2: gold2Icon,
  gold3: gold3Icon,
  platinum1: plat1Icon,
  platinum2: plat2Icon,
  platinum3: plat3Icon,
  diamond1: diamond1Icon,
  diamond2: diamond2Icon,
  diamond3: diamond3Icon,
  champion1: champ1Icon,
  champion2: champ2Icon,
  champion3: champ3Icon,
  grandchampion1: gc1Icon,
  grandchampion2: gc2Icon,
  grandchampion3: gc3Icon,
  supersoniclegend: sslIcon,
}

type Rating = {
  mmr: number | null
  rank: string | null
  division: string | null
  matches_played: number | null
}

type Player = {
  name: string
  primary_id?: string
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

type ChangeState = {
  changedTeams: Set<number>
  isModeChanged: boolean
  newPlayerKeys: Set<string>
}

type MatchPlayerSnapshot = {
  division: string | null
  mmr: number | null
  name: string
  platform: string | null
  rank: string | null
  team_num: number
}

type MatchTeamSnapshot = {
  name: string
  players: MatchPlayerSnapshot[]
  team_num: number
}

type MatchSnapshot = {
  id: string
  mode: string
  saved_at: string
  signature: string
  teams: MatchTeamSnapshot[]
}

type MmrTrendPoint = {
  mode: string
  mmr: number
  saved_at: string
}

type MmrTrendSeries = {
  id: string
  mode: string
  name: string
  platform: string | null
  points: MmrTrendPoint[]
}

const EMPTY_CHANGE_STATE: ChangeState = {
  changedTeams: new Set(),
  isModeChanged: false,
  newPlayerKeys: new Set(),
}

function App() {
  const [lobby, setLobby] = useState<LobbyPayload | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
  const [changeState, setChangeState] = useState<ChangeState>(EMPTY_CHANGE_STATE)
  const [hiddenTrendIds, setHiddenTrendIds] = useState<Set<string>>(loadHiddenTrendIds)
  const [matchHistory, setMatchHistory] = useState<MatchSnapshot[]>(loadMatchHistory)
  const lastSavedMatchSignatureRef = useRef<string | null>(matchHistory[0]?.signature ?? null)
  const pendingMatchSignatureRef = useRef<string | null>(null)
  const previousPlayerKeysRef = useRef<Set<string>>(new Set())
  const previousTeamSizesRef = useRef<Map<number, number>>(new Map())
  const previousModeRef = useRef<string | null>(null)
  const stableLobbyTimerRef = useRef<number | null>(null)

  useEffect(() => {
    let isActive = true
    let controller: AbortController | null = null

    function scheduleMatchSnapshot(payload: LobbyPayload, sortedTeams: [string, Team][]) {
      if (!SAVEABLE_MATCH_MODES.has(payload.mode)) {
        pendingMatchSignatureRef.current = null

        if (stableLobbyTimerRef.current !== null) {
          window.clearTimeout(stableLobbyTimerRef.current)
          stableLobbyTimerRef.current = null
        }

        return
      }

      const signature = getLobbySignature(payload, sortedTeams)

      if (signature === pendingMatchSignatureRef.current) {
        return
      }

      if (stableLobbyTimerRef.current !== null) {
        window.clearTimeout(stableLobbyTimerRef.current)
      }

      pendingMatchSignatureRef.current = signature
      stableLobbyTimerRef.current = window.setTimeout(() => {
        if (lastSavedMatchSignatureRef.current === signature) {
          return
        }

        const snapshot = createMatchSnapshot(payload, sortedTeams, signature)
        lastSavedMatchSignatureRef.current = signature

        setMatchHistory((currentHistory) => {
          const nextHistory = [snapshot, ...currentHistory]
            .filter((match, index, matches) => {
              return matches.findIndex((candidate) => candidate.signature === match.signature) === index
            })
            .slice(0, MAX_MATCH_HISTORY)

          saveMatchHistory(nextHistory)
          return nextHistory
        })
      }, MATCH_STABLE_MS)
    }

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

        const sortedTeams = getSortedTeams(payload)
        const nextChangeState = getLobbyChangeState(
          payload,
          sortedTeams,
          previousPlayerKeysRef.current,
          previousTeamSizesRef.current,
          previousModeRef.current,
        )

        setLobby(payload)
        setChangeState(nextChangeState)
        setError(null)
        setLastUpdated(new Date())
        previousPlayerKeysRef.current = new Set(
          sortedTeams.flatMap(([, team]) => team.players.map((player) => getPlayerKey(team, player))),
        )
        previousTeamSizesRef.current = new Map(
          sortedTeams.map(([, team]) => [team.team_num, team.players.length]),
        )
        previousModeRef.current = payload.mode
        scheduleMatchSnapshot(payload, sortedTeams)
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
      if (stableLobbyTimerRef.current !== null) {
        window.clearTimeout(stableLobbyTimerRef.current)
      }
    }
  }, [])

  const teams = useMemo(() => {
    if (!lobby) {
      return []
    }

    return getSortedTeams(lobby)
  }, [lobby])
  const mmrTrendSeries = useMemo(() => getRecurringPlayerMmrSeries(matchHistory), [matchHistory])
  const visibleMmrTrendSeries = useMemo(
    () => mmrTrendSeries.filter((series) => !hiddenTrendIds.has(series.id)),
    [hiddenTrendIds, mmrTrendSeries],
  )

  return (
    <main className="app-shell">
      <header className="top-bar">
        <div>
          <p className="eyebrow">Rocket League MMR Tracker</p>
          <h1>Lobby Overview</h1>
        </div>
        <div className="header-status">
          <div className="mode-pill" data-mode-changed={changeState.isModeChanged}>
            {lobby?.mode ?? 'loading'}
          </div>
          <span className="refresh-state" data-refreshing={isRefreshing}>
            {isRefreshing ? 'Refreshing...' : formatLastUpdated(lastUpdated)}
          </span>
        </div>
      </header>

      {isLoading && <p className="status">Loading lobby data...</p>}
      {error && <p className="status error">Backend unavailable: {error}</p>}

      {lobby && (
        <>
          <section className="compact-board" aria-label="Compact lobby overview">
            {teams.map(([teamKey, team]) => (
              <article
                className="compact-team"
                data-roster-changed={changeState.changedTeams.has(team.team_num)}
                data-team={team.team_num}
                key={teamKey}
              >
                <header className="compact-team-header">
                  <h2>{shortTeamName(team)}</h2>
                  <span>{team.players.length}</span>
                </header>

                <div className="compact-players">
                  {team.players.map((player) => {
                    const rating = getDisplayRating(player, lobby.mode)
                    const playerKey = getPlayerKey(team, player)

                    return (
                      <div
                        className="compact-player"
                        data-new-player={changeState.newPlayerKeys.has(playerKey)}
                        key={playerKey}
                      >
                        <span className="rank-icon-frame compact-rank-frame">
                          <img
                            alt=""
                            className="rank-icon compact-rank-icon"
                            src={getRankIcon(rating?.rank)}
                          />
                        </span>
                        <div className="compact-player-text">
                          <strong title={player.name}>{player.name}</strong>
                          <span>
                            {formatMmr(rating)} {formatCompactRank(rating)}
                          </span>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </article>
            ))}
          </section>

          <section className="details-section" aria-label="Detailed lobby ratings">
            <div className="section-heading">
              <h2>Detailed Ratings</h2>
              <span>All playlists per player</span>
            </div>

            <div className="teams-grid">
              {teams.map(([teamKey, team]) => (
                <article
                  className="team-panel"
                  data-roster-changed={changeState.changedTeams.has(team.team_num)}
                  data-team={team.team_num}
                  key={teamKey}
                >
                  <header className="team-header">
                    <h2>{team.name}</h2>
                    <span>{team.players.length} players</span>
                  </header>

                  <div className="player-list">
                    {team.players.map((player) => {
                      const playerKey = getPlayerKey(team, player)

                      return (
                      <section
                        className="player-row"
                        data-new-player={changeState.newPlayerKeys.has(playerKey)}
                        key={playerKey}
                      >
                        <div className="player-meta">
                          <div>
                            <h3>{player.name}</h3>
                            <span>{player.platform ?? 'unknown'}</span>
                          </div>
                          <span className="rank-icon-frame player-main-rank-frame">
                            <img
                              alt=""
                              className="rank-icon player-main-rank"
                              src={getRankIcon(getDisplayRating(player, lobby.mode)?.rank)}
                            />
                          </span>
                        </div>

                        {player.error && <p className="player-error">{player.error}</p>}

                        <div className="ratings-grid">
                          {PLAYLIST_ORDER.map((mode) => {
                            const rating = player.ratings[mode]

                            return (
                              <div className="rating-cell" key={mode}>
                                <span className="rank-icon-frame rating-rank-frame">
                                  <img
                                    alt=""
                                    className="rank-icon rating-rank-icon"
                                    src={getRankIcon(rating?.rank)}
                                  />
                                </span>
                                <div className="rating-copy">
                                  <span className="playlist">{mode}</span>
                                  <strong>{formatMmr(rating)}</strong>
                                  <span>{rating?.rank ?? 'Unranked'}</span>
                                  <span>{rating?.division ?? ''}</span>
                                </div>
                              </div>
                            )
                          })}
                        </div>
                      </section>
                      )
                    })}
                  </div>
                </article>
              ))}
            </div>
          </section>

          <section className="history-section" aria-label="Recent match history">
            <div className="section-heading">
              <h2>Recent Matches</h2>
              <div className="history-actions">
                <span>{matchHistory.length} saved</span>
                <button
                  disabled={matchHistory.length === 0}
                  onClick={() => {
                    setMatchHistory([])
                    setHiddenTrendIds(new Set())
                    lastSavedMatchSignatureRef.current = null
                    window.localStorage.removeItem(HIDDEN_TRENDS_STORAGE_KEY)
                    window.localStorage.removeItem(MATCH_HISTORY_STORAGE_KEY)
                  }}
                  type="button"
                >
                  Clear
                </button>
              </div>
            </div>

            {matchHistory.length === 0 ? (
              <p className="history-empty">No stable matches saved yet</p>
            ) : (
              <div className="match-history-list">
                {matchHistory.map((match) => (
                  <article className="match-history-card" key={match.id}>
                    <header className="match-history-header">
                      <div>
                        <strong>{match.mode}</strong>
                        <span>{formatMatchSavedAt(match.saved_at)}</span>
                      </div>
                      <div className="match-history-actions">
                        <span>{getMatchPlayerCount(match)} players</span>
                        <button
                          aria-label={`Delete ${match.mode} match from ${formatMatchSavedAt(match.saved_at)}`}
                          onClick={() => {
                            setMatchHistory((currentHistory) => {
                              const nextHistory = currentHistory.filter((candidate) => candidate.id !== match.id)
                              saveMatchHistory(nextHistory)
                              return nextHistory
                            })
                          }}
                          title="Delete match"
                          type="button"
                        >
                          <svg aria-hidden="true" viewBox="0 0 24 24">
                            <path d="M9 3h6l1 2h4v2H4V5h4l1-2Zm-2 6h10l-.7 11H7.7L7 9Zm3 2v7h2v-7h-2Zm4 0v7h2v-7h-2Z" />
                          </svg>
                        </button>
                      </div>
                    </header>

                    <div className="match-history-teams">
                      {match.teams.map((team) => (
                        <section className="match-history-team" data-team={team.team_num} key={team.team_num}>
                          <h3>{shortTeamName(team)}</h3>
                          <div className="match-history-players">
                            {team.players.map((player) => (
                              <div className="match-history-player" key={`${team.team_num}-${player.name}`}>
                                <span title={player.name}>{player.name}</span>
                                <strong>{player.mmr ?? 'N/A'}</strong>
                              </div>
                            ))}
                          </div>
                        </section>
                      ))}
                    </div>
                  </article>
                ))}
              </div>
            )}
          </section>

          <section className="trend-section" aria-label="MMR trends">
            <div className="section-heading">
              <h2>MMR Trends</h2>
              <span>{visibleMmrTrendSeries.length} tracked</span>
            </div>

            {visibleMmrTrendSeries.length === 0 ? (
              <p className="history-empty">Save at least two matches with the same player to start tracking MMR</p>
            ) : (
              <div className="trend-grid">
                {visibleMmrTrendSeries.map((series) => (
                  <article className="trend-card" key={series.id}>
                    <header className="trend-header">
                      <div>
                        <h3>{series.name}</h3>
                        <span>
                          {series.mode} | {series.platform ?? 'unknown'}
                        </span>
                      </div>
                      <div className="trend-actions">
                        <strong>{series.points.at(-1)?.mmr ?? 'N/A'}</strong>
                        <button
                          aria-label={`Hide ${series.name} MMR trend`}
                          onClick={() => {
                            setHiddenTrendIds((currentIds) => {
                              const nextIds = new Set(currentIds)
                              nextIds.add(series.id)
                              saveHiddenTrendIds(nextIds)
                              return nextIds
                            })
                          }}
                          title="Hide graph"
                          type="button"
                        >
                          <svg aria-hidden="true" viewBox="0 0 24 24">
                            <path d="M9 3h6l1 2h4v2H4V5h4l1-2Zm-2 6h10l-.7 11H7.7L7 9Zm3 2v7h2v-7h-2Zm4 0v7h2v-7h-2Z" />
                          </svg>
                        </button>
                      </div>
                    </header>

                    <MmrSparkline points={series.points} />

                    <div className="trend-footer">
                      <span>{series.points[0].mmr}</span>
                      <span>{series.points.length} matches</span>
                      <span>{series.points.at(-1)?.mmr}</span>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </section>
        </>
      )}
    </main>
  )
}

function getDisplayRating(player: Player, lobbyMode: string) {
  return player.ratings[lobbyMode] ?? player.ratings['2v2'] ?? Object.values(player.ratings)[0]
}

function getSortedTeams(lobby: LobbyPayload) {
  return Object.entries(lobby.teams).sort(
    ([, teamA], [, teamB]) => teamA.team_num - teamB.team_num,
  )
}

function createMatchSnapshot(
  lobby: LobbyPayload,
  teams: [string, Team][],
  signature: string,
): MatchSnapshot {
  return {
    id: `${Date.now()}-${signature}`,
    mode: lobby.mode,
    saved_at: new Date().toISOString(),
    signature,
    teams: teams.map(([, team]) => ({
      name: team.name,
      team_num: team.team_num,
      players: team.players.map((player) => {
        const rating = getDisplayRating(player, lobby.mode)

        return {
          division: rating?.division ?? null,
          mmr: rating?.mmr ?? null,
          name: player.name,
          platform: player.platform,
          rank: rating?.rank ?? null,
          team_num: team.team_num,
        }
      }),
    })),
  }
}

function getLobbySignature(lobby: LobbyPayload, teams: [string, Team][]) {
  return JSON.stringify({
    mode: lobby.mode,
    teams: teams.map(([, team]) => ({
      players: team.players
        .map((player) => player.primary_id ?? player.name)
        .sort(),
      team_num: team.team_num,
    })),
  })
}

function getLobbyChangeState(
  lobby: LobbyPayload,
  teams: [string, Team][],
  previousPlayerKeys: Set<string>,
  previousTeamSizes: Map<number, number>,
  previousMode: string | null,
): ChangeState {
  const newPlayerKeys = new Set<string>()
  const changedTeams = new Set<number>()

  for (const [, team] of teams) {
    const previousSize = previousTeamSizes.get(team.team_num)

    if (previousSize !== undefined && previousSize !== team.players.length) {
      changedTeams.add(team.team_num)
    }

    for (const player of team.players) {
      const playerKey = getPlayerKey(team, player)

      if (!previousPlayerKeys.has(playerKey)) {
        newPlayerKeys.add(playerKey)
      }
    }
  }

  return {
    changedTeams,
    isModeChanged: previousMode !== null && previousMode !== lobby.mode,
    newPlayerKeys,
  }
}

function getPlayerKey(team: Team, player: Player) {
  return `${team.team_num}:${player.primary_id ?? player.name}`
}

function getRankIcon(rank: string | null | undefined) {
  if (!rank) {
    return unrankedIcon
  }

  return RANK_ICONS[normalizeRankKey(rank)] ?? unrankedIcon
}

function normalizeRankKey(rank: string) {
  return rank
    .toLowerCase()
    .replace(/\biii\b/g, '3')
    .replace(/\bii\b/g, '2')
    .replace(/\bi\b/g, '1')
    .replace(/[^a-z0-9]/g, '')
}

function formatMmr(rating: Rating | undefined) {
  return rating?.mmr ?? 'N/A'
}

function formatCompactRank(rating: Rating | undefined) {
  if (!rating?.rank) {
    return 'Unranked'
  }

  return rating.division ? `${rating.rank} ${rating.division}` : rating.rank
}

function shortTeamName(team: Pick<Team, 'name' | 'team_num'>) {
  if (team.team_num === 0) {
    return 'Blue'
  }

  if (team.team_num === 1) {
    return 'Orange'
  }

  return team.name
}

function loadMatchHistory() {
  try {
    const storedHistory = window.localStorage.getItem(MATCH_HISTORY_STORAGE_KEY)

    if (!storedHistory) {
      return []
    }

    return JSON.parse(storedHistory) as MatchSnapshot[]
  } catch {
    return []
  }
}

function loadHiddenTrendIds() {
  try {
    const storedIds = window.localStorage.getItem(HIDDEN_TRENDS_STORAGE_KEY)

    if (!storedIds) {
      return new Set<string>()
    }

    return new Set(JSON.parse(storedIds) as string[])
  } catch {
    return new Set<string>()
  }
}

function saveMatchHistory(matchHistory: MatchSnapshot[]) {
  window.localStorage.setItem(MATCH_HISTORY_STORAGE_KEY, JSON.stringify(matchHistory))
}

function saveHiddenTrendIds(hiddenTrendIds: Set<string>) {
  window.localStorage.setItem(HIDDEN_TRENDS_STORAGE_KEY, JSON.stringify([...hiddenTrendIds]))
}

function getMatchPlayerCount(match: MatchSnapshot) {
  return match.teams.reduce((total, team) => total + team.players.length, 0)
}

function formatMatchSavedAt(savedAt: string) {
  return new Date(savedAt).toLocaleTimeString()
}

function getRecurringPlayerMmrSeries(matchHistory: MatchSnapshot[]): MmrTrendSeries[] {
  const playerSeries = new Map<string, MmrTrendSeries>()

  for (const match of [...matchHistory].reverse()) {
    for (const team of match.teams) {
      for (const player of team.players) {
        if (player.mmr === null) {
          continue
        }

        const id = `${match.mode}:${player.platform ?? 'unknown'}:${player.name}`
        const series = playerSeries.get(id) ?? {
          id,
          mode: match.mode,
          name: player.name,
          platform: player.platform,
          points: [],
        }

        series.points.push({
          mmr: player.mmr,
          mode: match.mode,
          saved_at: match.saved_at,
        })
        playerSeries.set(id, series)
      }
    }
  }

  return [...playerSeries.values()]
    .filter((series) => series.points.length >= 2)
    .sort((seriesA, seriesB) => seriesB.points.length - seriesA.points.length)
}

function MmrSparkline({ points }: { points: MmrTrendPoint[] }) {
  const width = 260
  const height = 84
  const padding = 10
  const mmrs = points.map((point) => point.mmr)
  const minMmr = Math.min(...mmrs)
  const maxMmr = Math.max(...mmrs)
  const range = Math.max(maxMmr - minMmr, 1)
  const xStep = points.length > 1 ? (width - padding * 2) / (points.length - 1) : 0
  const coordinates = points.map((point, index) => {
    const x = padding + index * xStep
    const y = height - padding - ((point.mmr - minMmr) / range) * (height - padding * 2)
    return { x, y }
  })
  const path = coordinates
    .map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x.toFixed(1)} ${point.y.toFixed(1)}`)
    .join(' ')
  const areaPath = `${path} L ${coordinates.at(-1)?.x ?? padding} ${height - padding} L ${padding} ${height - padding} Z`

  return (
    <svg className="trend-chart" role="img" viewBox={`0 0 ${width} ${height}`}>
      <defs>
        <linearGradient id="trend-area" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor="rgba(52, 211, 153, 0.34)" />
          <stop offset="100%" stopColor="rgba(52, 211, 153, 0)" />
        </linearGradient>
      </defs>
      <path className="trend-area" d={areaPath} />
      <path className="trend-line" d={path} />
      {coordinates.map((point, index) => (
        <circle className="trend-point" cx={point.x} cy={point.y} key={index} r="3" />
      ))}
    </svg>
  )
}

function formatLastUpdated(lastUpdated: Date | null) {
  if (lastUpdated === null) {
    return 'Waiting for data'
  }

  return `Updated ${lastUpdated.toLocaleTimeString()}`
}

export default App

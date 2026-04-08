import { useState, useEffect } from 'react'
import * as api from '../api'

function ScoreScreen({ campaignId, user }) {
    const [score, setScore] = useState(null)
    const [hallOfFame, setHallOfFame] = useState([])
    const [loading, setLoading] = useState(true)
    const username = user?.username ?? ''

    useEffect(() => {
        async function loadScore() {
            const scoreData = await api.getScore(campaignId, username)
            const hofData = await api.getHallOfFame()
            setScore(scoreData)
            setHallOfFame(hofData.entries)
            setLoading(false)
        }
        loadScore()
    }, [campaignId, username])

    if (loading) return <div className="loading">Calculating score...</div>

    return (
        <div className="score-screen">
            <h1>🏆 Campaign Complete!</h1>

            <div className="score-card">
                <h2>{username}</h2>
                <div className="score-breakdown">
                    <div className="score-row">
                        <span>Hero Levels</span>
                        <span>{score.hero_level_score} pts</span>
                    </div>
                    <div className="score-row">
                        <span>Gold Remaining</span>
                        <span>{score.gold_score} pts</span>
                    </div>
                    <div className="score-row">
                        <span>Items Purchased</span>
                        <span>{score.item_score} pts</span>
                    </div>
                    <div className="score-row total">
                        <span>Total Score</span>
                        <span>{score.total_score} pts</span>
                    </div>
                    <p className="rank">Rank #{score.rank}</p>
                </div>
            </div>

            <div className="hall-of-fame">
                <h2>🏅 Hall of Fame</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Rank</th>
                            <th>Player</th>
                            <th>Score</th>
                        </tr>
                    </thead>
                    <tbody>
                        {hallOfFame.map(entry => (
                            <tr
                                key={entry.rank}
                                className={entry.username === username ? 'highlight' : ''}
                            >
                                <td>#{entry.rank}</td>
                                <td>{entry.username}</td>
                                <td>{entry.total_score}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    )
}

export default ScoreScreen
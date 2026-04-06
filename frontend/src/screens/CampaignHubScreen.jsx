import { useEffect, useState } from 'react'
import * as api from '../api'

function CampaignHubScreen({ user, onCampaignSelected }) {
    const [heroName, setHeroName] = useState('')
    const [heroClass, setHeroClass] = useState('warrior')
    const [campaigns, setCampaigns] = useState([])
    const [loading, setLoading] = useState(true)
    const [creating, setCreating] = useState(false)
    const [error, setError] = useState('')

    useEffect(() => {
        let mounted = true

        async function loadCampaigns() {
            try {
                const data = await api.getUserCampaigns(user.id)
                if (mounted) {
                    setCampaigns(data)
                }
            } catch {
                if (mounted) {
                    setError('Failed to load campaigns.')
                }
            } finally {
                if (mounted) {
                    setLoading(false)
                }
            }
        }

        loadCampaigns()

        return () => {
            mounted = false
        }
    }, [user.id])

    async function handleCreateCampaign() {
        if (!heroName) {
            setError('Hero name is required.')
            return
        }

        setCreating(true)
        setError('')
        try {
            const campaign = await api.startCampaign(
                user.id,
                user.username,
                heroName,
                heroClass
            )
            onCampaignSelected(campaign.id)
        } catch {
            setError('Failed to create campaign.')
        }
        setCreating(false)
    }

    const activeCampaigns = campaigns.filter(campaign => campaign.status === 'active')

    return (
        <div className="hub-screen">
            <h1>Welcome, {user.username}</h1>

            <div className="hub-grid">
                <section className="hub-card">
                    <h2>Create Campaign</h2>
                    <label>Hero Name</label>
                    <input
                        type="text"
                        value={heroName}
                        onChange={e => setHeroName(e.target.value)}
                        placeholder="Name your hero"
                    />

                    <label>Hero Class</label>
                    <select value={heroClass} onChange={e => setHeroClass(e.target.value)}>
                        <option value="warrior">⚔️ Warrior</option>
                        <option value="order">🛡️ Order</option>
                        <option value="chaos">🔥 Chaos</option>
                        <option value="mage">🪄 Mage</option>
                    </select>

                    <button
                        className="primary-btn"
                        onClick={handleCreateCampaign}
                        disabled={creating}
                    >
                        {creating ? 'Creating...' : 'Create New Campaign'}
                    </button>
                </section>

                <section className="hub-card">
                    <h2>Continue Campaign</h2>
                    {loading && <p className="loading-inline">Loading your campaigns...</p>}
                    {!loading && activeCampaigns.length === 0 && (
                        <p className="loading-inline">No active campaigns found.</p>
                    )}
                    {!loading && activeCampaigns.map(campaign => (
                        <div key={campaign.id} className="campaign-list-item">
                            <div>
                                <strong>Campaign #{campaign.id}</strong>
                                <p>Room {campaign.current_room} | Gold: {campaign.gold}</p>
                            </div>
                            <button
                                className="secondary-btn"
                                onClick={() => onCampaignSelected(campaign.id)}
                            >
                                Continue
                            </button>
                        </div>
                    ))}
                </section>
            </div>

            {error && <p className="error">{error}</p>}
        </div>
    )
}

export default CampaignHubScreen

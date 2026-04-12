import { useEffect, useState } from 'react'
import * as api from '../api'

function CampaignHubScreen({ user, onCampaignSelected }) {
    const [heroName, setHeroName] = useState('')
    const [heroClass, setHeroClass] = useState('warrior')
    const [campaigns, setCampaigns] = useState([])
    const [loading, setLoading] = useState(true)
    const [creating, setCreating] = useState(false)
    const [error, setError] = useState('')
    
    const [pvpParties, setPvpParties] = useState([]);
    const [pvpLoading, setPvpLoading] = useState(true);
    // Effect for PvP Data
    useEffect(() => {
        async function loadPvPData() {
            try {
                // We fetch by username since PvP identifies users that way
                const parties = await api.getUserParties(user.username);
                setPvpParties(parties);
            } catch (err) {
                console.error("PvP Load Error:", err);
            } finally {
                setPvpLoading(false);
            }
        }
        if (user?.username) loadPvPData();
    }, [user.username]);

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
            

            {/* --- UPDATED: PVP SECTION --- */}
            <div className="pvp-container">
                <section className="hub-card">
                    <h2>Proving Grounds (PvP)</h2>
                    
                    {pvpLoading ? (
                        <p className="loading-inline">Searching for your squad...</p>
                    ) : pvpParties.length > 0 ? (
                        <div className="pvp-party-list">
                            {pvpParties.map(party => (
                                <div key={party.party_id} className="campaign-list-item">
                                    <div>
                                        <strong>{party.name}</strong>
                                        <p>Ready for Battle</p>
                                    </div>
                                    <button className="primary-btn" style={{width: 'auto', padding: '8px 16px'}}>
                                        Enter Arena
                                    </button>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="pvp-test-content">
                            <p>No PvP party found. Contacting the guild...</p>
                            <div className="test-box-visual"></div>
                        </div>
                    )}
                </section>
            </div>

            {error && <p className="error">{error}</p>}
        </div>
    )
}

export default CampaignHubScreen

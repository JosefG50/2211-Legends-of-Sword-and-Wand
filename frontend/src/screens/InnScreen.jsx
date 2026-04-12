import { useState, useEffect } from 'react'
import * as api from '../api'

function InnScreen({ campaignId, onLeave }) {
    const [innData, setInnData] = useState(null)
    const [gold, setGold] = useState(0)
    const [messages, setMessages] = useState([])
    const [loading, setLoading] = useState(true)

    function addMessage(msg) {
        setMessages(prev => [msg, ...prev])
    }

    useEffect(() => {
        async function loadInn() {
            const data = await api.getInn(campaignId)
            setInnData(data)

            // Show what happened on arrival
            if (data.revived_heroes.length > 0) {
                addMessage(`✨ Revived: ${data.revived_heroes.join(', ')}`)
            }
            Object.entries(data.healed_heroes).forEach(([name, amount]) => {
                if (amount > 0) addMessage(`💚 ${name} restored ${amount} HP`)
            })

            // Get current gold
            const campaign = await api.getCampaign(campaignId)
            setGold(campaign.gold)
            setLoading(false)
        }
        loadInn()
    }, [campaignId])

    async function handlePurchase(itemName, cost) {
        if (gold < cost) {
            addMessage(`❌ Not enough gold for ${itemName}`)
            return
        }
        const result = await api.purchaseItem(campaignId, itemName, 1)
        if (result.success) {
            setGold(result.gold_remaining)
            addMessage(`✅ Purchased ${itemName} for ${cost}g`)
        } else {
            addMessage(`❌ ${result.message}`)
        }
    }

    async function handleLeave() {
        await api.leaveInn(campaignId)
        onLeave()
    }

    if (loading) return <div className="loading">You enter the inn...</div>

    return (
        <div className="inn-screen">
            <h1>🏨 The Wanderer's Rest</h1>
            <p className="gold-display">💰 Your gold: {gold}g</p>

            {/* Shop */}
            <div className="shop-panel">
                <h2>🛒 Shop</h2>
                <div className="items-grid">
                    {innData.available_items.map(item => (
                        <div key={item.name} className="shop-item">
                            <div className="item-name">{item.name}</div>
                            <div className="item-effect">{item.effect}</div>
                            <div className="item-cost">{item.cost}g</div>
                            <button
                                onClick={() => handlePurchase(item.name, item.cost)}
                                disabled={gold < item.cost}
                            >
                                Buy
                            </button>
                        </div>
                    ))}
                </div>
            </div>

            {/* Hero recruitment — only in first 10 rooms */}
            {innData.available_heroes.length > 0 && (
                <div className="recruit-panel">
                    <h2>⚔️ Available Heroes</h2>
                    {innData.available_heroes.map(hero => (
                        <div key={hero.id} className="recruit-card">
                            <span>{hero.name} — {hero.hero_class} Lv.{hero.level}</span>
                            <span>{hero.recruit_cost === 0 ? 'FREE' : `${hero.recruit_cost}g`}</span>
                            <button
                                onClick={async () => {
                                    const result = await api.recruitHero(campaignId, hero.id, hero.name)
                                    if (result.success) {
                                        setGold(result.gold_remaining)
                                        addMessage(`🎉 ${hero.name} joined your party!`)
                                    }
                                }}
                                disabled={gold < hero.recruit_cost || innData.party_full}
                            >
                                Recruit
                            </button>
                        </div>
                    ))}
                </div>
            )}

            {/* Message log */}
            <div className="message-log">
                {messages.map((msg, i) => <p key={i}>{msg}</p>)}
            </div>

            <button className="primary-btn" onClick={handleLeave}>
                ➡️ Continue Adventure
            </button>
        </div>
    )
}

export default InnScreen
import { useState, useEffect } from 'react'
import * as api from '../api'

const ABILITY_EMOJI = {
  protect:          '🛡️',
  heal:             '💚',
  group_heal:       '💚',
  fireball:         '🔥',
  chain_lightning:  '⚡',
  berserker_attack: '⚔️',
  replenish:        '✨',
  fire_shield:      '🔥',
  sneak_attack:     '🗡️',
  mana_burn:        '🔮',
}

function abilityEmoji(name) {
  const key = name.toLowerCase().replace(/ /g, '_')
  return ABILITY_EMOJI[key] || '✨'
}

function HeroCard({ hero, abilities }) {
  const hpPercent = (hero.hp   / hero.max_hp)   * 100
  const mpPercent = (hero.mana / hero.max_mana) * 100

  return (
    <div className={`hero-card ${!hero.is_alive ? 'dead' : ''}`}>

      {/* Name + class */}
      <div className="hero-name">
        {hero.name}
        {!hero.is_alive && <span className="dead-label"> ☠️ Dead</span>}
      </div>
      <div className="hero-class">
        {hero.hero_class
          ? hero.hero_class.charAt(0).toUpperCase() + hero.hero_class.slice(1)
          : 'Base'
        } — Lv.{hero.level}
      </div>

      {/* HP / MP bars */}
      <div className="stat-bars">
        <div className="stat-row">
          <span>HP</span>
          <div className="bar-bg">
            <div className="bar-fill hp" style={{ width: `${hpPercent}%` }} />
          </div>
          <span>{hero.hp}/{hero.max_hp}</span>
        </div>
        <div className="stat-row">
          <span>MP</span>
          <div className="bar-bg">
            <div className="bar-fill mp" style={{ width: `${mpPercent}%` }} />
          </div>
          <span>{hero.mana}/{hero.max_mana}</span>
        </div>
      </div>

      {/* ATK / DEF */}
      <div className="hero-stats">
        ATK {hero.attack} | DEF {hero.defense}
      </div>

      {/* Abilities */}
      {abilities && abilities.length > 0 && (
        <div className="hero-abilities">
          <div className="abilities-label">Abilities</div>
          {abilities.map(ab => (
            <div
              key={ab.name}
              className={`ability-tag ability-${ab.type}`}
              title={ab.effect_modifier || ''}
            >
              <span className="ability-icon">{abilityEmoji(ab.name)}</span>
              <span className="ability-name">{ab.name}</span>
              {ab.type !== 'passive' && (
                <span className="ability-cost">{ab.mana_cost} MP</span>
              )}
              {ab.type === 'passive' && (
                <span className="ability-passive-tag">passive</span>
              )}
            </div>
          ))}
        </div>
      )}
      {abilities && abilities.length === 0 && (
        <div className="hero-abilities">
          <div className="abilities-label">Abilities</div>
          <p className="no-abilities">Level up to unlock abilities</p>
        </div>
      )}
    </div>
  )
}

function CampaignScreen({ campaignId, onBattleRoom, onInnRoom, onComplete, onSavedExit }) {
  const [campaign,    setCampaign]    = useState(null)
  const [loading,     setLoading]     = useState(true)
  const [advancing,   setAdvancing]   = useState(false)
  const [messages,    setMessages]    = useState(['Your adventure begins...'])
  // heroAbilities: map from hero.id -> abilities array
  const [heroAbilities, setHeroAbilities] = useState({})

  function addMessage(msg) {
    setMessages(prev => [msg, ...prev])
  }

  // Load campaign + abilities on mount
  useEffect(() => {
    async function load() {
      const data = await api.getCampaign(campaignId)
      setCampaign(data)
      setLoading(false)

      // Fetch abilities for each hero from Party service
      const map = {}
      await Promise.all(
        data.heroes.map(async hero => {
          try {
            const abs = await api.getHeroAbilities(hero.id)
            map[hero.id] = abs
          } catch {
            map[hero.id] = []
          }
        })
      )
      setHeroAbilities(map)
    }
    load()
  }, [campaignId])

  async function handleNextRoom() {
    setAdvancing(true)
    try {
      const room = await api.nextRoom(campaignId)
      addMessage(`You enter room ${room.room_number}...`)

      const updated = await api.getCampaign(campaignId)
      setCampaign(updated)

      if (room.room_number >= 30) {
        addMessage('You have completed the campaign!')
        onComplete()
        return
      }

      if (room.room_type === 'battle') {
        addMessage(`⚔️ Enemies appear! ${room.enemy_party.length} units!`)
        onBattleRoom(room)
      } else {
        addMessage('🏨 You find a cozy inn...')
        onInnRoom(room)
      }
    } catch {
      addMessage('Something went wrong.')
    }
    setAdvancing(false)
  }

  async function handleSave() {
    await api.saveCampaign(campaignId)
    addMessage('Progress saved.')
    onSavedExit()
  }

  if (loading) return <div className="loading">Loading campaign...</div>

  const aliveHeroes = campaign.heroes.filter(h => h.is_alive)

  return (
    <div className="campaign-screen">

      {/* Left panel — party */}
      <div className="party-panel">
        <h2>Your Party</h2>
        {campaign.heroes.map(hero => (
          <HeroCard
            key={hero.id}
            hero={hero}
            abilities={heroAbilities[hero.id]}
          />
        ))}
        <div className="party-stats">
          <p>💰 Gold: {campaign.gold}g</p>
          <p>🗺️ Room: {campaign.current_room} / 30</p>
          <p>⚔️ Alive: {aliveHeroes.length} / {campaign.heroes.length}</p>
        </div>
      </div>

      {/* Right panel — actions and log */}
      <div className="action-panel">
        <div className="action-buttons">
          <button
            onClick={handleNextRoom}
            disabled={advancing}
            className="primary-btn"
          >
            {advancing ? 'Entering room...' : '➡️ Enter Next Room'}
          </button>
          <button onClick={handleSave} className="secondary-btn">
            💾 Save & Exit
          </button>
        </div>

        <div className="message-log">
          <h3>Adventure Log</h3>
          {messages.map((msg, i) => (
            <p key={i} className={i === 0 ? 'latest' : 'old'}>{msg}</p>
          ))}
        </div>
      </div>

    </div>
  )
}

export default CampaignScreen

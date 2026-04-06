import axios from 'axios'

// All requests go through the API Gateway
const client = axios.create({
    baseURL: 'http://localhost:80',
})

// Automatically attach the auth token to every request
client.interceptors.request.use(config => {
    const token = localStorage.getItem('token')
    if (token) {
        config.headers.Authorization = `Bearer ${token}`
    }
    return config
})

// ─── Auth ──────────────────────────────────────────────

export async function login(username, password) {
    const res = await client.post('/auth/login', { username, password })
    localStorage.setItem('token', res.data.token)
    return res.data
}

export async function register(username, password) {
    const res = await client.post('/auth/register', { username, password })
    return res.data
}

// ─── Campaign ──────────────────────────────────────────

export async function startCampaign(userId, username, heroName, heroClass) {
    const res = await client.post('/pve/campaign/start', {
        user_id: userId,
        username,
        hero_name: heroName,
        hero_class: heroClass,
    })
    return res.data
}

export async function getCampaign(campaignId) {
    const res = await client.get(`/pve/campaign/${campaignId}`)
    return res.data
}

export async function getUserCampaigns(userId) {
    const res = await client.get(`/pve/campaign/user/${userId}`)
    return res.data
}

export async function nextRoom(campaignId) {
    const res = await client.post(`/pve/campaign/${campaignId}/next-room`)
    return res.data
}

export async function saveCampaign(campaignId) {
    const res = await client.post(`/pve/campaign/${campaignId}/save`)
    return res.data
}

// ─── Inn ───────────────────────────────────────────────

export async function getInn(campaignId) {
    const res = await client.get(`/pve/campaign/${campaignId}/inn`)
    return res.data
}

export async function purchaseItem(campaignId, itemName, quantity) {
    const res = await client.post(`/pve/campaign/${campaignId}/inn/purchase`, {
        item_name: itemName,
        quantity,
    })
    return res.data
}

export async function recruitHero(campaignId, heroPoolId, heroName) {
    const res = await client.post(`/pve/campaign/${campaignId}/inn/recruit`, {
        hero_pool_id: heroPoolId,
        hero_name: heroName,
    })
    return res.data
}

export async function leaveInn(campaignId) {
    const res = await client.post(`/pve/campaign/${campaignId}/inn/leave`)
    return res.data
}

// ─── Battle ────────────────────────────────────────────

export async function submitBattleResult(campaignId, result, survivingHeroIds, enemyParty) {
    const res = await client.post(`/pve/campaign/${campaignId}/battle-result`, {
        campaign_id: campaignId,
        result,
        surviving_hero_ids: survivingHeroIds,
        enemy_party: enemyParty,
    })
    return res.data
}

export async function levelUpHero(campaignId, heroId, classToLevel) {
    const res = await client.post(
        `/pve/campaign/${campaignId}/hero/${heroId}/level-up`,
        { hero_id: heroId, class_to_level: classToLevel }
    )
    return res.data
}

// ─── Score ─────────────────────────────────────────────

export async function getScore(campaignId, username) {
    const res = await client.post(`/pve/campaign/${campaignId}/score`, { username })
    return res.data
}

export async function getHallOfFame() {
    const res = await client.get('/pve/hall-of-fame')
    return res.data
}
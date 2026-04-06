const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

async function request(path, options = {}) {
    const response = await fetch(`${API_BASE_URL}${path}`, {
        headers: {
            'Content-Type': 'application/json',
            ...(options.headers ?? {})
        },
        ...options
    })

    if (!response.ok) {
        const errorText = await response.text()
        throw new Error(errorText || `Request failed with status ${response.status}`)
    }

    if (response.status === 204) {
        return null
    }

    return response.json()
}

export function login(username, password) {
    return request('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ username, password })
    })
}

export function startCampaign(userId, username, heroName, heroClass) {
    return request('/campaign/start', {
        method: 'POST',
        body: JSON.stringify({
            user_id: userId,
            username,
            hero_name: heroName,
            hero_class: heroClass
        })
    })
}

export function getCampaign(campaignId) {
    return request(`/campaign/${campaignId}`)
}

export function getUserCampaigns(userId) {
    return request(`/campaign/user/${userId}`)
}

export function nextRoom(campaignId) {
    return request(`/campaign/${campaignId}/next-room`, {
        method: 'POST'
    })
}

export function saveCampaign(campaignId) {
    return request(`/campaign/${campaignId}/save`, {
        method: 'POST'
    })
}

export function getInn(campaignId) {
    return request(`/campaign/${campaignId}/inn`)
}

export function purchaseItem(campaignId, itemName, quantity) {
    return request(`/campaign/${campaignId}/inn/purchase`, {
        method: 'POST',
        body: JSON.stringify({
            item_name: itemName,
            quantity
        })
    })
}

export function recruitHero(campaignId, heroId, heroName) {
    return request(`/campaign/${campaignId}/inn/recruit`, {
        method: 'POST',
        body: JSON.stringify({
            hero_pool_id: String(heroId),
            hero_name: heroName
        })
    })
}

export function leaveInn(campaignId) {
    return request(`/campaign/${campaignId}/inn/leave`, {
        method: 'POST'
    })
}

export function getScore(campaignId, username) {
    const query = new URLSearchParams({ username })
    return request(`/score/${campaignId}?${query.toString()}`)
}

export function getHallOfFame() {
    return request('/hall-of-fame')
}

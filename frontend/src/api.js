import axios from "axios";

// ─── Clients ────────────────────────────────────────────────────────────────
// In development (npm run dev): Vite proxies /pve/* -> http://localhost:8000
// In Docker: the same proxy config works because Vite runs inside the container
// Battle service is called directly on port 8001

const pveClient = axios.create({ baseURL: "/" });


const partyClient = axios.create({ baseURL: "/" });

const battleClient = axios.create({
  baseURL: import.meta.env.VITE_BATTLE_URL || "http://localhost:8001",
});

// ─── Auth headers ────────────────────────────────────────────────────────────
pveClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// ─── Auth ────────────────────────────────────────────────────────────────────
// The PvE auth endpoint returns { user: { id, username }, created: bool }
// There is no JWT token — the user object is stored directly in state

export async function login(username, password) {
  const res = await pveClient.post("/pve/auth/login", { username, password });
  // Return the full response so App.jsx can extract user
  return res.data;
}

// ─── Campaign ────────────────────────────────────────────────────────────────

export async function startCampaign(userId, username, heroName, heroClass) {
  const res = await pveClient.post("/pve/campaign/start", {
    user_id: userId,
    username,
    hero_name: heroName,
    hero_class: heroClass,
  });
  return res.data;
}

export async function getCampaign(campaignId) {
  const res = await pveClient.get(`/pve/campaign/${campaignId}`);
  return res.data;
}

export async function getUserCampaigns(userId) {
  const res = await pveClient.get(`/pve/campaign/user/${userId}`);
  return res.data;
}

export async function nextRoom(campaignId) {
  const res = await pveClient.post(`/pve/campaign/${campaignId}/next-room`);
  return res.data;
}

export async function saveCampaign(campaignId) {
  const res = await pveClient.post(`/pve/campaign/${campaignId}/save`);
  return res.data;
}

// ─── Battle result (reports outcome back to PvE after a battle) ──────────────

export async function submitBattleResult(
  campaignId,
  result,
  survivingHeroIds,
  enemyParty,
) {
  const res = await pveClient.post(
    `/pve/campaign/${campaignId}/battle-result`,
    {
      campaign_id: campaignId,
      result,
      surviving_hero_ids: survivingHeroIds,
      enemy_party: enemyParty,
    },
  );
  return res.data;
}

export async function levelUpHero(campaignId, heroId, classToLevel) {
  const res = await pveClient.post(
    `/pve/campaign/${campaignId}/hero/${heroId}/level-up`,
    { hero_id: heroId, class_to_level: classToLevel },
  );
  return res.data;
}

// ─── Inn ─────────────────────────────────────────────────────────────────────

export async function getInn(campaignId) {
  const res = await pveClient.get(`/pve/campaign/${campaignId}/inn`);
  return res.data;
}

export async function purchaseItem(campaignId, itemName, quantity) {
  const res = await pveClient.post(`/pve/campaign/${campaignId}/inn/purchase`, {
    item_name: itemName,
    quantity,
  });
  return res.data;
}

export async function recruitHero(campaignId, heroPoolId, heroName) {
  const res = await pveClient.post(`/pve/campaign/${campaignId}/inn/recruit`, {
    hero_pool_id: heroPoolId,
    hero_name: heroName,
  });
  return res.data;
}

export async function leaveInn(campaignId) {
  const res = await pveClient.post(`/pve/campaign/${campaignId}/inn/leave`);
  return res.data;
}

// ─── Score ────────────────────────────────────────────────────────────────────

export async function getScore(campaignId, username) {
  const res = await pveClient.post(`/pve/campaign/${campaignId}/score`, {
    username,
  });
  return res.data;
}

export async function getHallOfFame() {
  const res = await pveClient.get("/pve/hall-of-fame");
  return res.data;
}

// ─── Hero abilities by class ──────────────────────────────────────────────────
// Fetches the abilities for a hero class from the Battle service.
// The Party service uses a separate MongoDB ID that differs from the PvE hero id,
// so we derive abilities from the hero's class_name instead.

export async function getHeroAbilities(className) {
  try {
    const res = await battleClient.get(`/abilities/${className}`);
    return res.data.abilities || [];
  } catch {
    return [];
  }
}

// ─── Battle Service (turn-based, called directly on port 8001) ───────────────
//
// Flow:
//   1. startBattle()        → get battle_id and initial game state
//   2. submitBattleAction() → call once per player turn until battle_over = true
//   3. submitBattleResult() → report outcome to PvE service (function above)

export async function startBattle(teamA, teamB, nameA, nameB, mode = "pve") {
  const res = await battleClient.post("/battle/start", {
    team_a: teamA,
    team_b: teamB,
    name_a: nameA,
    name_b: nameB,
    mode,
  });
  return res.data;
}

export async function submitBattleAction(battleId, action, targetIndex = 0) {
  const res = await battleClient.post("/battle/action", {
    battle_id: battleId,
    action,
    target_index: targetIndex,
  });
  return res.data;
}

export async function getBattleState(battleId) {
  const res = await battleClient.get(`/battle/state/${battleId}`);
  return res.data;
}

// ─── PvP (battle service) ─────────────────────────────────────────────────────

export async function sendPvpInvite(inviter, invitee) {
  const res = await battleClient.post("/pvp/invite", { inviter, invitee });
  return res.data;
}

export async function respondToInvite(invitationId, action) {
  const res = await battleClient.post(`/pvp/invite/${invitationId}/respond`, {
    action,
  });
  return res.data;
}

export async function getInvitations(username) {
  const res = await battleClient.get(`/pvp/invitations?username=${username}`);
  return res.data;
}

export async function getLeagueStandings() {
  const res = await battleClient.get("/pvp/league");
  return res.data;
}

import { useState, useEffect, useRef } from "react";
import * as api from "../api";

// ─── Hero card component ──────────────────────────────────────────────────────

function HeroCard({ hero, isActive, isTargetable, onTarget }) {
  const hpPct = Math.max(0, (hero.hp / hero.max_hp) * 100);
  const manaPct = Math.max(0, (hero.mana / hero.max_mana) * 100);
  const alive = hero.hp > 0;

  let cls = "battle-hero-card";
  if (!alive) cls += " dead";
  if (isActive) cls += " active";
  if (isTargetable) cls += " targetable";

  return (
    <div
      className={cls}
      onClick={() => isTargetable && alive && onTarget(hero.index ?? 0)}
      title={isTargetable && alive ? `Click to attack ${hero.name}` : ""}
    >
      {isActive && <div className="active-indicator">⚡ Acting</div>}
      {isTargetable && alive && (
        <div className="target-indicator">🎯 Click to target</div>
      )}

      <div className="battle-hero-name">
        {hero.name}
        {!alive && <span className="dead-tag"> ☠️</span>}
      </div>
      <div className="battle-hero-class">
        {hero.class_name} — Lv.{hero.level}
      </div>

      <div className="stat-row">
        <span>HP</span>
        <div className="bar-bg">
          <div className="bar-fill hp" style={{ width: `${hpPct}%` }} />
        </div>
        <span className="stat-num">
          {hero.hp}/{hero.max_hp}
        </span>
      </div>

      <div className="stat-row">
        <span>MP</span>
        <div className="bar-bg">
          <div className="bar-fill mp" style={{ width: `${manaPct}%` }} />
        </div>
        <span className="stat-num">
          {hero.mana}/{hero.max_mana}
        </span>
      </div>

      {hero.shield > 0 && (
        <div className="shield-tag">🛡 Shield: {hero.shield}</div>
      )}

      <div className="hero-stats">
        ATK {hero.attack} | DEF {hero.defense}
      </div>
    </div>
  );
}

// ─── BattleScreen ─────────────────────────────────────────────────────────────

function BattleScreen({ campaignId, roomData, onFinished }) {
  const [battleState, setBattleState] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [waitingForTarget, setWaitingForTarget] = useState(null);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const logRef = useRef(null);

  // ── Start battle on mount ─────────────────────────────────────────────────

  useEffect(() => {
    async function init() {
      try {
        // Get current hero stats from PvE service
        const campaign = await api.getCampaign(campaignId);

        const playerHeroes = campaign.heroes
          .filter((h) => h.is_alive)
          .map((h, i) => ({
            name: h.name,
            level: h.level,
            attack: h.attack,
            defense: h.defense,
            hp: h.hp,
            max_hp: h.max_hp,
            mana: h.mana,
            max_mana: h.max_mana,
            shield: 0,
            class_name: h.hero_class,
            index: i,
            db_id: h.id,
          }));

        const enemies = (roomData?.enemy_party || []).map((e, i) => ({
          name: `Enemy ${i + 1}`,
          level: e.level,
          attack: e.attack,
          defense: e.defense,
          hp: e.hp,
          max_hp: e.max_hp,
          mana: 0,
          max_mana: 1,
          shield: 0,
          class_name: "Warrior",
          index: i,
          db_id: e.id,
        }));

        if (playerHeroes.length === 0) {
          setError(
            "All your heroes are defeated. You cannot enter this battle.",
          );
          setLoading(false);
          return;
        }

        const state = await api.startBattle(
          playerHeroes,
          enemies,
          "Player",
          "Enemies",
          "pve",
        );
        setBattleState(state);
      } catch (e) {
        console.error(e);
        setError(
          "Could not connect to the battle service. Make sure it is running on port 8001.",
        );
      }
      setLoading(false);
    }
    init();
  }, [campaignId, roomData]);

  // ── Auto-scroll log ───────────────────────────────────────────────────────

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [battleState?.log]);

  // ── Submit action ─────────────────────────────────────────────────────────

  async function sendAction(action, targetIndex = 0) {
    if (submitting || !battleState) return;
    setSubmitting(true);
    setWaitingForTarget(null);
    setError("");
    try {
      const state = await api.submitBattleAction(
        battleState.battle_id,
        action,
        targetIndex,
      );
      setBattleState(state);
      if (state.battle_over) await handleBattleOver(state);
    } catch (e) {
      console.error(e);
      setError("Action failed. Please try again.");
    }
    setSubmitting(false);
  }

  // ── Handle target click ───────────────────────────────────────────────────

  function handleTargetClick(targetIndex) {
    if (waitingForTarget) sendAction(waitingForTarget, targetIndex);
  }

  // ── Battle over ───────────────────────────────────────────────────────────

  async function handleBattleOver(state) {
    const playerWon = state.winner === "Player";
    const outcome = playerWon ? "win" : "loss";

    const survivingIds = (state.team_a || [])
      .filter((h) => h.hp > 0 && h.db_id)
      .map((h) => h.db_id);

    const enemyParty = (state.team_b || []).map((e) => ({
      id: e.db_id || 0,
      level: e.level,
      attack: e.attack,
      defense: e.defense,
      hp: e.hp,
      max_hp: e.max_hp,
      is_alive: e.hp > 0,
      is_stunned: false,
    }));

    try {
      await api.submitBattleResult(
        campaignId,
        outcome,
        survivingIds,
        enemyParty,
      );
    } catch (e) {
      console.error("Could not report battle result to PvE service:", e);
    }

    setResult({
      outcome,
      message: playerWon
        ? "Victory! You defeated the enemies."
        : "Defeat! Your party has fallen. You return to the last inn.",
    });
  }

  // ── Render action buttons ──────────────────────────────────────────────────

  function renderActions() {
    if (!battleState || battleState.battle_over) return null;
    const turn = battleState.current_turn;
    if (!turn || turn.team !== "a") {
      return <p className="waiting-msg">Enemy is acting...</p>;
    }

    if (waitingForTarget) {
      return (
        <div className="target-prompt">
          <p>🎯 Click an enemy to target</p>
          <button
            className="secondary-btn"
            onClick={() => setWaitingForTarget(null)}
          >
            Cancel
          </button>
        </div>
      );
    }

    const actions = turn.available_actions || [];
    return (
      <div className="action-buttons">
        <p className="acting-hero-label">⚡ {turn.hero_name}'s turn</p>

        {actions.includes("attack") && (
          <button
            className="primary-btn attack-btn"
            onClick={() => setWaitingForTarget("attack")}
            disabled={submitting}
          >
            ⚔️ Attack
          </button>
        )}

        {actions.includes("defend") && (
          <button
            className="secondary-btn"
            onClick={() => sendAction("defend")}
            disabled={submitting}
          >
            🛡 Defend (+10 HP, +5 MP)
          </button>
        )}

        {actions.includes("wait") && (
          <button
            className="secondary-btn"
            onClick={() => sendAction("wait")}
            disabled={submitting}
          >
            ⏳ Wait
          </button>
        )}

        {actions
          .filter((a) => a.startsWith("cast:"))
          .map((a) => {
            const ability = a.split(":")[1];
            const needsTarget = [
              "fireball",
              "chain_lightning",
              "berserker_attack",
            ].includes(ability);
            return (
              <button
                key={a}
                className="secondary-btn cast-btn"
                onClick={() =>
                  needsTarget ? setWaitingForTarget(a) : sendAction(a)
                }
                disabled={submitting}
              >
                ✨{" "}
                {ability
                  .replace(/_/g, " ")
                  .replace(/\b\w/g, (c) => c.toUpperCase())}
              </button>
            );
          })}
      </div>
    );
  }

  // ── Loading / error ────────────────────────────────────────────────────────

  if (loading) return <div className="loading">⚔️ Preparing battle...</div>;

  if (error && !battleState) {
    return (
      <div className="loading">
        <p className="error">{error}</p>
        <button
          className="secondary-btn"
          onClick={onFinished}
          style={{ marginTop: 16 }}
        >
          Return to Campaign
        </button>
      </div>
    );
  }

  // ── Battle over screen ──────────────────────────────────────────────────

  if (result) {
    return (
      <div className="battle-result-screen">
        <h1>{result.outcome === "win" ? "🏆 Victory!" : "💀 Defeat"}</h1>
        <p className="result-msg">{result.message}</p>

        <div className="final-party">
          <h3>Your Party</h3>
          <div className="final-heroes">
            {(battleState?.team_a || []).map((h, i) => (
              <div
                key={i}
                className={`final-hero-card ${h.hp <= 0 ? "dead" : ""}`}
              >
                <div className="hero-name">{h.name}</div>
                <div className="hero-class">{h.class_name}</div>
                <div>
                  {h.hp <= 0 ? "☠️ Fallen" : `❤️ ${h.hp}/${h.max_hp} HP`}
                </div>
              </div>
            ))}
          </div>
        </div>

        <button
          className="primary-btn"
          onClick={onFinished}
          style={{ maxWidth: 300, margin: "0 auto" }}
        >
          Continue Adventure
        </button>
      </div>
    );
  }

  const teamA = battleState?.team_a || [];
  const teamB = battleState?.team_b || [];
  const turn = battleState?.current_turn;

  // ── Main battle view ────────────────────────────────────────────────────

  return (
    <div className="battle-screen">
      <div className="battle-header">
        <h2>⚔️ Battle — Room {roomData?.room_number}</h2>
        {submitting && (
          <span style={{ color: "#aaa", fontSize: "0.85rem" }}>
            Processing...
          </span>
        )}
      </div>

      <div className="battle-arena">
        {/* Player party */}
        <div className="battle-team player-team">
          <h3 className="team-label">Your Party</h3>
          {teamA.map((hero, i) => (
            <HeroCard
              key={i}
              hero={hero}
              isActive={turn?.team === "a" && turn?.hero_name === hero.name}
              isTargetable={false}
              onTarget={() => {}}
            />
          ))}
        </div>

        {/* Actions centre */}
        <div className="battle-centre">
          <div className="vs-label">VS</div>
          {renderActions()}
          {error && (
            <p className="error" style={{ marginTop: 8, textAlign: "center" }}>
              {error}
            </p>
          )}
        </div>

        {/* Enemy party */}
        <div className="battle-team enemy-team">
          <h3 className="team-label enemy">Enemies</h3>
          {teamB.map((hero, i) => (
            <HeroCard
              key={i}
              hero={hero}
              isActive={turn?.team === "b" && turn?.hero_name === hero.name}
              isTargetable={!!waitingForTarget && hero.hp > 0}
              onTarget={handleTargetClick}
            />
          ))}
        </div>
      </div>

      {/* Battle log */}
      <div className="battle-log" ref={logRef}>
        <h3>Battle Log</h3>
        <div className="log-entries">
          {(battleState?.log || []).map((line, i) => (
            <p
              key={i}
              className={
                line.includes("defeated")
                  ? "log-defeat"
                  : line.includes("casts")
                    ? "log-cast"
                    : line.includes("healed")
                      ? "log-heal"
                      : line.includes("Round") || line.includes("===")
                        ? "log-round"
                        : "log-normal"
              }
            >
              {line}
            </p>
          ))}
        </div>
      </div>
    </div>
  );
}

export default BattleScreen;

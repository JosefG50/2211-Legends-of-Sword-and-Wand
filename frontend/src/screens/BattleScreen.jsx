function BattleScreen({ roomData, onFinished }) {
    return (
        <div className="inn-screen">
            <h1>⚔️ Battle Room</h1>
            <p>Room {roomData?.room_number ?? '?'}</p>
            <p>
                {roomData?.enemy_party?.length
                    ? `Enemies spotted: ${roomData.enemy_party.length}`
                    : 'No enemy data was returned.'}
            </p>
            <button className="primary-btn" onClick={onFinished}>
                Return To Campaign
            </button>
        </div>
    )
}

export default BattleScreen

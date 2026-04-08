from flask import Flask, request, jsonify
import database
import logic

app = Flask(__name__)

@app.route('/hero/create', methods=['POST'])
def create_hero():
    data = request.json
    username = data.get('username')
    hero_name = data.get('hero_name')
    initial_class = data.get('initial_class')

    if initial_class not in ["Order", "Chaos", "Warrior", "Mage"]:
        return jsonify({"error": "Invalid starting class"}), 400

    hero_id = database.create_hero_record(username, hero_name, initial_class)
    return jsonify({"message": "Hero created successfully", "hero_id": hero_id}), 201

@app.route('/hero/<hero_id>', methods=['GET'])
def get_hero(hero_id):
    hero_record = database.get_hero_record(hero_id)
    if not hero_record:
        return jsonify({"error": "Hero not found"}), 404

    calculated_data = logic.calculate_stats(hero_record)
    abilities = logic.get_abilities(hero_record['class_levels'], calculated_data['hybrid_class'])

    response_data = {
        "hero_id": hero_record['_id'],
        "hero_name": hero_record['hero_name'],
        "total_level": hero_record['total_level'],
        "current_xp": hero_record['xp'],
        "xp_to_next_level": logic.calculate_xp_required(hero_record['total_level'] + 1),
        "class_levels": hero_record['class_levels'],
        "stats": calculated_data['max_stats'],
        "status": {
            "is_hybrid": calculated_data['is_hybrid'],
            "class_title": calculated_data['hybrid_class'] or calculated_data['specialization'] or "Base",
        },
        "abilities": abilities
    }
    
    return jsonify(response_data), 200

@app.route('/hero/<hero_id>/level_up', methods=['POST'])
def level_up_hero(hero_id):
    data = request.json
    class_to_level = data.get('class_to_level')
    
    hero_record = database.get_hero_record(hero_id)
    if not hero_record:
        return jsonify({"error": "Hero not found"}), 404

    if hero_record['total_level'] >= 20:
        return jsonify({"error": "Hero is already at maximum level (20)"}), 400
    
    # Update levels
    new_total_level = hero_record['total_level'] + 1
    hero_record['class_levels'][class_to_level] += 1
    
    is_hybrid, hybrid_name, _ = logic.determine_classes(hero_record['class_levels'])

    database.update_hero_record(hero_id, {
        "total_level": new_total_level,
        "class_levels": hero_record['class_levels'],
        "is_hybrid": is_hybrid,
        "hybrid_class": hybrid_name
    })

    return jsonify({"message": f"Hero leveled up {class_to_level}!"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
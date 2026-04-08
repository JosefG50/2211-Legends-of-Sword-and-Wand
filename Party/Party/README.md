**Base URL:** `http://<host-ip>:5001` 
**Data Format:** `application/json`
### 1. Create a Hero

Initializes a new level 1 hero with base stats and a starting class.

- **Endpoint:** `/hero/create`
- **HTTP Method:** `POST`

**Input Data (JSON):** 
| Field | Type | Description | 
| :--- | :--- | :--- | 
| `username` | String | The account username creating the hero. | 
| `hero_name` | String | The chosen name for the hero. | 
| `initial_class` | String | Must be one of: `"Order"`, `"Chaos"`, `"Warrior"`, `"Mage"`. |

**Output Data (JSON):**

- **Success (201 Created):**
```JSON
{
  "message": "Hero created successfully",
  "hero_id": "64f1a2b3c4d5e6f7a8b9c0d1"
}
```

- **Error (400 Bad Request):**
```JSON
{
  "error": "Invalid starting class"
}
```

---
### 2. Get Hero Stats & Abilities

Statelessly calculates and retrieves a hero's current maximum stats, hybrid status, and available abilities based on their saved class levels.

- **Endpoint:** `/hero/<hero_id>`
- **HTTP Method:** `GET`

**Input Data:** * _URL Parameter:_ `hero_id` (String) - The MongoDB ObjectId of the hero.

**Output Data (JSON):**

- **Success (200 OK):**
```JSON
{
  "hero_id": "64f1a2b3c4d5e6f7a8b9c0d1",
  "hero_name": "Gandalf",
  "total_level": 1,
  "current_xp": 0,
  "xp_to_next_level": 595,
  "class_levels": {
    "Order": 0,
    "Chaos": 0,
    "Warrior": 0,
    "Mage": 1
  },
  "stats": {
    "attack": 6,
    "defense": 5,
    "hp": 100,
    "mana": 55
  },
  "status": {
    "is_hybrid": false,
    "class_title": "Base"
  },
  "abilities": [
    {
      "name": "Replenish",
      "mana_cost": 80,
      "type": "spell"
    }
  ]
}
```

- **Error (404 Not Found):**
```JSON
{
  "error": "Hero not found"
}
```

---

### 3. Level Up Hero

Increments a specific class level for the hero and recalculates hybrid/specialization status.

- **Endpoint:** `/hero/<hero_id>/level_up`
- **HTTP Method:** `POST`

**Input Data (JSON):** 
| Field | Type | Description | 
| :--- | :--- | :--- | 
| `class_to_level` | String | The class to increment: `"Order"`, `"Chaos"`, `"Warrior"`, or `"Mage"`. |

**Output Data (JSON):**

- **Success (200 OK):**
```JSON
{
  "message": "Hero leveled up Mage!"
}
```

- **Error (400 Bad Request):**
```JSON
{
  "error": "Hero is already at maximum level (20)"
}
```

- **Error (404 Not Found):**
```JSON
{
  "error": "Hero not found"
}
```

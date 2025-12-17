# Elevator Strategy Configuration Guide

## Overview

The `elevator_config.json` file allows you to tune the elevator system's behavior without modifying code. You can adjust scoring weights, traffic patterns, and simulation parameters.

## How to Use

1. **Edit** `elevator_config.json` with your desired values
2. **Run** the simulation - it will automatically load your config
3. **Experiment** with different values to see how behavior changes
4. **Compare** results using the statistics output

## Configuration Sections

### 🏢 Building Configuration

```json
"building": {
  "num_floors": 20,        // Total floors in building
  "num_elevators": 4,      // Number of elevators
  "elevator_capacity": 8,  // Max passengers per elevator
  "elevator_speed": 2.0    // Floors per second
}
```

**What to adjust:**

- More floors → longer wait times, need more elevators
- More elevators → better service but higher cost
- Higher capacity → fewer trips needed
- Faster speed → quicker service

---

### 🎯 Strategy Configuration (The Core!)

This is where you tune **how elevators are assigned** to requests.

```json
"strategy": {
  "distance_weight": 1.0,              // How much distance matters
  "full_penalty": 50,                  // Penalty for full elevators
  "same_direction_bonus": -10,         // Bonus for same direction
  "opposite_direction_penalty": 20,    // Penalty for opposite direction
  "load_factor_weight": 10,            // Weight for load balancing
  "idle_bonus": 0                      // Bonus for idle elevators
}
```

#### Scoring Formula

```
Final Score = (distance × distance_weight) 
            + (is_full ? full_penalty : 0)
            + (same_direction ? same_direction_bonus : 0)
            + (opposite_direction ? opposite_direction_penalty : 0)
            + (passenger_count/capacity × load_factor_weight)
            + (is_idle ? idle_bonus : 0)
```

**Lower score = better choice!**

#### Example Adjustments

**Scenario 1: Minimize Wait Time**

```json
{
  "distance_weight": 2.0,              // Strongly prefer nearest
  "same_direction_bonus": -20,         // Big bonus for same direction
  "opposite_direction_penalty": 50     // Heavy penalty for wrong direction
}
```

*Result: People get picked up faster, but elevators may be less efficient*

**Scenario 2: Maximize Efficiency**

```json
{
  "distance_weight": 0.5,              // Distance matters less
  "same_direction_bonus": -30,         // Heavily reward same direction
  "load_factor_weight": 5              // Prefer filling elevators
}
```

*Result: Better elevator utilization, but some people wait longer*

**Scenario 3: Balanced Load**

```json
{
  "distance_weight": 1.0,
  "load_factor_weight": 20,            // Strongly prefer empty elevators
  "same_direction_bonus": -5           // Small direction preference
}
```

*Result: Work is distributed evenly across all elevators*

---

### 🚶 Traffic Configuration

```json
"traffic": {
  "base_arrival_rate": 6.0,           // People/minute during normal hours
  "rush_multiplier": 3.0,             // 8-10am, 5-7pm
  "lunch_multiplier": 2.0,            // 12-2pm
  "night_multiplier": 0.2,            // 11pm-6am
  "enable_realistic_visitors": true   // Mall visitor pattern
}
```

**Adjustments for different scenarios:**

**Office Building:**

```json
{
  "rush_multiplier": 5.0,      // Heavy morning/evening rush
  "lunch_multiplier": 2.5,     // Moderate lunch traffic
  "night_multiplier": 0.0      // Empty at night
}
```

**Shopping Mall:**

```json
{
  "rush_multiplier": 1.5,              // Steady throughout day
  "lunch_multiplier": 2.0,             // Busier at lunch
  "enable_realistic_visitors": true    // People enter ground, visit, return
}
```

**Residential:**

```json
{
  "base_arrival_rate": 3.0,    // Lower overall traffic
  "rush_multiplier": 2.0,      // Moderate rush
  "night_multiplier": 0.5      // Some activity at night
}
```

---

### ⚙️ Simulation Parameters

```json
"simulation": {
  "control_loop_interval_ms": 100,      // How often elevator checks state
  "traffic_check_interval_s": 1.0,      // How often people are generated
  "movement_delay_factor": 0.5,         // Movement animation speed
  "stats_recording_interval_s": 10.0    // Stats snapshot frequency
}
```

**Performance tuning:**

- Smaller `control_loop_interval` → more responsive but higher CPU
- Larger `traffic_check_interval` → less traffic generation overhead

---

## Experimentation Ideas

### 1. **Test Different Building Sizes**

Try these combinations:

```json
Small office: {"num_floors": 10, "num_elevators": 2}
Medium mall:  {"num_floors": 20, "num_elevators": 4}
Skyscraper:   {"num_floors": 50, "num_elevators": 8}
```

Compare average wait times and throughput.

### 2. **Optimize for Specific Goals**

**Goal: Minimize Average Wait Time**

- Increase `distance_weight`
- Decrease `same_direction_bonus` (more negative)
- Add more elevators

**Goal: Maximize Throughput**

- Decrease `load_factor_weight`
- Increase `elevator_capacity`
- Increase `elevator_speed`

**Goal: Even Distribution**

- Increase `load_factor_weight`
- Set `idle_bonus` to negative value

### 3. **Stress Testing**

High traffic scenario:

```json
{
  "base_arrival_rate": 15.0,
  "rush_multiplier": 5.0
}
```

See how the system handles peak load!

---

## Advanced: Future Strategies

The config includes placeholders for advanced features you could implement:

```json
"advanced_strategies": {
  "enable_destination_dispatch": false,    // Modern elevator systems
  "enable_zoning": false,                  // Dedicated elevator zones
  "enable_predictive_positioning": false,  // AI-based positioning
  "enable_energy_optimization": false      // Green building mode
}
```

These are **not yet implemented** but show where you could extend the system!

---

## Comparing Configurations

To scientifically compare strategies:

1. **Run benchmark mode:**

   ```bash
   uv run main.py benchmark
   ```

2. **Record these metrics:**
   - Average wait time
   - Throughput (people/hour)
   - Elevator efficiency
   - Total distance traveled

3. **Modify one parameter at a time**

4. **Document your findings**

---

## Quick Reference: Common Adjustments

| Goal | Parameters to Change |
|------|---------------------|
| Faster response | ↑ `distance_weight`, ↓ `same_direction_bonus` |
| Better efficiency | ↓ `distance_weight`, ↑ `same_direction_bonus` |
| Load balancing | ↑ `load_factor_weight` |
| Handle rush hours | ↑ `rush_multiplier`, ↑ `num_elevators` |
| Realistic mall | `enable_realistic_visitors: true` |
| Faster elevators | ↑ `elevator_speed` |
| More capacity | ↑ `elevator_capacity` |

---

## Tips for Experimentation

1. **Start with defaults** - understand baseline behavior
2. **Change one thing** - isolate effects
3. **Run multiple times** - randomness affects results
4. **Look at trends** - not just single numbers
5. **Consider tradeoffs** - speed vs efficiency vs cost

Happy experimenting! 🚀

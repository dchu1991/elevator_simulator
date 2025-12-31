# Migration Guide: Transitioning to Dependency Injection

This guide outlines the step-by-step process to migrate the existing codebase to use the new Dependency Injection system.

## Current Status

✅ **Phase 1 Complete**: Foundation implemented

- Interfaces and protocols defined
- Strategy pattern implemented
- DI container created
- Tests and documentation complete

🔄 **Phase 2 Pending**: Core refactoring needed

## Migration Strategy

### Incremental Approach

We'll migrate incrementally to avoid breaking the system:

1. **Add DI support** while keeping old code working
2. **Test both approaches** in parallel
3. **Gradually transition** calling code
4. **Remove old code** once migration complete

## Phase 2: Core Refactoring

### Step 1: Refactor Building Class

**File**: `src/core/elevator_simulator.py`

#### Current Code

```python
class Building:
    def __init__(self, num_floors, num_elevators, ...):
        self.config = get_config()  # Singleton
        # ... rest of init
    
    def assign_elevator_to_request(self, floor, direction):
        # Hardcoded scoring logic in Elevator.score()
        scores = []
        for elevator in self.elevators:
            score = elevator.score(floor, direction, self.config)
            scores.append(score)
        
        best_idx = scores.index(min(scores))
        return best_idx
```

#### New Code (Backward Compatible)

```python
class Building:
    def __init__(self, num_floors, num_elevators, ..., 
                 config: Optional[ElevatorConfig] = None,
                 strategy: Optional[ElevatorAssignmentStrategy] = None):
        # Support both old and new approaches
        self.config = config if config else get_config()
        self.strategy = strategy if strategy else NearestCarStrategy()
        # ... rest of init
    
    def assign_elevator_to_request(self, floor, direction):
        # Use injected strategy instead of hardcoded logic
        return self.strategy.assign_elevator(
            self.elevators, floor, direction, self.config
        )
```

#### Changes Required

1. Add optional `config` and `strategy` parameters (default to old behavior)
2. Replace hardcoded assignment logic with strategy call
3. Move `Elevator.score()` logic into `NearestCarStrategy` (if not already)

#### Testing

```python
def test_building_with_di():
    """Test Building with DI"""
    config = ElevatorConfig(num_floors=10, num_elevators=2)
    strategy = RoundRobinStrategy()
    
    building = Building(
        num_floors=10, 
        num_elevators=2,
        config=config,
        strategy=strategy
    )
    
    # Test uses RoundRobin instead of Nearest
    assert building.strategy == strategy

def test_building_backward_compatible():
    """Test Building still works without DI"""
    building = Building(num_floors=10, num_elevators=2)
    
    # Should use defaults (get_config() and NearestCarStrategy)
    assert isinstance(building.strategy, NearestCarStrategy)
```

### Step 2: Refactor SimulationEngine

**File**: `src/core/simulation_engine.py`

#### Current Code

```python
class SimulationEngine:
    def __init__(self, num_floors=20, num_elevators=4, time_scale=1.0):
        self.config = get_config()  # Singleton
        self.building = Building(num_floors, num_elevators)
        # ... rest of init
```

#### New Code (Backward Compatible)

```python
class SimulationEngine:
    def __init__(self, num_floors=20, num_elevators=4, time_scale=1.0,
                 config: Optional[ElevatorConfig] = None,
                 strategy: Optional[ElevatorAssignmentStrategy] = None):
        # Support both old and new approaches
        self.config = config if config else get_config()
        
        # Create building with DI if available
        self.building = Building(
            num_floors, 
            num_elevators,
            config=self.config,
            strategy=strategy
        )
        # ... rest of init
```

#### Changes Required

1. Add optional `config` and `strategy` parameters
2. Pass them to Building constructor
3. Use `self.config` instead of `get_config()` throughout

#### Testing

```python
def test_simulation_engine_with_di():
    """Test SimulationEngine with DI"""
    container = create_test_container(
        strategy_name='scan',
        config_overrides={'num_floors': 10, 'elevator_speed': 10.0}
    )
    
    config = container.resolve('config')
    strategy = container.resolve('strategy')
    
    sim = SimulationEngine(
        num_floors=10,
        num_elevators=2,
        config=config,
        strategy=strategy
    )
    
    assert sim.config == config
    assert sim.building.strategy == strategy
```

### Step 3: Update Calling Code

Gradually update code that creates SimulationEngine:

#### main.py

```python
# Before
def run_simulation_mode(args):
    sim = SimulationEngine(
        num_floors=args.floors,
        num_elevators=args.elevators
    )

# After (optional DI)
def run_simulation_mode(args, strategy_name='nearest'):
    container = create_test_container(
        strategy_name=strategy_name,
        config_overrides={
            'num_floors': args.floors,
            'num_elevators': args.elevators,
        }
    )
    
    config = container.resolve('config')
    strategy = container.resolve('strategy')
    
    sim = SimulationEngine(
        num_floors=args.floors,
        num_elevators=args.elevators,
        config=config,
        strategy=strategy
    )
```

#### visualization.py

```python
# Before
def run_visual_simulation(num_floors, num_elevators):
    sim = SimulationEngine(num_floors, num_elevators, time_scale=0.5)

# After
def run_visual_simulation(num_floors, num_elevators, strategy_name='nearest'):
    container = create_test_container(
        strategy_name=strategy_name,
        config_overrides={
            'num_floors': num_floors,
            'num_elevators': num_elevators,
        }
    )
    
    config = container.resolve('config')
    strategy = container.resolve('strategy')
    
    sim = SimulationEngine(
        num_floors, num_elevators, 
        time_scale=0.5,
        config=config,
        strategy=strategy
    )
```

### Step 4: Add CLI Options for Strategy Selection

Add command-line option to select strategy:

```python
# main.py
parser = argparse.ArgumentParser()
# ... existing arguments ...
parser.add_argument(
    '--strategy', '-s',
    choices=['nearest', 'scan', 'round_robin'],
    default='nearest',
    help='Elevator assignment strategy'
)

def main():
    args = parser.parse_args()
    
    # Use selected strategy
    if args.mode == 'visual':
        run_visual_simulation(
            args.floors, 
            args.elevators,
            strategy_name=args.strategy  # Pass strategy
        )
```

## Testing Strategy

### 1. Unit Tests

Test each component with DI:

```python
# Test Building with different strategies
def test_building_nearest_strategy():
    config = ElevatorConfig(num_floors=10)
    strategy = NearestCarStrategy()
    building = Building(10, 3, config=config, strategy=strategy)
    # ... test ...

def test_building_scan_strategy():
    config = ElevatorConfig(num_floors=10)
    strategy = SCANStrategy()
    building = Building(10, 3, config=config, strategy=strategy)
    # ... test ...
```

### 2. Integration Tests

Test end-to-end with DI:

```python
def test_full_simulation_with_di():
    """Test complete simulation with DI"""
    container = create_test_container(
        strategy_name='round_robin',
        config_overrides={'num_floors': 5, 'elevator_speed': 10.0}
    )
    
    config = container.resolve('config')
    strategy = container.resolve('strategy')
    
    sim = SimulationEngine(
        num_floors=5,
        num_elevators=2,
        config=config,
        strategy=strategy
    )
    
    with sim:
        time.sleep(10)  # Run for 10 seconds
        stats = sim.get_current_statistics()
        
    assert stats['total_generated'] > 0
    assert stats['total_completed'] > 0
```

### 3. Regression Tests

Ensure old behavior still works:

```python
def test_backward_compatibility():
    """Ensure old code still works"""
    # Should work without DI
    sim = SimulationEngine(num_floors=10, num_elevators=2)
    
    with sim:
        time.sleep(5)
        stats = sim.get_current_statistics()
    
    # Should behave same as before
    assert stats is not None
```

## Migration Checklist

### Phase 2.1: Building Refactoring

- [ ] Add optional `config` and `strategy` parameters to Building
- [ ] Replace hardcoded assignment with strategy call
- [ ] Move Elevator.score() logic to NearestCarStrategy
- [ ] Add tests for Building with DI
- [ ] Verify backward compatibility

### Phase 2.2: SimulationEngine Refactoring  

- [ ] Add optional `config` and `strategy` parameters
- [ ] Pass dependencies to Building
- [ ] Replace get_config() calls with self.config
- [ ] Add tests for SimulationEngine with DI
- [ ] Verify backward compatibility

### Phase 2.3: Update Calling Code

- [ ] Update main.py to support DI (optional)
- [ ] Update visualization.py
- [ ] Update pygame_visualization.py
- [ ] Update demos/ scripts
- [ ] Add CLI option for strategy selection

### Phase 2.4: Testing & Validation

- [ ] Run full test suite (all tests pass)
- [ ] Manual testing of all modes
- [ ] Performance testing (no regression)
- [ ] Documentation updates

### Phase 2.5: Cleanup

- [ ] Add deprecation warnings for non-DI usage
- [ ] Update all examples to use DI
- [ ] Update README with DI examples
- [ ] Remove deprecated code (future)

## Timeline Estimate

| Phase | Tasks | Estimated Time |
|-------|-------|----------------|
| 2.1 Building | Refactor + tests | 2-3 hours |
| 2.2 SimulationEngine | Refactor + tests | 2-3 hours |
| 2.3 Calling Code | Update all callers | 1-2 hours |
| 2.4 Testing | Comprehensive testing | 1-2 hours |
| 2.5 Cleanup | Documentation + cleanup | 1 hour |
| **Total** | | **7-11 hours** |

## Risk Mitigation

### Risk: Breaking Existing Code

**Mitigation**:

- Use optional parameters (backward compatible)
- Keep old code path working
- Comprehensive regression tests

### Risk: Performance Degradation

**Mitigation**:

- DI has zero runtime overhead (setup once)
- Benchmark before/after
- Profile hot paths

### Risk: Incomplete Migration

**Mitigation**:

- Incremental approach (can stop anytime)
- Each phase independently valuable
- Document migration status

## Benefits After Migration

### Immediate Benefits

- ✅ Can test with different strategies easily
- ✅ Can inject fast test configurations
- ✅ Better separation of concerns
- ✅ Easier to add new strategies

### Long-term Benefits

- ✅ Reduced coupling
- ✅ Improved testability
- ✅ Easier maintenance
- ✅ Better extensibility

## Example: Before vs After

### Before (Current)

```python
# Hard to test, tightly coupled
sim = SimulationEngine(num_floors=20, num_elevators=4)
# Uses singleton config
# Uses hardcoded assignment algorithm
# Can't swap strategies
```

### After (With DI)

```python
# Easy to test, loosely coupled
container = create_test_container(
    strategy_name='scan',  # Choose strategy
    config_overrides={'elevator_speed': 10.0}  # Fast for testing
)

config = container.resolve('config')
strategy = container.resolve('strategy')

sim = SimulationEngine(
    num_floors=20, 
    num_elevators=4,
    config=config,  # Injected
    strategy=strategy  # Injected
)

# Can easily swap to different strategy
# Can inject test configurations
# Clear dependencies
```

## Next Steps

1. **Review this guide** with the team
2. **Create feature branch** for DI migration
3. **Start with Phase 2.1** (Building refactoring)
4. **Test thoroughly** after each phase
5. **Merge when stable**

## Questions?

See:

- [DI Architecture](DI_ARCHITECTURE.md) - Visual diagrams
- [DI Guide](DEPENDENCY_INJECTION.md) - Complete documentation
- [DI Quick Start](DI_QUICKSTART.md) - Quick reference
- [DI Examples](../examples/dependency_injection_demo.py) - Working code
- [DI Tests](../tests/test_dependency_injection.py) - Test examples

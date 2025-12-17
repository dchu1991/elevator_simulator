# How to Use Interactive Mode 🎮

## Starting Interactive Mode

```bash
# Basic interactive mode
uv run main.py interactive

# Custom building size
uv run main.py interactive --floors 10 --elevators 2
```

## What You'll See

When you start interactive mode, you'll see:

1. **ASCII Building Display** - Real-time view of elevators and people
2. **Statistics Dashboard** - Live performance metrics
3. **Command Prompt** - Where you enter commands

## Interactive Commands

Once the simulation starts, you can use these commands:

### **Main Commands:**

- **`q`** - Quit the simulation
- **`a`** - Add a manual elevator request (spawn a person)
- **`r`** - Show detailed performance report
- **`s`** - Show trend analysis and statistics
- **`h`** - Show help and display legend

## How to Add People (Most Fun Part!)

1. Type **`a`** and press Enter
2. Enter **from floor** (e.g., `1`)
3. Enter **to floor** (e.g., `8`)
4. Watch the elevator system respond!

**Example:**

```
Command: a
From floor (1-10): 1
To floor (1-10): 8
Added request: Floor 1 → Floor 8
```

## Understanding the Display

### **Elevator Symbols:**

- **`[↑2/8]`** - Elevator going UP with 2/8 passengers
- **`[↓5/8]`** - Elevator going DOWN with 5/8 passengers  
- **`[○3/8]`** - Elevator IDLE with 3/8 passengers
- **`[◆4/8]`** - Elevator LOADING with 4/8 passengers

### **Floor Indicators:**

- **`↑3 ↓2`** - 3 people waiting to go UP, 2 waiting DOWN
- **`◇`** - Floor has pending elevator request
- **`│`** - Empty elevator shaft

### **Example Display:**

```
Floor Elev1    Elev2  
------------------
 8:     │        │    
 7:     │        │    
 6:     │     [↑1/6]  
 5:     │        │    
 4:  [↓3/8]     │    
 3:     │        │     ↑2
 2:     │        │    
 1:     │        │     ↓1
```

## Fun Things to Try

1. **Create Rush Hour:**
   - Add multiple requests from floor 1 going up
   - Add requests from top floors going down

2. **Test Efficiency:**
   - Add many requests and watch how elevators coordinate
   - Check the performance report with `r`

3. **Challenge the System:**
   - Add requests that require elevators to change direction
   - Fill up elevators to capacity

4. **Monitor Performance:**
   - Use `s` to see if wait times are improving or getting worse
   - Use `r` for detailed efficiency reports

## Example Session

```bash
uv run main.py interactive --floors 6 --elevators 2

# You'll see the building display
# Then type commands:

Command: a
From floor (1-6): 1
To floor (1-6): 5

Command: a  
From floor (1-6): 3
To floor (1-6): 6

Command: a
From floor (1-6): 5
To floor (1-6): 1

Command: r  # See performance report

Command: s  # See trends

Command: q  # Quit when done
```

## Tips

- **Watch the elevators move** - You'll see them pick up and drop off passengers
- **Try adding conflicting requests** - See how the system optimizes
- **Use small buildings first** (6-8 floors) to understand the system
- **The simulation keeps generating automatic traffic** too
- **Press Ctrl+C anytime** to force quit if needed

Have fun experimenting with the elevator system! 🚀

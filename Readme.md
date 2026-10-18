# Terminal Task Manager

A command-line task management application built in Python with JSON persistence and deadline tracking.

---

## 1. How to Run the Program

### Requirements
- **Python 3.10+** (uses structural pattern matching `match/case`).
- Standard library modules only (`collections`, `datetime`, `json`, `os`, `sys`). No external installations needed.

### Execution
1. Navigate to the project directory:
   ```bash
   cd /path/to/project
   ```
2. Run the application:
   ```bash
   python3 task_manager.py
   ```
3. Enter a number from `1` to `8` to interact with the menu.

---

## 2. Features Implemented

1. **Add a Task**: Prompts for task name, deadline (`DD-MM-YYYY` or `DD-MM-YYYY HH:MM`), priority (`LOW`, `MEDIUM`, `HIGH`), and category. Automatically assigns a unique numeric ID and persists to `tasks.json`.
2. **View Tasks**: Displays tasks in a clear card format showing ID, Name, Category, Priority, Deadline, and real-time status:
   - `[v] COMPLETED`: Completed by user.
   - `[!] OVERDUE`: Deadline has passed and task is pending.
   - `[o] UPCOMING`: Deadline is in the future.
3. **Update a Task**: Selectively edit Name, Deadline, Priority, Category, or toggle completion status (`COMPLETED` / `PENDING`). Pressing `Enter` keeps the existing value.
4. **Delete a Task**: Prompts for task ID with an interactive confirmation prompt before deletion.
5. **Search for a Task**: Case-insensitive search across task name, category, priority, and computed status using list comprehension.
6. **Automatic Persistence**: Automatically loads data from `tasks.json` at startup and flushes changes to disk on every modification and exit.

---

## 3. Explanation of 2 Additional Features

### Feature 1: Priority Levels, Multi-Criteria Filtering & Custom Sorting
- **Priority Assignment**: Tasks are tagged as `HIGH`, `MEDIUM`, or `LOW` to distinguish urgency.
- **Multi-Criteria Filtering**: Filter active tasks by status (`All`, `Overdue Only`, `Upcoming Only`, `Completed Only`) combined with priority level (`All`, `High`, `Medium`, `Low`).
- **Custom Sorting**: Sort tasks using custom key functions by:
  - Earliest Deadline (Ascending)
  - Latest Deadline (Descending)
  - Priority Rank (`HIGH` -> `MEDIUM` -> `LOW`)
  - Numeric Task ID (Default)

### Feature 2: Task Analytics & Urgent Deadline Alert Dashboard
- **Summary Metrics**: Uses `collections.Counter` to calculate total tasks, completion percentage, active vs. overdue counts, and priority/category distributions in $O(n)$ time.
- **48-Hour Deadline Alert**: Evaluates active upcoming tasks against `datetime.now() + timedelta(hours=48)` to highlight items due within the next two days, preventing tasks from slipping into overdue status.

---

## 4. Challenges or Problems Faced

1. **Dynamic vs. Stored Status**: Storing "OVERDUE" or "UPCOMING" statically in JSON causes data to become stale when the app is closed. *Solution*: Stored only a boolean `completed` flag and target deadline, calculating status dynamically against `datetime.now()` at runtime.
2. **Data Loss from Malformed JSON**: A corrupted file or non-dictionary root (e.g. `[]`) would cause generic crash handlers to return an empty dictionary and overwrite the file on next save. *Solution*: Caught both `json.JSONDecodeError` and `ValueError`, prompting the user before creating a timestamped backup (`.corrupt.TIMESTAMP`) to prevent data loss.
3. **Unterminated Terminal Sessions**: Pressing `Ctrl+C` or `Ctrl+D` at prompts caused unhandled `KeyboardInterrupt` or `EOFError` crashes. *Solution*: Wrapped the main event loop in `except (KeyboardInterrupt, EOFError):` to flush pending state and exit gracefully.

---

## 5. Program Structure

The application is organized into modular functional layers:

```
task_manager.py
├── Module Docstring & __future__ import annotations
├── Module Constants (Data file, date formats, priority/status tuples)
├── Helper & Validation Layer
│   ├── parse_deadline()      # Validates DD-MM-YYYY [HH:MM]
│   ├── format_deadline()     # Standardizes datetime strings
│   ├── get_task_status()     # Evaluates COMPLETED / OVERDUE / UPCOMING
│   └── generate_next_id()    # Computes unique sequential integer ID
├── Persistence Layer
│   ├── load_tasks()          # Loads JSON, validates schema, handles corruption
│   └── save_tasks()          # Serializes dictionary to tasks.json
├── Core Operations (CRUD & Search)
│   ├── add_task()            # Validated task creation & auto-save
│   ├── view_tasks()          # Iterates and displays tasks in card layout
│   ├── display_task_row()    # Formats individual task card
│   ├── update_task()         # Field-by-field selective editing
│   ├── delete_task()         # Safe task removal with confirmation
│   └── search_tasks()        # Filtered retrieval via list comprehension
├── Additional Features
│   ├── filter_and_sort_tasks() # Multi-criteria filtering & custom lambda sort
│   └── display_statistics()    # Metrics summary & 48-hour alert window
└── Execution Layer
    ├── print_main_menu()     # Renders options
    └── main()                # App loop, match/case routing, interrupt safety
```
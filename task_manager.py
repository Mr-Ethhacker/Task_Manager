"""Terminal Task Manager.

A robust command-line task management application built in Python.
Demonstrates foundational and intermediate Python concepts:
- Data structures: Lists, Dictionaries, Sets, Tuples
- Control flow: while loops, for loops, if/elif/else, match/case
- Functions, scope, parameters, return values
- File handling, JSON serialization/deserialization
- Exception handling: try, except, finally, raise
- Standard libraries: datetime, os, collections
"""

from __future__ import annotations

import collections
from datetime import datetime, timedelta
import json
import os
import sys

DEFAULT_DATA_FILE = "tasks.json"
DATE_FORMAT = "%d-%m-%Y %H:%M"

VALID_PRIORITIES = ("LOW", "MEDIUM", "HIGH")
PRIORITY_ORDER = {"HIGH": 1, "MEDIUM": 2, "LOW": 3}

STATUS_OVERDUE = "OVERDUE"
STATUS_UPCOMING = "UPCOMING"
STATUS_COMPLETED = "COMPLETED"
VALID_STATUSES = (STATUS_OVERDUE, STATUS_UPCOMING, STATUS_COMPLETED)


def parse_deadline(date_str: str) -> datetime:
    clean_str = date_str.strip()
    if not clean_str:
        raise ValueError("Deadline string cannot be empty.")

    try:
        return datetime.strptime(clean_str, DATE_FORMAT)
    except ValueError:
        pass

    try:
        dt = datetime.strptime(clean_str, "%d-%m-%Y")
        return dt.replace(hour=23, minute=59)
    except ValueError:
        raise ValueError(
            f"Invalid deadline '{date_str}'. Expected format: DD-MM-YYYY or DD-MM-YYYY HH:MM."
        )


def format_deadline(dt: datetime) -> str:
    return dt.strftime(DATE_FORMAT)


def get_task_status(task: dict, current_time: datetime | None = None) -> str:
    if task.get("completed", False):
        return STATUS_COMPLETED

    if current_time is None:
        current_time = datetime.now()

    deadline_str = task.get("deadline", "")
    try:
        deadline_dt = parse_deadline(deadline_str)
        status = STATUS_OVERDUE if deadline_dt < current_time else STATUS_UPCOMING
        return status if status in VALID_STATUSES else "UNKNOWN"
    except ValueError:
        return "UNKNOWN"


def generate_next_id(tasks: dict) -> int:
    if not tasks:
        return 1
    existing_ids = {int(k) for k in tasks.keys() if str(k).isdigit()}
    return max(existing_ids, default=0) + 1


def load_tasks(file_path: str = DEFAULT_DATA_FILE) -> dict:
    print(f"\n[Storage] Checking data file '{file_path}'...")
    if not os.path.exists(file_path):
        print(f"[Storage] File '{file_path}' not found. Initializing new task database.")
        save_tasks({}, file_path)
        return {}

    if os.path.getsize(file_path) == 0:
        print(f"[Storage] File '{file_path}' is empty. Starting with empty tasks.")
        return {}

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            raise ValueError("Corrupted JSON: root element must be a dictionary.")

        normalized_tasks = {}
        for k, v in data.items():
            if isinstance(v, dict) and "name" in v and "deadline" in v:
                raw_priority = str(v.get("priority", "MEDIUM")).upper()
                validated_priority = raw_priority if raw_priority in VALID_PRIORITIES else "MEDIUM"

                normalized_tasks[str(k)] = {
                    "name": str(v.get("name", "")).strip(),
                    "deadline": str(v.get("deadline", "")).strip(),
                    "completed": bool(v.get("completed", False)),
                    "priority": validated_priority,
                    "category": str(v.get("category", "General")).strip(),
                }
            else:
                print(f"[Warning] Skipping malformed task entry with ID: {k}")

        print(f"[Storage] Successfully loaded {len(normalized_tasks)} task(s).\n")
        return normalized_tasks

    except (json.JSONDecodeError, ValueError) as decode_err:
        print(f"\n[Error] Invalid or corrupted data in '{file_path}': {decode_err}")
        print("[Storage] The file appears corrupted or has an invalid structure.")
        try:
            choice = input("Would you like to reset to a clean database? (yes/no): ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\n[Storage] Aborting program startup.")
            sys.exit(1)

        if choice in ("yes", "y"):
            backup_path = f"{file_path}.corrupt.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            try:
                os.rename(file_path, backup_path)
                print(f"[Storage] Renamed corrupt file to '{backup_path}'.")
            except OSError as os_err:
                print(f"[Storage] Could not rename corrupted file: {os_err}")
            save_tasks({}, file_path)
            return {}
        else:
            print("[Storage] Aborting program startup to prevent data loss.")
            sys.exit(1)

    except Exception as e:
        print(f"[Error] Unexpected error while loading tasks: {e}")
        return {}

    finally:
        print("[Storage] Load step finished.")


def save_tasks(tasks: dict, file_path: str = DEFAULT_DATA_FILE) -> bool:
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(tasks, f, indent=4)
        return True
    except OSError as err:
        print(f"[Error] Failed to save tasks to '{file_path}': {err}")
        return False


def add_task(tasks: dict, file_path: str = DEFAULT_DATA_FILE) -> bool:
    print("\n\nADD NEW TASK\n")

    task_name = input("Enter Task Name: ").strip()
    if not task_name:
        print("[Validation Error] Task name cannot be empty!\n")
        return False

    print("Enter Deadline format: DD-MM-YYYY or DD-MM-YYYY HH:MM (e.g., 15-10-2026 18:00)")
    deadline_input = input("Deadline: ").strip()
    try:
        parsed_dt = parse_deadline(deadline_input)
    except ValueError as err:
        print(f"[Validation Error] {err}\n")
        return False

    formatted_deadline = format_deadline(parsed_dt)

    print("Select Priority (1: LOW, 2: MEDIUM, 3: HIGH) [Default: 2 = MEDIUM]:")
    priority_choice = input("Choice: ").strip()
    priority_map = {"1": "LOW", "2": "MEDIUM", "3": "HIGH"}
    priority = priority_map.get(priority_choice, "MEDIUM")

    category_input = input("Enter Category / Tag (e.g. Work, Study, Personal) [Default: General]: ").strip()
    category = category_input.title() if category_input else "General"

    new_id = str(generate_next_id(tasks))

    tasks[new_id] = {
        "name": task_name,
        "deadline": formatted_deadline,
        "completed": False,
        "priority": priority,
        "category": category,
    }

    save_tasks(tasks, file_path)
    print(f"\n[Success] Task #{new_id} '{task_name}' successfully added and saved!\n")
    return True


def display_task_row(task_id: str, task: dict, current_time: datetime):
    status = get_task_status(task, current_time)
    name = task.get("name", "N/A")
    deadline = task.get("deadline", "N/A")
    priority = task.get("priority", "MEDIUM")
    category = task.get("category", "General")

    if status == STATUS_OVERDUE:
        status_indicator = "[!] OVERDUE"
    elif status == STATUS_COMPLETED:
        status_indicator = "[v] COMPLETED"
    else:
        status_indicator = "[o] UPCOMING"

    print(f"Task ID   : {task_id}")
    print(f"Name      : {name}")
    print(f"Category  : {category}")
    print(f"Priority  : {priority}")
    print(f"Deadline  : {deadline}")
    print(f"Status    : {status_indicator}\n")


def view_tasks(tasks: dict, filtered_list: list = None, header_title: str = "ALL TASKS"):
    total_count = len(filtered_list) if filtered_list is not None else len(tasks)
    print(f"\n\n{header_title} (Total: {total_count})\n")

    current_time = datetime.now()

    items_to_display = []
    if filtered_list is not None:
        items_to_display = filtered_list
    else:
        items_to_display = sorted(
            tasks.items(),
            key=lambda x: int(x[0]) if x[0].isdigit() else str(x[0])
        )

    if not items_to_display:
        print("No tasks found to display.\n")
        return

    for task_id, task in items_to_display:
        display_task_row(str(task_id), task, current_time)


def update_task(tasks: dict, file_path: str = DEFAULT_DATA_FILE) -> bool:
    print("\n\nUPDATE TASK\n")

    if not tasks:
        print("[Info] No tasks available to update.\n")
        return False

    task_id_input = input("Enter Task ID to update: ").strip()
    if task_id_input not in tasks:
        print(f"[Error] Task ID '{task_id_input}' does not exist.\n")
        return False

    task = tasks[task_id_input]
    print(f"\nEditing Task #{task_id_input}: '{task['name']}'")
    print("Leave field blank and press [Enter] to keep current value.\n")

    new_name = input(f"New Name [{task['name']}]: ").strip()
    if new_name:
        task["name"] = new_name

    current_deadline = task.get("deadline", "")
    new_deadline_input = input(f"New Deadline [{current_deadline}]: ").strip()
    if new_deadline_input:
        try:
            parsed_dt = parse_deadline(new_deadline_input)
            task["deadline"] = format_deadline(parsed_dt)
        except ValueError as err:
            print(f"[Error] Invalid deadline format ({err}). Deadline not modified.")

    current_priority = task.get("priority", "MEDIUM")
    print(f"New Priority (1: LOW, 2: MEDIUM, 3: HIGH) [Current: {current_priority}]:")
    priority_choice = input("Choice: ").strip()
    priority_map = {"1": "LOW", "2": "MEDIUM", "3": "HIGH"}
    if priority_choice in priority_map:
        task["priority"] = priority_map[priority_choice]

    current_cat = task.get("category", "General")
    new_cat = input(f"New Category [{current_cat}]: ").strip()
    if new_cat:
        task["category"] = new_cat.title()

    current_comp = "COMPLETED" if task.get("completed", False) else "PENDING"
    toggle = input(f"Toggle completion status? Currently [{current_comp}]. (y/N): ").strip().lower()
    if toggle in ("y", "yes"):
        task["completed"] = not task.get("completed", False)
        new_state = "COMPLETED" if task["completed"] else "PENDING"
        print(f"[Update] Status toggled to: {new_state}")

    save_tasks(tasks, file_path)
    print(f"\n[Success] Task #{task_id_input} updated and saved successfully!\n")
    return True


def delete_task(tasks: dict, file_path: str = DEFAULT_DATA_FILE) -> bool:
    print("\n\nDELETE TASK\n")

    if not tasks:
        print("[Info] No tasks available to delete.\n")
        return False

    task_id_input = input("Enter Task ID to delete: ").strip()
    if task_id_input not in tasks:
        print(f"[Error] Task with ID '{task_id_input}' not found.\n")
        return False

    task_name = tasks[task_id_input].get("name", "Unknown")
    confirm = input(f"Are you sure you want to delete Task #{task_id_input} ('{task_name}')? (yes/no): ").strip().lower()
    if confirm in ("yes", "y"):
        deleted_task = tasks.pop(task_id_input)
        save_tasks(tasks, file_path)
        print(f"\n[Success] Task #{task_id_input} '{deleted_task['name']}' was permanently removed.\n")
        return True
    else:
        print("[Action Cancelled] Task was not deleted.\n")
        return False


def search_tasks(tasks: dict):
    print("\n\nSEARCH TASKS\n")

    if not tasks:
        print("[Info] No tasks available to search.\n")
        return

    query = input("Enter search keyword (name, category, or status): ").strip().lower()
    if not query:
        print("[Error] Search query cannot be empty.\n")
        return

    current_time = datetime.now()

    matching_tasks = [
        (task_id, task)
        for task_id, task in tasks.items()
        if (
            query in task.get("name", "").lower()
            or query in task.get("category", "").lower()
            or query == get_task_status(task, current_time).lower()
            or query == task.get("priority", "").lower()
        )
    ]

    if matching_tasks:
        view_tasks(tasks, filtered_list=matching_tasks, header_title=f"SEARCH RESULTS FOR '{query}'")
    else:
        print(f"\n[Info] No tasks matched the search term '{query}'.\n")


def filter_and_sort_tasks(tasks: dict):
    print("\n\nFILTER AND SORT TASKS\n")

    if not tasks:
        print("[Info] No tasks available to filter.\n")
        return

    current_time = datetime.now()

    print("Filter by Status:")
    print("1. All Tasks")
    print("2. Overdue Only")
    print("3. Upcoming Only")
    print("4. Completed Only\n")
    status_choice = input("Select status option (1-4) [Default: 1]: ").strip()

    status_filter_map = {
        "2": STATUS_OVERDUE,
        "3": STATUS_UPCOMING,
        "4": STATUS_COMPLETED,
    }
    selected_status = status_filter_map.get(status_choice, None)

    print("\nFilter by Priority:")
    print("1. All Priorities")
    print("2. High")
    print("3. Medium")
    print("4. Low\n")
    priority_choice = input("Select priority option (1-4) [Default: 1]: ").strip()
    priority_filter_map = {"2": "HIGH", "3": "MEDIUM", "4": "LOW"}
    selected_priority = priority_filter_map.get(priority_choice, None)

    filtered_items = []
    for task_id, task in tasks.items():
        task_status = get_task_status(task, current_time)
        task_priority = task.get("priority", "MEDIUM")

        if selected_status and task_status != selected_status:
            continue
        if selected_priority and task_priority != selected_priority:
            continue

        filtered_items.append((task_id, task))

    print("\nSort by:")
    print("1. Deadline (Earliest first")
    print("2. Deadline (Latest first")
    print("3. Priority (High to Medium to Low)")
    print("4. Task ID (Default)\n")
    sort_choice = input("Select sort option (1-4) [Default: 1]: ").strip()

    def get_sort_key_deadline(item):
        try:
            return parse_deadline(item[1].get("deadline", "31-12-9999 23:59"))
        except ValueError:
            return datetime.max

    if sort_choice == "2":
        filtered_items.sort(key=get_sort_key_deadline, reverse=True)
    elif sort_choice == "3":
        filtered_items.sort(key=lambda x: PRIORITY_ORDER.get(x[1].get("priority", "LOW"), 4))
    elif sort_choice == "4":
        filtered_items.sort(key=lambda x: int(x[0]) if str(x[0]).isdigit() else str(x[0]))
    else:
        filtered_items.sort(key=get_sort_key_deadline)

    view_tasks(tasks, filtered_list=filtered_items, header_title="FILTERED AND SORTED TASKS")


def display_statistics(tasks: dict):
    print("\n\nTASK ANALYTICS AND DASHBOARD\n")

    total_tasks = len(tasks)
    if total_tasks == 0:
        print("[Info] No tasks recorded. Add tasks to view statistics.\n")
        return

    current_time = datetime.now()

    status_counter = collections.Counter()
    priority_counter = collections.Counter()
    category_counter = collections.Counter()

    urgent_upcoming = []
    threshold_48h = current_time + timedelta(hours=48)

    for task_id, task in tasks.items():
        st = get_task_status(task, current_time)
        pr = task.get("priority", "MEDIUM")
        cat = task.get("category", "General")

        status_counter[st] += 1
        priority_counter[pr] += 1
        category_counter[cat] += 1

        if st == STATUS_UPCOMING:
            try:
                deadline_dt = parse_deadline(task.get("deadline", ""))
                if current_time <= deadline_dt <= threshold_48h:
                    urgent_upcoming.append((task_id, task["name"], task["deadline"]))
            except ValueError:
                pass

    completed_count = status_counter[STATUS_COMPLETED]
    overdue_count = status_counter[STATUS_OVERDUE]
    upcoming_count = status_counter[STATUS_UPCOMING]

    completion_rate = (completed_count / total_tasks) * 100

    print(f"Total Tasks Managed    : {total_tasks}")
    print(f"Completed Tasks        : {completed_count} ({completion_rate:.1f}%)")
    print(f"Upcoming Tasks         : {upcoming_count}")
    print(f"Overdue Tasks          : {overdue_count}\n")

    print("Priority Breakdown:")
    print(f"  HIGH    : {priority_counter['HIGH']} task(s)")
    print(f"  MEDIUM  : {priority_counter['MEDIUM']} task(s)")
    print(f"  LOW     : {priority_counter['LOW']} task(s)\n")

    print("Categories Tracked:")
    for cat, count in category_counter.most_common():
        print(f"  {cat} : {count} task(s)")
    print()

    print(f"URGENT ATTENTION: Tasks Due Within Next 48 Hours ({len(urgent_upcoming)}):")
    if urgent_upcoming:
        for tid, tname, tdl in urgent_upcoming:
            print(f"  [!] #{tid} '{tname}' Due At: {tdl}")
    else:
        print("  None. Great job staying ahead!")
    print("\n")


def print_main_menu():
    print("\n\nTERMINAL TASK MANAGER\n")
    print("1. Add a Task")
    print("2. View All Tasks")
    print("3. Update a Task")
    print("4. Delete a Task")
    print("5. Search for a Task")
    print("6. Filter and Sort Tasks")
    print("7. Task Statistics")
    print("8. Exit Program\n")


def main():
    print("\n\nWelcome to Terminal Task Manager (Python CLI)\n")

    tasks = load_tasks(DEFAULT_DATA_FILE)

    while True:
        try:
            print_main_menu()
            choice = input("Enter your choice (1-8): ").strip()

            match choice:
                case "1":
                    add_task(tasks, DEFAULT_DATA_FILE)
                case "2":
                    view_tasks(tasks)
                case "3":
                    update_task(tasks, DEFAULT_DATA_FILE)
                case "4":
                    delete_task(tasks, DEFAULT_DATA_FILE)
                case "5":
                    search_tasks(tasks)
                case "6":
                    filter_and_sort_tasks(tasks)
                case "7":
                    display_statistics(tasks)
                case "8":
                    print("\n[Saving] Ensuring all tasks are safely stored...")
                    save_tasks(tasks, DEFAULT_DATA_FILE)
                    print("Thank you for using Terminal Task Manager. Goodbye!\n")
                    break
                case _:
                    print(f"\n[Invalid Input] '{choice}' is not a valid menu choice. Please select 1 through 8.\n")

        except (KeyboardInterrupt, EOFError):
            print("\n\n[Warning] Program interrupted by user.")
            save_tasks(tasks, DEFAULT_DATA_FILE)
            print("[Storage] Current tasks saved. Exiting safely. Goodbye!\n")
            break
        except Exception as unhandled_err:
            print(f"\n[Unexpected Error Occurred]: {unhandled_err}")
            print("The program recovered safely. Please try again.\n")


if __name__ == "__main__":
    main()
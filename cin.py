from fastapi import FastAPI, HTTPException, Query
import requests
import json
import sqlite3 
import os
import subprocess

app = FastAPI()

# Connect to an in-memory SQLite database
conn = sqlite3.connect(":memory:", check_same_thread=False)
cursor = conn.cursor()

# Create a table for tasks in the database
cursor.execute("""
   CREATE TABLE task (
       id INTEGER PRIMARY KEY,
       action TEXT,
       task_name TEXT,
       task_description TEXT,
       task_script TEXT,
       task_type TEXT,
       task_param TEXT
   )
""")

actions_folder = "actions"
# List of subfolders (actions) in the actions_folder folder
actions = [folder for folder in os.listdir(actions_folder) if os.path.isdir(os.path.join(actions_folder, folder))]

# Load action and extension definitions from JSON files and insert them into the database
for action in actions:
   action_path = os.path.join(actions_folder, action)
   action_json_path = os.path.join(action_path, "action.json")

   if os.path.exists(action_json_path):
       with open(action_json_path, "r") as file:
           action_data = json.load(file)
           action_name = action_data.get("action", "")
           tasks = action_data.get("tasks", [])

           for task in tasks:
               task_name = task.get("name", "")
               task_description = task.get("description", "")
               task_script = task.get("script", "")
               task_type = task.get("type", "")
               task_param = json.dumps(task.get("param", []))

               cursor.execute("""
                   INSERT INTO task (action, task_name, task_description, task_script, task_type, task_param)
                   VALUES (?, ?, ?, ?, ?, ?)
               """, (action_name, task_name, task_description, task_script, task_type, task_param))

@app.get("/tasks")
def get_tasks():
    cursor.execute("SELECT * FROM task")
    tasks = cursor.fetchall()

    # Convert database rows to a list of dictionaries
    task_list = []
    for task in tasks:
        _, action, task_name, task_description, task_script, task_type, task_param = task
        task_dict = {
            "action": action,
            "task_name": task_name,
            "task_description": task_description,
            "task_script": task_script,
            "task_type": task_type,
            "task_param": json.loads(task_param)
        }
        task_list.append(task_dict)

    return {"tasks": task_list}
@app.post("/execute-task/url_action/{azione}/{task}")
def execute_url_action(
    azione: str, 
    task: str,
    url: str = Query(..., description="URL to use in the task")
):
    # Build a unique identifier for the task (action and task name)
    task_identifier = f"{azione}/{task}"
    print(f"azione: {azione}")
    print(f"task: {task}")
    print(f"url: {url}")
    # Search for the task in the database based on the identifier
    cursor.execute("SELECT task_script, task_param FROM task WHERE action=? AND task_name=?", (azione, task))
    task_data = cursor.fetchone()

    if not task_data:
        raise HTTPException(status_code=404, detail=f"Task '{task_identifier}' not found")

    task_script, task_param_json = task_data
    task_param = json.loads(task_param_json)

    # Execute the script associated with the task with the parameters
    try:
        # Add the URL parameter to the parameter list
        task_param.append(url)
        script_path = os.path.join("actions", azione, task_script)
        print(f"url: {script_path}")
        print(f"url: {azione}")
        # Execute the script as an external process
        print(task_param)
        result = subprocess.run(
            ["python",task_script] + task_param,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=os.path.dirname(script_path)
        )
        print(result)
        # Check if the script execution was successful
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Task execution failed: {result.stderr}")

        # Save the script output in the global variable
        global output_script
        output_script = result.stdout

        return {"message": f"Task '{task_identifier}' executed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Task execution failed: {str(e)}")

# Endpoint to get the list of available requests in the format type/action/task
@app.get("/get-tasks-api")
def get_tasks_api():
    cursor.execute("SELECT DISTINCT action, task_name, task_description, task_type FROM task")
    tasks = cursor.fetchall()

    # Create a list of dictionaries with the requested information
    task_list = [
        {
            "request": f"{task[3]}/{task[0]}/{task[1]}",
            "task_description": task[2]
        }
        for task in tasks
    ]

    return {"available_requests": task_list}

@app.get("/")
async def root():
    return {"message": "Hello World"}
'''
if __name__ == "__main__":
   uvicorn.run(app, host="0.0.0.0", port=8000)
'''

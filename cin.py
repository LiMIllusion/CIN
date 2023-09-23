from fastapi import FastAPI, HTTPException
import requests
import json

#import actions data from custom file
with open("configuration.json", "r") as actions_file:
    actions_data = json.load(actions_file)

def check_url(action,url):
    for a in action["url_actions"]:
        if a["url"] in url:
            return True
    return False

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/configuration")
async def get_configuration():
    return actions_data

@app.get("/url_action/{action_name}")
def url_action(url: str, action_name: str):
    for action_index in actions_data["actions"]:
        if action_index["name"] == action_name:
            action = action_index
    if not check_url(action,url):
        raise HTTPException(status_code=404, detail="Action not found for that url")
    if action["action"]=="add":
        api_url= "https://api.notion.com/v1/pages"
        headers = {
            "Authorization": "Bearer " + action["api_key"],
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        }
        for a in action["url_actions"]:
            if a["url"] in url:
                data = a["param"]
        
        payload = {"parent": {"database_id": action["database_id"]}, "properties": data}
        res = requests.post(api_url, headers=headers, json=payload)

    return action





###  for action in actions_data["actions"]:
###        for associazione in action["associazioni"]:
###         if associazione["url"] == url:
###                # Esegui l"azione qui in base alle associazioni
###               return {"messaggio": f"Azione "{action["etichetta"]}" eseguita per URL "{url}""}``` 
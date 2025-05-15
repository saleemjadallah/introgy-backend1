from fastapi import APIRouter, Request

router = APIRouter()

@router.get("/users")
async def get_users(request: Request):
    users = []
    cursor = request.app.mongodb["IntrogyUsers"].find()
    async for user in cursor:
        user["_id"] = str(user["_id"])
        users.append(user)
    return users

@router.get("/boundary-templates")
async def get_boundary_templates(request: Request):
    templates = []
    cursor = request.app.mongodb["boundary_templates"].find()
    async for template in cursor:
        template["_id"] = str(template["_id"])
        templates.append(template)
    return templates

@router.get("/communication-preferences")
async def get_communication_preferences(request: Request):
    preferences = []
    cursor = request.app.mongodb["communication_preferences"].find()
    async for pref in cursor:
        pref["_id"] = str(pref["_id"])
        preferences.append(pref)
    return preferences

@router.get("/social-events")
async def get_social_events(request: Request):
    events = []
    cursor = request.app.mongodb["social_events"].find()
    async for event in cursor:
        event["_id"] = str(event["_id"])
        events.append(event)
    return events 
import strawberry
from typing import List, Optional
from strawberry.types import Info
from strawberry.file_uploads import Upload
from .models import Event
from .types import (
    PortalEventType, 
    PortalEventMediaType,
    CreatePortalEventInput,
    UpdatePortalEventInput
)
from .services import (
    create_event, 
    update_event, 
    delete_event, 
    upload_event_media
)


@strawberry.type
class Query:

    @strawberry.field(description="List all events for the current partner.")
    def my_events(self, info: Info) -> List[PortalEventType]:
        user = info.context.request.user
        # If user is a Partner instance directly
        return Event.objects.filter(user=user)


@strawberry.type
class Mutation:

    @strawberry.mutation(description="Create a new event as a partner.")
    def create_portal_event(
        self, 
        info: Info, 
        input: CreatePortalEventInput
    ) -> PortalEventType:
        user = info.context.request.user
        
        # Convert input object to dict for service
        data = {
            "title": input.title,
            "description": input.description,
            "start_date": input.start_date,
            "end_date": input.end_date,
            "registration_link": input.registration_link,
            "status": input.status,
        }

        event = create_event(user, data)
        return event


    @strawberry.mutation(description="Update an existing event.")
    def update_portal_event(
        self, 
        info: Info, 
        event_id: strawberry.ID, 
        input: UpdatePortalEventInput
    ) -> PortalEventType:
        user = info.context.request.user

        # Filter out UNSET values
        data = {}
        for field in ["title", "description", "start_date", "end_date", "registration_link", "status"]:
            val = getattr(input, field)
            if val is not strawberry.UNSET:
                data[field] = val

        event = update_event(user, event_id, data)
        return event


    @strawberry.mutation(description="Delete an event.")
    def delete_portal_event(self, info: Info, event_id: strawberry.ID) -> bool:
        user = info.context.request.user
        return delete_event(user, event_id)


    @strawberry.mutation(description="Upload media to an event.")
    def upload_portal_event_media(
        self, 
        info: Info, 
        event_id: strawberry.ID, 
        file: Upload, 
        media_type: str
    ) -> PortalEventMediaType:
        user = info.context.request.user
        media = upload_event_media(user, event_id, file, media_type)
        return media
import strawberry
from typing import Optional, List
from datetime import datetime
from strawberry.file_uploads import Upload


@strawberry.type
class PortalEventMediaType:
    id: strawberry.ID
    file: str
    type: str
    uploaded_at: datetime


@strawberry.type
class PortalEventType:
    id: strawberry.ID
    title: str
    description: Optional[str]
    start_date: datetime
    end_date: datetime
    registration_link: Optional[str]
    status: str
    
    @strawberry.field
    def media(self, root) -> List[PortalEventMediaType]:
        return root.media.all()


@strawberry.input
class CreatePortalEventInput:
    title: str
    description: Optional[str] = ""
    start_date: datetime
    end_date: datetime
    registration_link: Optional[str] = None
    status: Optional[str] = "DRAFT"


@strawberry.input
class UpdatePortalEventInput:
    title: Optional[str] = strawberry.UNSET
    description: Optional[str] = strawberry.UNSET
    start_date: Optional[datetime] = strawberry.UNSET
    end_date: Optional[datetime] = strawberry.UNSET
    registration_link: Optional[str] = strawberry.UNSET
    status: Optional[str] = strawberry.UNSET
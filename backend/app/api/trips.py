"""
Trips API Endpoints - Save/Load Board State
"""

import uuid
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Dict, List, Any, Optional

from ..services.database import db
from ..logic.transformer import generate_excalidraw_scene
from ..core.templates import generate_welcome_template

router = APIRouter()

# Default user UUID (fallback when no auth header provided)
DEFAULT_USER_ID = "67e4c780-75fe-4c18-8329-2492cedb57cc"


def get_user_id(x_user_id: Optional[str] = None) -> str:
    """Get user ID from header or use default"""
    return x_user_id if x_user_id else DEFAULT_USER_ID


# ================================================
# Request/Response Models
# ================================================

class CanvasState(BaseModel):
    """Canvas state for save/load operations"""
    elements: List[Dict[str, Any]] = []
    files: Dict[str, Any] = {}
    appState: Optional[Dict[str, Any]] = None


class CanvasResponse(BaseModel):
    """Response containing canvas data"""
    trip_id: str
    elements: List[Dict[str, Any]]
    files: Dict[str, Any]
    appState: Optional[Dict[str, Any]] = None
    last_modified: Optional[str] = None


# ================================================
# API Endpoints
# ================================================

@router.get("/trips/{trip_id}/canvas", response_model=CanvasResponse)
async def get_canvas(trip_id: str):
    """
    GET /trips/{id}/canvas

    Returns the canvas state (elements + files) for a trip.
    If the canvas is empty, returns the welcome template instead.
    """
    print(f"[API] GET /trips/{trip_id}/canvas")

    try:
        canvas = await db.get_canvas_state(trip_id)

        # If no canvas exists or canvas is empty, return welcome template
        if not canvas or not canvas.get("scene_elements") or len(canvas.get("scene_elements", [])) == 0:
            print(f"    Canvas empty, returning welcome template")
            template = generate_welcome_template()
            return CanvasResponse(
                trip_id=trip_id,
                elements=template["elements"],
                files=template["files"],
                appState=None
            )

        return CanvasResponse(
            trip_id=trip_id,
            elements=canvas.get("scene_elements", []),
            files=canvas.get("scene_files", {}),
            appState=canvas.get("scene_app_state"),
            last_modified=str(canvas.get("last_modified")) if canvas.get("last_modified") else None
        )

    except Exception as e:
        print(f"[API] Error getting canvas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/trips/{trip_id}/canvas", response_model=CanvasResponse)
async def update_canvas(trip_id: str, canvas: CanvasState):
    """
    PUT /trips/{id}/canvas

    Updates the canvas state for a trip.
    Full replace for MVP - sends complete elements + files.
    """
    print(f"[API] PUT /trips/{trip_id}/canvas - {len(canvas.elements)} elements")

    try:
        # Verify trip exists
        trip = await db.get_trip(trip_id)
        if not trip:
            raise HTTPException(status_code=404, detail="Trip not found")

        # Update canvas state
        result = await db.update_canvas_state(
            trip_id=trip_id,
            scene_elements=canvas.elements,
            scene_files=canvas.files,
            scene_app_state=canvas.appState
        )

        # If no existing canvas, the update might return empty
        # In that case, return what was sent
        return CanvasResponse(
            trip_id=trip_id,
            elements=result.get("scene_elements", canvas.elements) if result else canvas.elements,
            files=result.get("scene_files", canvas.files) if result else canvas.files,
            appState=result.get("scene_app_state", canvas.appState) if result else canvas.appState,
            last_modified=str(result.get("last_modified")) if result and result.get("last_modified") else None
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] Error updating canvas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ================================================
# Trip CRUD Endpoints (bonus for completeness)
# ================================================

class TripCreate(BaseModel):
    """Create trip request"""
    title: str = "New Trip"
    destination: Optional[str] = None


class TripResponse(BaseModel):
    """Trip response"""
    id: str
    title: str
    status: str
    destination: Optional[str] = None
    created_at: Optional[str] = None


@router.post("/trips", response_model=TripResponse)
async def create_trip(trip: TripCreate, x_user_id: Optional[str] = Header(None)):
    """
    POST /trips

    Create a new trip for the authenticated user with welcome template
    """
    user_id = get_user_id(x_user_id)
    print(f"[API] POST /trips - Title: {trip.title}, User: {user_id}")

    try:
        # Create the trip
        result = await db.create_trip(
            user_id=user_id,
            title=trip.title,
            destination=trip.destination,
            status="active",
        )

        trip_id = result.get("id", "")

        # Generate welcome template
        template = generate_welcome_template()

        # Create initial canvas state with welcome template
        await db.update_canvas_state(
            trip_id=trip_id,
            scene_elements=template["elements"],
            scene_files=template["files"],
            scene_app_state=None
        )

        print(f"[API] Created trip {trip_id} with welcome template")

        return TripResponse(
            id=trip_id,
            title=result.get("title", trip.title),
            status=result.get("status", "draft"),
            destination=result.get("destination"),
            created_at=str(result.get("created_at")) if result.get("created_at") else None
        )

    except Exception as e:
        print(f"[API] Error creating trip: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trips/{trip_id}", response_model=TripResponse)
async def get_trip(trip_id: str):
    """
    GET /trips/{id}

    Get trip metadata
    """
    print(f"[API] GET /trips/{trip_id}")

    try:
        trip = await db.get_trip(trip_id)

        if not trip:
            raise HTTPException(status_code=404, detail="Trip not found")

        return TripResponse(
            id=trip.get("id", ""),
            title=trip.get("title", ""),
            status=trip.get("status", "draft"),
            destination=trip.get("destination"),
            created_at=str(trip.get("created_at")) if trip.get("created_at") else None
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] Error getting trip: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trips/latest/id")
async def get_latest_trip(x_user_id: Optional[str] = Header(None)):
    """
    GET /trips/latest/id

    Get the most recent trip ID for the user
    """
    user_id = get_user_id(x_user_id)
    print(f"[API] GET /trips/latest/id - User: {user_id}")

    try:
        trips = await db.get_user_trips(user_id)

        if not trips:
            raise HTTPException(status_code=404, detail="No trips found")

        latest = trips[0]
        return {
            "trip_id": latest.get("id"),
            "title": latest.get("title"),
            "created_at": str(latest.get("created_at")) if latest.get("created_at") else None
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] Error getting latest trip: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ================================================
# Dashboard Endpoints (Wave 4 - Issue #15)
# ================================================

class TripListItem(BaseModel):
    """Trip item for dashboard list"""
    id: str
    title: str
    status: str
    destination: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    thumbnail_url: Optional[str] = None


class TripListResponse(BaseModel):
    """Response containing list of trips"""
    trips: List[TripListItem]
    count: int


@router.get("/trips", response_model=TripListResponse)
async def list_trips(x_user_id: Optional[str] = Header(None)):
    """
    GET /trips

    Get all trips for the current user (dashboard view)
    Includes thumbnail images from canvas state
    """
    user_id = get_user_id(x_user_id)
    print(f"[API] GET /trips - User: {user_id}")

    try:
        trips = await db.get_user_trips_with_thumbnails(user_id)

        trip_items = [
            TripListItem(
                id=t.get("id", ""),
                title=t.get("title", "Untitled Trip"),
                status=t.get("status", "draft"),
                destination=t.get("destination"),
                created_at=str(t.get("created_at")) if t.get("created_at") else None,
                updated_at=str(t.get("updated_at")) if t.get("updated_at") else None,
                thumbnail_url=t.get("thumbnail_url")
            )
            for t in trips
        ]

        return TripListResponse(trips=trip_items, count=len(trip_items))

    except Exception as e:
        print(f"[API] Error listing trips: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class TripUpdate(BaseModel):
    """Update trip request"""
    title: Optional[str] = None
    destination: Optional[str] = None
    status: Optional[str] = None


@router.patch("/trips/{trip_id}", response_model=TripResponse)
async def update_trip(trip_id: str, update: TripUpdate):
    """
    PATCH /trips/{id}

    Update trip metadata (rename, change status, etc.)
    """
    print(f"[API] PATCH /trips/{trip_id}")

    try:
        # Build update dict with only provided fields
        update_data = {}
        if update.title is not None:
            update_data["title"] = update.title
        if update.destination is not None:
            update_data["destination"] = update.destination
        if update.status is not None:
            update_data["status"] = update.status

        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")

        result = await db.update_trip(trip_id, update_data)

        if not result:
            raise HTTPException(status_code=404, detail="Trip not found")

        return TripResponse(
            id=result.get("id", trip_id),
            title=result.get("title", ""),
            status=result.get("status", "draft"),
            destination=result.get("destination"),
            created_at=str(result.get("created_at")) if result.get("created_at") else None
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] Error updating trip: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/trips/{trip_id}")
async def delete_trip(trip_id: str):
    """
    DELETE /trips/{id}

    Delete a trip and its canvas state
    """
    print(f"[API] DELETE /trips/{trip_id}")

    try:
        success = await db.delete_trip(trip_id)

        if not success:
            raise HTTPException(status_code=404, detail="Trip not found")

        return {"message": "Trip deleted", "id": trip_id}

    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] Error deleting trip: {e}")
        raise HTTPException(status_code=500, detail=str(e))

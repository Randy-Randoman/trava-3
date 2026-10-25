"""
Trips API Endpoints - Save/Load Board State
"""

import logging
import re
import uuid
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, List, Any, Literal, Optional

from ..services.database import db
from ..core.templates import generate_welcome_template
from ..core.auth import require_auth, verify_trip_owner

logger = logging.getLogger(__name__)

router = APIRouter()


# ================================================
# Request/Response Models
# ================================================

class CanvasState(BaseModel):
    """Canvas state for save/load operations"""
    elements: List[Dict[str, Any]] = []
    files: Dict[str, Any] = {}
    appState: Optional[Dict[str, Any]] = None
    # last_modified of the canvas this tab last loaded/saved; a mismatch means a stale tab
    base_version: Optional[str] = None


class CanvasResponse(BaseModel):
    """Response containing canvas data"""
    trip_id: str
    elements: List[Dict[str, Any]]
    files: Dict[str, Any]
    appState: Optional[Dict[str, Any]] = None
    last_modified: Optional[str] = None


def _canvas_version(canvas: Optional[Dict[str, Any]]) -> Optional[str]:
    """The stored canvas version: its last_modified (bumped by a DB trigger on every write)."""
    if canvas and canvas.get("last_modified"):
        return str(canvas["last_modified"])
    return None


# ================================================
# API Endpoints
# ================================================

@router.get("/trips/{trip_id}/canvas", response_model=CanvasResponse)
async def get_canvas(trip_id: str, user_id: str = Depends(require_auth)):
    """
    GET /trips/{id}/canvas

    Returns the canvas state (elements + files) for a trip.
    If the canvas is empty, returns the welcome template instead.
    """
    logger.info(f"GET /trips/{trip_id}/canvas")

    try:
        await verify_trip_owner(trip_id, user_id)
        canvas = await db.get_canvas_state(trip_id)

        # If no canvas exists or canvas is empty, return welcome template
        if not canvas or not canvas.get("scene_elements") or len(canvas.get("scene_elements", [])) == 0:
            logger.info("Canvas empty, returning welcome template")
            template = generate_welcome_template()
            return CanvasResponse(
                trip_id=trip_id,
                elements=template["elements"],
                files=template["files"],
                appState=None,
                last_modified=_canvas_version(canvas)
            )

        return CanvasResponse(
            trip_id=trip_id,
            elements=canvas.get("scene_elements", []),
            files=canvas.get("scene_files", {}),
            appState=canvas.get("scene_app_state"),
            last_modified=_canvas_version(canvas)
        )

    except HTTPException:
        raise
    except Exception:
        logger.exception("Error getting canvas")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/trips/{trip_id}/canvas", response_model=CanvasResponse)
async def update_canvas(trip_id: str, canvas: CanvasState, user_id: str = Depends(require_auth)):
    """
    PUT /trips/{id}/canvas

    Updates the canvas state for a trip.
    Full replace for MVP - sends complete elements + files.
    Returns 409 with the current canvas if base_version is stale.
    """
    logger.info(f"PUT /trips/{trip_id}/canvas - {len(canvas.elements)} elements")

    try:
        await verify_trip_owner(trip_id, user_id)

        # Optimistic concurrency: a stale tab must not overwrite or reconcile away newer changes
        current = await db.get_canvas_state(trip_id) or {}
        current_version = _canvas_version(current)
        if canvas.base_version != current_version:
            logger.info(f"Canvas save conflict for trip {trip_id}")
            raise HTTPException(status_code=409, detail=CanvasResponse(
                trip_id=trip_id,
                elements=current.get("scene_elements") or [],
                files=current.get("scene_files") or {},
                appState=current.get("scene_app_state"),
                last_modified=current_version
            ).model_dump())

        # Update canvas state
        result = await db.update_canvas_state(
            trip_id=trip_id,
            scene_elements=canvas.elements,
            scene_files=canvas.files,
            scene_app_state=canvas.appState
        )

        # Reconcile board_items: remove items whose cards were deleted from the canvas
        board_items = await db.get_board_items(trip_id)
        if board_items:
            # Collect all group IDs still present in the saved elements
            active_group_ids = set()
            for el in canvas.elements:
                if el.get("isDeleted"):
                    continue
                for gid in (el.get("groupIds") or []):
                    active_group_ids.add(gid)

            # Keep only board items whose excalidraw_group_id is still on the canvas
            reconciled = [
                bi for bi in board_items
                if bi.get("excalidraw_group_id") in active_group_ids
            ]
            if len(reconciled) != len(board_items):
                removed = len(board_items) - len(reconciled)
                logger.info(f"Board reconciliation: removed {removed} orphaned board item(s)")
                await db.update_board_items(trip_id, reconciled)

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
    except Exception:
        logger.exception("Error updating canvas")
        raise HTTPException(status_code=500, detail="Internal server error")


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
async def create_trip(trip: TripCreate, user_id: str = Depends(require_auth)):
    """
    POST /trips

    Create a new trip for the authenticated user with welcome template
    """
    logger.info(f"POST /trips - Title: {trip.title}, User: {user_id}")

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

        logger.info(f"Created trip {trip_id} with welcome template")

        return TripResponse(
            id=trip_id,
            title=result.get("title", trip.title),
            status=result.get("status", "draft"),
            destination=result.get("destination"),
            created_at=str(result.get("created_at")) if result.get("created_at") else None
        )

    except Exception:
        logger.exception("Error creating trip")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/trips/{trip_id}", response_model=TripResponse)
async def get_trip(trip_id: str, user_id: str = Depends(require_auth)):
    """
    GET /trips/{id}

    Get trip metadata
    """
    logger.info(f"GET /trips/{trip_id}")

    try:
        trip = await verify_trip_owner(trip_id, user_id)

        return TripResponse(
            id=trip.get("id", ""),
            title=trip.get("title", ""),
            status=trip.get("status", "draft"),
            destination=trip.get("destination"),
            created_at=str(trip.get("created_at")) if trip.get("created_at") else None
        )

    except HTTPException:
        raise
    except Exception:
        logger.exception("Error getting trip")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/trips/latest/id")
async def get_latest_trip(user_id: str = Depends(require_auth)):
    """
    GET /trips/latest/id

    Get the most recent trip ID for the user
    """
    logger.info(f"GET /trips/latest/id - User: {user_id}")

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
    except Exception:
        logger.exception("Error getting latest trip")
        raise HTTPException(status_code=500, detail="Internal server error")


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
async def list_trips(user_id: str = Depends(require_auth)):
    """
    GET /trips

    Get all trips for the current user (dashboard view)
    Includes thumbnail images from canvas state
    """
    logger.info(f"GET /trips - User: {user_id}")

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

    except Exception:
        logger.exception("Error listing trips")
        raise HTTPException(status_code=500, detail="Internal server error")


class TripUpdate(BaseModel):
    """Update trip request"""
    title: Optional[str] = None
    destination: Optional[str] = None
    status: Optional[Literal["draft", "active", "archived"]] = None


@router.patch("/trips/{trip_id}", response_model=TripResponse)
async def update_trip(trip_id: str, update: TripUpdate, user_id: str = Depends(require_auth)):
    """
    PATCH /trips/{id}

    Update trip metadata (rename, change status, etc.)
    """
    logger.info(f"PATCH /trips/{trip_id}")

    try:
        await verify_trip_owner(trip_id, user_id)

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
    except Exception:
        logger.exception("Error updating trip")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/trips/{trip_id}")
async def delete_trip(trip_id: str, user_id: str = Depends(require_auth)):
    """
    DELETE /trips/{id}

    Delete a trip, its canvas state, and any uploaded images from storage
    """
    logger.info(f"DELETE /trips/{trip_id}")

    try:
        await verify_trip_owner(trip_id, user_id)
        # Clean up uploaded images from Supabase Storage
        try:
            storage = db.client.storage.from_("canvas-images")
            file_list = storage.list(trip_id)
            if file_list:
                paths = [f"{trip_id}/{f['name']}" for f in file_list]
                if paths:
                    storage.remove(paths)
                    logger.info(f"Deleted {len(paths)} image(s) from storage for trip {trip_id}")
        except Exception as storage_err:
            # Don't fail the whole delete if storage cleanup fails
            logger.warning(f"Storage cleanup failed for trip {trip_id}: {storage_err}")

        success = await db.delete_trip(trip_id)

        if not success:
            raise HTTPException(status_code=404, detail="Trip not found")

        return {"message": "Trip deleted", "id": trip_id}

    except HTTPException:
        raise
    except Exception:
        logger.exception("Error deleting trip")
        raise HTTPException(status_code=500, detail="Internal server error")


# ================================================
# Budget Endpoint (Issue #19)
# ================================================

@router.get("/trips/{trip_id}/budget")
async def get_budget(trip_id: str, user_id: str = Depends(require_auth)):
    """
    GET /trips/{id}/budget

    Returns the trip budget and running total spent from board items.
    Extracts the first numeric value from each item's price string.
    """
    logger.info(f"GET /trips/{trip_id}/budget")

    try:
        trip = await verify_trip_owner(trip_id, user_id)

        budget = trip.get("budget")  # Decimal or None from DB
        board_items = trip.get("board_items") or []

        spent = 0.0
        items_with_prices = []
        for bi in board_items:
            data = bi.get("data", {})
            price_str = str(data.get("price", "") or "")
            # Extract first number from strings like "$234", "$1,234", "99.90 EUR", "1.234,50 €"
            match = re.search(r"\d[\d.,]*", price_str)
            if match:
                num = match.group().rstrip(".,")
                if "," in num and "." in num:
                    # The separator that comes last is the decimal one
                    if num.rfind(",") > num.rfind("."):
                        num = num.replace(".", "").replace(",", ".")
                    else:
                        num = num.replace(",", "")
                elif "," in num:
                    # "1,234" is thousands, "12,50" is decimal
                    num = num.replace(",", "") if re.fullmatch(r"\d{1,3}(,\d{3})+", num) else num.replace(",", ".")
                elif re.fullmatch(r"\d{1,3}(\.\d{3})+", num):
                    # "1.234" is European thousands, "99.90" stays decimal
                    num = num.replace(".", "")
                try:
                    price_val = float(num)
                    spent += price_val
                    items_with_prices.append({
                        "name": bi.get("name", ""),
                        "type": bi.get("type", ""),
                        "price": price_val,
                    })
                except ValueError:
                    pass

        return {
            "budget": float(budget) if budget is not None else None,
            "spent": round(spent, 2),
            "items": items_with_prices,
        }

    except HTTPException:
        raise
    except Exception:
        logger.exception("Error getting budget")
        raise HTTPException(status_code=500, detail="Internal server error")


# ================================================
# Share Endpoints (Issue #20)
# ================================================

@router.post("/trips/{trip_id}/share")
async def share_trip(trip_id: str, user_id: str = Depends(require_auth)):
    """
    POST /trips/{id}/share

    Generate (or return existing) share token for a trip.
    Returns the share token so the frontend can build the share URL.
    """
    logger.info(f"POST /trips/{trip_id}/share")

    try:
        trip = await verify_trip_owner(trip_id, user_id)

        # Reuse existing token if present, otherwise generate a new one
        share_token = trip.get("share_token") or str(uuid.uuid4())
        await db.set_share_token(trip_id, share_token)

        return {"share_token": share_token}

    except HTTPException:
        raise
    except Exception:
        logger.exception("Error sharing trip")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/trips/public/{share_token}")
async def get_public_board(share_token: str):
    """
    GET /trips/public/{share_token}

    Public read-only board view — no auth required.
    Returns trip title + canvas elements/files for display.
    """
    logger.info("GET /trips/public/<token>")

    try:
        trip = await db.get_trip_by_share_token(share_token)
        if not trip:
            raise HTTPException(status_code=404, detail="Board not found")

        canvas = await db.get_canvas_state(trip["id"])

        return {
            "trip_id": trip["id"],
            "title": trip.get("title", ""),
            "elements": canvas.get("scene_elements", []) if canvas else [],
            "files": canvas.get("scene_files", {}) if canvas else {},
        }

    except HTTPException:
        raise
    except Exception:
        logger.exception("Error fetching public board")
        raise HTTPException(status_code=500, detail="Internal server error")

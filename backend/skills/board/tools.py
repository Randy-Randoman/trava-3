import json
from datetime import datetime, timezone
from typing import Annotated
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState


def _generate_id() -> str:
    """Generate a short unique ID for board items."""
    import uuid
    return str(uuid.uuid4())[:8]


async def read_board(trip_id: str) -> str:
    """Summarise the items on a trip's board."""
    from app.services.database import DatabaseService

    db = DatabaseService()
    items = await db.get_board_items(trip_id)

    if not items:
        return "Board is empty. No items have been added yet."

    lines = [f"Board has {len(items)} item(s):"]
    for item in items:
        item_id = item.get("id", "?")[:4]
        item_type = item.get("type", "item").upper()
        name = item.get("name", "Unnamed")
        data = item.get("data", {})

        details = []
        if data.get("price"):
            details.append(data["price"])
        if data.get("rating"):
            details.append(f"Rating: {data['rating']}")
        if data.get("review_count"):
            details.append(f"{data['review_count']} reviews")

        detail_str = f" ({', '.join(details)})" if details else ""
        lines.append(f"- [{item_id}] {item_type}: {name}{detail_str}")

    return "\n".join(lines)


async def add_items(trip_id: str, items: str | list | dict) -> str:
    """Add items (JSON string, list or single dict) to a trip's board and redraw its cards."""
    from app.services.database import DatabaseService
    from app.logic.transformer import generate_card_elements

    # Parse items JSON
    try:
        item_list = json.loads(items) if isinstance(items, str) else items
        if not isinstance(item_list, list):
            item_list = [item_list]
    except json.JSONDecodeError as e:
        return f"Error: Could not parse items JSON: {e}"

    if not item_list:
        return "Error: No items provided."

    db = DatabaseService()

    # Read current canvas & board state
    canvas = await db.get_canvas_state(trip_id)
    existing_elements = []
    existing_files = {}
    if canvas:
        existing_elements = canvas.get("scene_elements") or []
        existing_files = canvas.get("scene_files") or {}

    current_board_items = await db.get_board_items(trip_id)

    # ── First-ever add: wipe the canvas clean (removes welcome message) ──
    first_add = len(current_board_items) == 0
    if first_add:
        existing_elements = []
        existing_files = {}

    # ── Merge board items: keep all existing items, append new ones ──
    kept_board_items = list(current_board_items)


    # Strip ALL agent-placed elements from canvas (tagged with customData.agentPlaced)
    # Also strip legacy agent elements by group ID for backwards compat
    all_agent_group_ids = set()
    for bi in current_board_items:
        gid = bi.get("excalidraw_group_id")
        if gid:
            all_agent_group_ids.add(gid)

    user_elements = []
    for el in existing_elements:
        # Primary: check the agentPlaced tag (set by transformer)
        if (el.get("customData") or {}).get("agentPlaced"):
            continue
        # Fallback: match by group ID for elements created before the tag existed
        el_group_ids = el.get("groupIds") or []
        if any(gid in all_agent_group_ids for gid in el_group_ids):
            continue
        user_elements.append(el)

    # Build merged item data list from kept board items + new items
    merged_item_data = []
    merged_ids = []
    for bi in kept_board_items:
        # Reconstruct the item dict from board_item data
        item_data = dict(bi.get("data", {}))
        item_data.setdefault("name", bi.get("name", "Unnamed"))
        item_data.setdefault("type", bi.get("type", "stay"))
        if bi.get("day") is not None:
            item_data["day"] = bi["day"]
        if bi.get("date"):
            item_data["date"] = bi["date"]
        merged_item_data.append(item_data)
        merged_ids.append(bi.get("id") or _generate_id())

    for item in item_list:
        merged_item_data.append(item)
        merged_ids.append(_generate_id())

    # Regenerate ALL card elements from merged items, positioned below user content
    new_elements, new_files, group_ids = await generate_card_elements(
        merged_item_data, user_elements
    )

    # Combine user-drawn elements with regenerated agent elements
    updated_elements = user_elements + new_elements

    # Merge files (keep user files, add new agent files)
    updated_files = {**existing_files, **new_files}

    # Save updated canvas state
    await db.update_canvas_state(
        trip_id,
        scene_elements=updated_elements,
        scene_files=updated_files,
    )

    # Create BoardItem records for ALL merged items (existing IDs kept, fresh group IDs from layout)
    all_board_items = []
    for i, item_data in enumerate(merged_item_data):
        board_item = {
            "id": merged_ids[i],
            "type": item_data.get("type", "stay"),
            "name": item_data.get("name", "Unnamed"),
            "day": item_data.get("day"),
            "date": item_data.get("date"),
            "excalidraw_group_id": group_ids[i] if i < len(group_ids) else _generate_id(),
            "data": item_data,
            "added_at": datetime.now(timezone.utc).isoformat(),
        }
        all_board_items.append(board_item)

    await db.update_board_items(trip_id, all_board_items)

    names = [item.get("name", "item") for item in item_list]
    return f"Added {len(item_list)} item(s) to the board: {', '.join(names)}"


async def remove_items(trip_id: str, item_ids: str) -> str:
    """Remove board items whose ID starts with one of the comma-separated IDs."""
    from app.services.database import DatabaseService

    # Parse item IDs
    ids_to_remove = [id.strip() for id in item_ids.split(",") if id.strip()]
    if not ids_to_remove:
        return "Error: No item IDs provided."

    db = DatabaseService()
    board_items = await db.get_board_items(trip_id)

    if not board_items:
        return "Board is empty, nothing to remove."

    # Find items to remove (match by ID prefix — board_read shows first 4 chars)
    items_to_remove = []
    group_ids_to_remove = set()
    for bi in board_items:
        bi_id = bi.get("id", "")
        if any(bi_id.startswith(rid) for rid in ids_to_remove):
            items_to_remove.append(bi)
            group_ids_to_remove.add(bi.get("excalidraw_group_id"))

    if not items_to_remove:
        return f"No items found matching IDs: {', '.join(ids_to_remove)}"

    # Filter out canvas elements with those group IDs
    canvas = await db.get_canvas_state(trip_id)
    if canvas and canvas.get("scene_elements"):
        elements = canvas["scene_elements"]
        filtered = [
            el for el in elements
            if not any(gid in (el.get("groupIds") or []) for gid in group_ids_to_remove)
        ]
        await db.update_canvas_state(trip_id, scene_elements=filtered)

    # Remove items from board_items
    remaining = [bi for bi in board_items if bi not in items_to_remove]
    await db.update_board_items(trip_id, remaining)

    names = [bi.get("name", "item") for bi in items_to_remove]
    return f"Removed {len(items_to_remove)} item(s) from the board: {', '.join(names)}"


async def clear_board(trip_id: str) -> str:
    """Remove all agent-placed items from a trip's board, keeping user-drawn content."""
    from app.services.database import DatabaseService

    db = DatabaseService()
    board_items = await db.get_board_items(trip_id)

    if not board_items:
        return "Board is already empty."

    # Collect all group IDs from agent-placed items (fallback matching)
    group_ids_to_remove = set()
    for bi in board_items:
        gid = bi.get("excalidraw_group_id")
        if gid:
            group_ids_to_remove.add(gid)

    # Filter out agent-placed elements from canvas (preserves user-drawn content)
    canvas = await db.get_canvas_state(trip_id)
    if canvas and canvas.get("scene_elements"):
        elements = canvas["scene_elements"]
        filtered = []
        for el in elements:
            # Primary: check agentPlaced tag
            if (el.get("customData") or {}).get("agentPlaced"):
                continue
            # Fallback: match by group ID
            if any(gid in group_ids_to_remove for gid in (el.get("groupIds") or [])):
                continue
            filtered.append(el)
        await db.update_canvas_state(trip_id, scene_elements=filtered)

    count = len(board_items)
    await db.update_board_items(trip_id, [])

    return f"Cleared {count} item(s) from the board. User-drawn content preserved."


@tool
async def board_read(trip_id: Annotated[str, InjectedState("trip_id")]) -> str:
    """Read what's currently on the trip board. Returns a summary of all items (hotels, activities) placed on the visual canvas."""
    return await read_board(trip_id)


@tool
async def board_add_items(
    items: str,
    trip_id: Annotated[str, InjectedState("trip_id")],
) -> str:
    """Add hotel or activity cards to the visual trip board.

    Args:
        items: JSON string — a list of item objects. Each object should have:
            name (required), type ("stay"/"activity"), price, rating, review_count,
            distance, url/bookingUrl, image_url/imageUrl.
            Optional: day (int, e.g. 1), date (str, e.g. "2026-03-17") for day grouping.
    """
    return await add_items(trip_id, items)


@tool
async def board_remove_items(
    item_ids: str,
    trip_id: Annotated[str, InjectedState("trip_id")],
) -> str:
    """Remove specific items from the trip board by their IDs (the short IDs shown by board_read, e.g. 'a1b2').

    Args:
        item_ids: Comma-separated item IDs to remove (e.g. "a1b2,c3d4")
    """
    return await remove_items(trip_id, item_ids)


@tool
async def board_clear(trip_id: Annotated[str, InjectedState("trip_id")]) -> str:
    """Clear all agent-placed items from the trip board, preserving user-drawn content."""
    return await clear_board(trip_id)

"""Tests for the board skill tools (skills/board/tools.py)."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from skills.board.tools import (
    add_items,
    board_add_items,
    board_clear,
    board_read,
    board_remove_items,
    clear_board,
    read_board,
    remove_items,
)

TRIP_ID = "trip-1"


def make_db(board_items=None, canvas=None):
    db = MagicMock()
    db.get_board_items = AsyncMock(return_value=board_items or [])
    db.get_canvas_state = AsyncMock(return_value=canvas)
    db.update_board_items = AsyncMock()
    db.update_canvas_state = AsyncMock()
    return db


@pytest.fixture
def patch_db():
    """Patch DatabaseService so tools get the given fake db."""
    patchers = []

    def _patch(db):
        p = patch("app.services.database.DatabaseService", return_value=db)
        p.start()
        patchers.append(p)
        return db

    yield _patch
    for p in patchers:
        p.stop()


@pytest.fixture
def fake_cards():
    """Replace card generation: one agent element + group id per item."""

    async def _generate(items, user_elements):
        elements = [{"id": f"card-{i}", "customData": {"agentPlaced": True}} for i in range(len(items))]
        return elements, {"file-new": {}}, [f"g-{i}" for i in range(len(items))]

    with patch("app.logic.transformer.generate_card_elements", side_effect=_generate) as m:
        yield m


# Every case runs against both the @tool wrapper and the plain function it calls.
@pytest.fixture(params=["tool", "plain"])
def via(request):
    return request.param


@pytest.fixture
def read(via):
    return board_read.coroutine if via == "tool" else read_board


@pytest.fixture
def add(via):
    return board_add_items.coroutine if via == "tool" else add_items


@pytest.fixture
def remove(via):
    return board_remove_items.coroutine if via == "tool" else remove_items


@pytest.fixture
def clear(via):
    return board_clear.coroutine if via == "tool" else clear_board


def saved_board_items(db):
    return db.update_board_items.call_args.args[1]


class TestBoardRead:
    async def test_empty_board(self, patch_db, read):
        patch_db(make_db())
        result = await read(trip_id=TRIP_ID)
        assert result == "Board is empty. No items have been added yet."

    async def test_summary_of_several_items(self, patch_db, read):
        patch_db(make_db(board_items=[
            {"id": "abcd1234", "type": "stay", "name": "Hotel Roma",
             "data": {"price": "€120", "rating": 8.5, "review_count": 300}},
            {"id": "efgh5678", "type": "activity", "name": "Colosseum Tour", "data": {}},
        ]))
        result = await read(trip_id=TRIP_ID)
        assert result == (
            "Board has 2 item(s):\n"
            "- [abcd] STAY: Hotel Roma (€120, Rating: 8.5, 300 reviews)\n"
            "- [efgh] ACTIVITY: Colosseum Tour"
        )


class TestBoardAddItems:
    async def test_adds_to_empty_board_with_generated_ids(self, patch_db, fake_cards, add):
        db = patch_db(make_db(canvas={
            "scene_elements": [{"id": "welcome-text"}],
            "scene_files": {"old": {}},
        }))
        items = json.dumps([{"name": "Hotel Roma", "type": "stay", "price": "€120", "day": 1}])

        result = await add(items=items, trip_id=TRIP_ID)

        assert result == "Added 1 item(s) to the board: Hotel Roma"
        saved = saved_board_items(db)
        assert len(saved) == 1
        assert len(saved[0]["id"]) == 8
        assert saved[0]["name"] == "Hotel Roma"
        assert saved[0]["type"] == "stay"
        assert saved[0]["day"] == 1
        assert saved[0]["excalidraw_group_id"] == "g-0"
        # First add wipes the canvas (welcome message) before placing cards
        canvas_kwargs = db.update_canvas_state.call_args.kwargs
        assert canvas_kwargs["scene_elements"] == [{"id": "card-0", "customData": {"agentPlaced": True}}]
        assert canvas_kwargs["scene_files"] == {"file-new": {}}

    async def test_single_object_is_accepted(self, patch_db, fake_cards, add):
        db = patch_db(make_db())
        result = await add(items='{"name": "Solo"}', trip_id=TRIP_ID)
        assert result == "Added 1 item(s) to the board: Solo"
        assert saved_board_items(db)[0]["type"] == "stay"  # default type

    async def test_keeps_existing_items_and_appends_new_ones(self, patch_db, fake_cards, add):
        existing = [{
            "id": "old11111", "type": "stay", "name": "Old Hotel", "day": 1,
            "excalidraw_group_id": "old-group", "data": {"price": "€80"},
        }]
        db = patch_db(make_db(board_items=existing, canvas={
            "scene_elements": [
                {"id": "user-drawing"},
                {"id": "tagged", "customData": {"agentPlaced": True}},
                {"id": "legacy", "groupIds": ["old-group"]},
            ],
            "scene_files": {"user-file": {}},
        }))
        items = json.dumps([{"name": "New Hotel", "type": "stay", "day": 1}])

        result = await add(items=items, trip_id=TRIP_ID)

        assert result == "Added 1 item(s) to the board: New Hotel"
        saved = saved_board_items(db)
        # Same day does NOT replace: existing items are kept, new ones appended
        assert [bi["name"] for bi in saved] == ["Old Hotel", "New Hotel"]
        assert saved[0]["data"]["price"] == "€80"
        assert saved[0]["day"] == 1
        # Existing items keep their ID; only new items get a generated one
        assert saved[0]["id"] == "old11111"
        assert len(saved[1]["id"]) == 8
        assert saved[1]["id"] != "old11111"
        # User content kept, old agent elements (tagged or legacy group) stripped
        canvas_kwargs = db.update_canvas_state.call_args.kwargs
        assert [el["id"] for el in canvas_kwargs["scene_elements"]] == ["user-drawing", "card-0", "card-1"]
        assert canvas_kwargs["scene_files"] == {"user-file": {}, "file-new": {}}

    async def test_invalid_json(self, patch_db, add):
        db = patch_db(make_db())
        result = await add(items="not json", trip_id=TRIP_ID)
        assert result.startswith("Error: Could not parse items JSON")
        db.update_board_items.assert_not_called()

    async def test_empty_list(self, patch_db, add):
        db = patch_db(make_db())
        result = await add(items="[]", trip_id=TRIP_ID)
        assert result == "Error: No items provided."
        db.update_board_items.assert_not_called()


BOARD = [
    {"id": "abcd1234", "name": "Hotel Roma", "excalidraw_group_id": "g-a"},
    {"id": "efgh5678", "name": "Colosseum Tour", "excalidraw_group_id": "g-e"},
]
CANVAS = {"scene_elements": [
    {"id": "card-a", "groupIds": ["g-a"]},
    {"id": "card-e", "groupIds": ["g-e"]},
    {"id": "user-drawing"},
]}


class TestBoardRemoveItems:
    async def test_remove_by_full_id(self, patch_db, remove):
        db = patch_db(make_db(board_items=list(BOARD), canvas=CANVAS))
        result = await remove(item_ids="abcd1234", trip_id=TRIP_ID)

        assert result == "Removed 1 item(s) from the board: Hotel Roma"
        assert [bi["id"] for bi in saved_board_items(db)] == ["efgh5678"]
        elements = db.update_canvas_state.call_args.kwargs["scene_elements"]
        assert [el["id"] for el in elements] == ["card-e", "user-drawing"]

    async def test_remove_by_prefix(self, patch_db, remove):
        db = patch_db(make_db(board_items=list(BOARD), canvas=CANVAS))
        result = await remove(item_ids="abcd, efgh", trip_id=TRIP_ID)

        assert result == "Removed 2 item(s) from the board: Hotel Roma, Colosseum Tour"
        assert saved_board_items(db) == []

    async def test_unknown_ids(self, patch_db, remove):
        db = patch_db(make_db(board_items=list(BOARD), canvas=CANVAS))
        result = await remove(item_ids="zzzz,yyyy", trip_id=TRIP_ID)

        assert result == "No items found matching IDs: zzzz, yyyy"
        db.update_board_items.assert_not_called()

    async def test_empty_board(self, patch_db, remove):
        patch_db(make_db())
        result = await remove(item_ids="abcd", trip_id=TRIP_ID)
        assert result == "Board is empty, nothing to remove."

    async def test_no_ids(self, patch_db, remove):
        patch_db(make_db(board_items=list(BOARD)))
        result = await remove(item_ids=" , ", trip_id=TRIP_ID)
        assert result == "Error: No item IDs provided."


class TestBoardClear:
    async def test_empties_board_and_keeps_user_content(self, patch_db, clear):
        canvas = {"scene_elements": [
            {"id": "tagged", "customData": {"agentPlaced": True}},
            {"id": "legacy", "groupIds": ["g-a"]},
            {"id": "user-drawing"},
        ]}
        db = patch_db(make_db(board_items=list(BOARD), canvas=canvas))

        result = await clear(trip_id=TRIP_ID)

        assert result == "Cleared 2 item(s) from the board. User-drawn content preserved."
        db.update_board_items.assert_awaited_once_with(TRIP_ID, [])
        elements = db.update_canvas_state.call_args.kwargs["scene_elements"]
        assert elements == [{"id": "user-drawing"}]

    async def test_already_empty(self, patch_db, clear):
        db = patch_db(make_db())
        result = await clear(trip_id=TRIP_ID)
        assert result == "Board is already empty."
        db.update_board_items.assert_not_called()

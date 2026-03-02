"""
Supabase Database Service - Client wrapper for database operations
"""

from typing import Dict, List, Any, Optional
from supabase import create_client, Client
from ..core.config import settings


class DatabaseService:
    """
    Wrapper for Supabase database operations

    Provides clean interfaces for:
    - Profiles management
    - Trips CRUD operations
    - Canvas state persistence
    """

    def __init__(self):
        self._client: Optional[Client] = None

    @property
    def client(self) -> Client:
        """
        Lazy initialization of Supabase client

        Uses SUPABASE_SERVICE_KEY to bypass RLS policies.
        This is safe in the backend because the service key is never exposed to the frontend.
        Required for MVP since we don't have authentication yet (auth.uid() is NULL).
        """
        if self._client is None:
            # Use service key for backend operations to bypass RLS
            service_key = settings.SUPABASE_SERVICE_KEY or settings.SUPABASE_ANON_KEY
            if not settings.SUPABASE_URL or not service_key:
                raise ValueError("Supabase URL and Service Key must be configured")
            self._client = create_client(
                settings.SUPABASE_URL,
                service_key
            )
        return self._client

    # ================================================
    # Profile Operations
    # ================================================

    async def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile by ID"""
        print(f"[DB] get_profile({user_id})")
        response = self.client.table("profiles").select("*").eq("id", user_id).limit(1).execute()
        return response.data[0] if response.data else None

    async def update_profile(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user profile"""
        print(f"[DB] update_profile({user_id})")
        response = self.client.table("profiles").update(data).eq("id", user_id).execute()
        return response.data[0] if response.data else {}

    # ================================================
    # Trip Operations
    # ================================================

    async def create_trip(self, user_id: str, title: str = "Untitled Trip", **kwargs) -> Dict[str, Any]:
        """Create a new trip for a user"""
        print(f"[DB] create_trip(user_id={user_id}, title={title})")
        trip_data = {
            "user_id": user_id,
            "title": title,
            **kwargs
        }
        response = self.client.table("trips").insert(trip_data).execute()
        return response.data[0] if response.data else {}

    async def get_trip(self, trip_id: str) -> Optional[Dict[str, Any]]:
        """Get trip by ID"""
        print(f"[DB] get_trip({trip_id})")
        response = self.client.table("trips").select("*").eq("id", trip_id).limit(1).execute()
        return response.data[0] if response.data else None

    async def get_user_trips(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all trips for a user"""
        print(f"[DB] get_user_trips({user_id})")
        response = self.client.table("trips").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        return response.data if response.data else []

    async def get_user_trips_with_thumbnails(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all trips for a user with thumbnail images from canvas state or board items"""
        print(f"[DB] get_user_trips_with_thumbnails({user_id})")

        # Get trips with their canvas states in one query
        response = self.client.table("trips").select(
            "*, canvas_states(scene_files)"
        ).eq("user_id", user_id).order("created_at", desc=True).execute()

        trips = response.data if response.data else []

        # Extract first image URL from each trip's canvas state or board items
        for trip in trips:
            thumbnail_url = None
            canvas_state = trip.pop("canvas_states", None)

            # Supabase may return the relation as a list or a dict
            if isinstance(canvas_state, list) and canvas_state:
                canvas_state = canvas_state[0]

            if canvas_state and isinstance(canvas_state, dict):
                scene_files = canvas_state.get("scene_files", {})
                if scene_files and isinstance(scene_files, dict):
                    # Get the first image URL from scene_files
                    for file_id, file_data in scene_files.items():
                        if isinstance(file_data, dict):
                            data_url = file_data.get("dataURL", "")
                            # Prefer HTTP URLs (easier to proxy/display)
                            if data_url.startswith("http"):
                                thumbnail_url = data_url
                                break
                            elif data_url.startswith("data:image"):
                                thumbnail_url = data_url
                                break

            # Fallback: extract image URL from board_items data
            if not thumbnail_url:
                board_items = trip.get("board_items") or []
                for item in board_items:
                    data = item.get("data", {})
                    img = data.get("image_url") or data.get("imageUrl") or data.get("image")
                    if img and isinstance(img, str) and img.startswith("http"):
                        thumbnail_url = img
                        break

            trip["thumbnail_url"] = thumbnail_url

        return trips

    async def update_trip(self, trip_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update trip data"""
        print(f"[DB] update_trip({trip_id})")
        response = self.client.table("trips").update(data).eq("id", trip_id).execute()
        return response.data[0] if response.data else {}

    async def delete_trip(self, trip_id: str) -> bool:
        """Delete a trip (cascades to canvas_states)"""
        print(f"[DB] delete_trip({trip_id})")
        response = self.client.table("trips").delete().eq("id", trip_id).execute()
        return len(response.data) > 0 if response.data else False

    async def get_trip_by_share_token(self, share_token: str) -> Optional[Dict[str, Any]]:
        """Get trip by share token (for public viewing)"""
        print(f"[DB] get_trip_by_share_token({share_token})")
        response = self.client.table("trips").select("*").eq("share_token", share_token).limit(1).execute()
        return response.data[0] if response.data else None

    async def set_share_token(self, trip_id: str, token: str) -> Dict[str, Any]:
        """Set the share token for a trip"""
        print(f"[DB] set_share_token({trip_id})")
        response = self.client.table("trips").update({"share_token": token}).eq("id", trip_id).execute()
        return response.data[0] if response.data else {}

    # ================================================
    # Canvas State Operations
    # ================================================

    async def get_canvas_state(self, trip_id: str) -> Optional[Dict[str, Any]]:
        """Get canvas state for a trip"""
        print(f"[DB] get_canvas_state({trip_id})")
        response = self.client.table("canvas_states").select("*").eq("trip_id", trip_id).limit(1).execute()
        return response.data[0] if response.data else None

    async def update_canvas_state(
        self,
        trip_id: str,
        scene_elements: List[Dict[str, Any]] = None,
        scene_files: Dict[str, Any] = None,
        scene_app_state: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Update canvas state for a trip (upsert to guarantee persistence)

        Args:
            trip_id: The trip ID
            scene_elements: Excalidraw elements array
            scene_files: Excalidraw files dictionary (for images)
            scene_app_state: Excalidraw app state
        """
        print(f"[DB] update_canvas_state({trip_id})")
        update_data = {}

        if scene_elements is not None:
            update_data["scene_elements"] = scene_elements
        if scene_files is not None:
            update_data["scene_files"] = scene_files
        if scene_app_state is not None:
            update_data["scene_app_state"] = scene_app_state

        if not update_data:
            return {}

        # Use upsert to ensure the row is created if it doesn't exist yet.
        # The trigger on trips should create canvas_states rows, but if it
        # hasn't fired (e.g. migration timing) the save would silently fail
        # with a plain UPDATE, leaving the shared board empty.
        upsert_data = {"trip_id": trip_id, **update_data}
        response = self.client.table("canvas_states").upsert(
            upsert_data, on_conflict="trip_id"
        ).execute()
        return response.data[0] if response.data else {}

    # ================================================
    # Board Items Operations
    # ================================================

    async def get_board_items(self, trip_id: str) -> List[Dict[str, Any]]:
        """Get board_items for a trip (list of agent-placed items)"""
        print(f"[DB] get_board_items({trip_id})")
        response = self.client.table("trips").select("board_items").eq("id", trip_id).limit(1).execute()
        if response.data and response.data[0].get("board_items"):
            return response.data[0]["board_items"]
        return []

    async def update_board_items(self, trip_id: str, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Update board_items for a trip"""
        print(f"[DB] update_board_items({trip_id})")
        response = self.client.table("trips").update({"board_items": items}).eq("id", trip_id).execute()
        return response.data[0] if response.data else {}

    # ================================================
    # Conversation Operations
    # ================================================

    async def get_or_create_conversation(self, trip_id: str, title: str = None) -> Dict[str, Any]:
        """
        Get existing conversation for a trip, or create one if it doesn't exist

        Args:
            trip_id: The trip ID
            title: Optional conversation title

        Returns:
            Conversation record
        """
        print(f"[DB] get_or_create_conversation({trip_id})")

        # Try to get existing conversation
        response = self.client.table("conversations").select("*").eq("trip_id", trip_id).limit(1).execute()

        if response.data and len(response.data) > 0:
            return response.data[0]

        # Create new conversation
        conversation_data = {"trip_id": trip_id}
        if title:
            conversation_data["title"] = title

        response = self.client.table("conversations").insert(conversation_data).execute()
        return response.data[0] if response.data else {}

    async def update_conversation(self, conversation_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update conversation metadata (title, cache_name, etc.)

        Args:
            conversation_id: The conversation ID
            data: Dictionary of fields to update

        Returns:
            Updated conversation record
        """
        print(f"[DB] update_conversation({conversation_id})")
        response = self.client.table("conversations").update(data).eq("id", conversation_id).execute()
        return response.data[0] if response.data else {}

    # ================================================
    # Message Operations
    # ================================================

    async def save_message(self, conversation_id: str, role: str, content: str) -> Dict[str, Any]:
        """
        Save a message to the database

        Args:
            conversation_id: The conversation ID
            role: 'user' or 'model' (Gemini roles)
            content: The message text

        Returns:
            Created message record
        """
        print(f"[DB] save_message(conversation_id={conversation_id}, role={role})")

        message_data = {
            "conversation_id": conversation_id,
            "role": role,
            "content": content
        }

        response = self.client.table("messages").insert(message_data).execute()
        return response.data[0] if response.data else {}

    async def load_messages(self, conversation_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Load message history from database

        Args:
            conversation_id: The conversation ID
            limit: Maximum number of recent messages to load (default: 20)

        Returns:
            List of message records ordered by created_at ASC (oldest first)
        """
        print(f"[DB] load_messages(conversation_id={conversation_id}, limit={limit})")

        response = self.client.table("messages") \
            .select("role, content, created_at") \
            .eq("conversation_id", conversation_id) \
            .order("created_at", desc=True) \
            .limit(limit) \
            .execute()

        # Reverse to get oldest-first order
        messages = list(reversed(response.data)) if response.data else []
        return messages

    # ================================================
    # Feedback Operations
    # ================================================

    async def save_feedback(self, user_id: str, username: str, feedback: str) -> Dict[str, Any]:
        """Save user feedback to the database"""
        print(f"[DB] save_feedback(user_id={user_id}, username={username})")
        feedback_data = {
            "user_id": user_id,
            "username": username,
            "feedback": feedback[:1000],  # Enforce 1000 char limit
        }
        response = self.client.table("user_feedback").insert(feedback_data).execute()
        return response.data[0] if response.data else {}


# Singleton instance
db = DatabaseService()

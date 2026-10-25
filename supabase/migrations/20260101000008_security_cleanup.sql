-- Security cleanup: remove the user-approval gate, drop public read policies
-- on trips/canvas_states (shared boards load via the backend service key),
-- and scope canvas-images writes to the uploader's own trips.

ALTER TABLE profiles DROP COLUMN is_approved;

DROP POLICY "Anyone can view shared trips" ON trips;
DROP POLICY "Anyone can view canvas for shared trips" ON canvas_states;

-- Objects live at canvas-images/{trip_id}/{file_id}.{ext}; only the trip owner may write.
DROP POLICY "Users can upload canvas images" ON storage.objects;
DROP POLICY "Users can update canvas images" ON storage.objects;
DROP POLICY "Users can delete canvas images" ON storage.objects;

CREATE POLICY "Users can upload canvas images"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (
  bucket_id = 'canvas-images'
  AND (storage.foldername(name))[1]::uuid IN (SELECT id FROM trips WHERE user_id = auth.uid())
);

CREATE POLICY "Users can update canvas images"
ON storage.objects FOR UPDATE
TO authenticated
USING (
  bucket_id = 'canvas-images'
  AND (storage.foldername(name))[1]::uuid IN (SELECT id FROM trips WHERE user_id = auth.uid())
);

CREATE POLICY "Users can delete canvas images"
ON storage.objects FOR DELETE
TO authenticated
USING (
  bucket_id = 'canvas-images'
  AND (storage.foldername(name))[1]::uuid IN (SELECT id FROM trips WHERE user_id = auth.uid())
);

-- Create a public storage bucket for user-uploaded canvas images.
-- Images are stored at: canvas-images/{trip_id}/{file_id}.{ext}
-- Being public means anyone with the URL can view (needed for shared boards).

INSERT INTO storage.buckets (id, name, public)
VALUES ('canvas-images', 'canvas-images', true)
ON CONFLICT (id) DO NOTHING;

-- Allow authenticated users to upload images (INSERT)
CREATE POLICY "Users can upload canvas images"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'canvas-images');

-- Allow anyone to view images (for shared boards)
CREATE POLICY "Public read access for canvas images"
ON storage.objects FOR SELECT
TO public
USING (bucket_id = 'canvas-images');

-- Allow authenticated users to overwrite their uploads (UPDATE)
CREATE POLICY "Users can update canvas images"
ON storage.objects FOR UPDATE
TO authenticated
USING (bucket_id = 'canvas-images');

-- Allow authenticated users to delete their uploads
CREATE POLICY "Users can delete canvas images"
ON storage.objects FOR DELETE
TO authenticated
USING (bucket_id = 'canvas-images');

-- Collection events: links events to collections with sort order
CREATE TABLE IF NOT EXISTS collection_events (
  id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  collection_id uuid REFERENCES collections(id) ON DELETE CASCADE NOT NULL,
  event_id bigint REFERENCES events(id) ON DELETE CASCADE NOT NULL,
  sort_order int DEFAULT 0,
  added_at timestamptz DEFAULT now(),
  UNIQUE(collection_id, event_id)
);

CREATE INDEX IF NOT EXISTS idx_collection_events_collection_id ON collection_events(collection_id);
CREATE INDEX IF NOT EXISTS idx_collection_events_event_id ON collection_events(event_id);

-- RLS: public SELECT, owner-only INSERT/DELETE (via join to collections.user_id)
ALTER TABLE collection_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY "collection_events_select_public"
  ON collection_events FOR SELECT
  USING (true);

CREATE POLICY "collection_events_insert_owner"
  ON collection_events FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM collections
      WHERE id = collection_id AND user_id = auth.uid()
    )
  );

CREATE POLICY "collection_events_delete_owner"
  ON collection_events FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM collections
      WHERE id = collection_id AND user_id = auth.uid()
    )
  );

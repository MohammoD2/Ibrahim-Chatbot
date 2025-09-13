-- Create the database
CREATE DATABASE file_metadata_db;

-- Connect to the database
\c file_metadata_db;

-- Create the file_metadata table
CREATE TABLE file_metadata (
    id SERIAL PRIMARY KEY,
    file_name VARCHAR(255) NOT NULL,
    file_key VARCHAR(255) UNIQUE NOT NULL,
    source_path TEXT NOT NULL,
    local_path TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX idx_file_name ON file_metadata(file_name);
CREATE INDEX idx_file_key ON file_metadata(file_key);

-- Add some helpful comments
COMMENT ON TABLE file_metadata IS 'Stores metadata for uploaded files';
COMMENT ON COLUMN file_metadata.id IS 'Unique identifier for each record';
COMMENT ON COLUMN file_metadata.file_name IS 'Name of the uploaded file';
COMMENT ON COLUMN file_metadata.file_key IS 'Unique key for the file';
COMMENT ON COLUMN file_metadata.source_path IS 'Original path of the file on the user''s PC';
COMMENT ON COLUMN file_metadata.local_path IS 'Path where the file is stored locally';
COMMENT ON COLUMN file_metadata.created_at IS 'Timestamp when the record was created'; 
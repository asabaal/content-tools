# Visual Content Database

A read-only HTML-based visual front end for browsing content records.

## Running the App

This app requires a local HTTP server due to browser security rules.

**Start a server:**
```bash
python3 -m http.server
```

**Then open:**
```
http://localhost:8000
```

**Important:** Opening `index.html` via file:// will not work.

## Data Ingestion

The system ingests all data from the `/data` directory.

### Required Data Files

#### content.csv
The canonical content index. Contains entries with the following fields:
- **content_id** (required) - Stable, unique identifier for each entry
- Month
- Week of x (date)
- Release Date (date)
- Show/Content Type
- Season (optional)
- Episode (optional)
- Media Source (optional)

#### media.json (optional)
Contains media attachment records. Each record includes:
- **content_id** - Links to the entry in content.csv
- **type** - "video", "audio", or "image"
- **source** - "local" or "remote"
- **path** (local only) - Relative path into `/media` directory
- **url** (remote only) - Full URL to the media
- **display** (optional) - "embed" or "link" (default: local=embed, remote=link)

### Media Attachment Modes

1. **Local Media**
   - Media files exist in the `/media` directory
   - Referenced by relative path in media.json

2. **Remote Media**
   - Media exists at remote URLs
   - Referenced by URL in media.json
   - Can be embedded (iframe/video/audio) or shown as a link

## Adding New Data Files

To add new content:
1. Add entries to content.csv with unique content_id values
2. Add media files to the `/media` directory (for local media)
3. Add media records to media.json linking content_id to media files
4. Reload the page to ingest the new data

**Note:** The system is read-only and will regenerate the UI on reload. No data files are written to or modified.

## Features

- Browse all content entries in a database table layout
- Filter by any available field
- Sort by Release Date (default)
- Click entries to view details in the details panel
- View attached media (video, audio, images)
- Support for local and remote media sources

## System Characteristics

- Desktop-first design
- No white backgrounds
- Colorful, vibrant UI
- Modular architecture with clear separation of concerns
- Forward-compatible for future media attachments

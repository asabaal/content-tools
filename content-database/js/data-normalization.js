const DataNormalization = {
    normalizeRows(rawRows) {
        return rawRows.map(row => this.normalizeRow(row));
    },

    normalizeRow(rawRow) {
        return {
            contentId: rawRow['content_id'] || '',
            month: rawRow['Month'] || '',
            weekOf: this.normalizeDate(rawRow['Week of x'] || rawRow['Week Of'] || ''),
            releaseDate: this.normalizeDate(rawRow['Release Date'] || ''),
            showType: rawRow['Show/Content Type'] || rawRow['Show or Content Type'] || '',
            season: rawRow['Season'] || '',
            episode: rawRow['Episode'] || '',
            mediaSource: rawRow['Media Source'] || '',
            attachedMedia: []
        };
    },

    attachMedia(entries, mediaRecords) {
        const mediaMap = {};

        mediaRecords.forEach(record => {
            const contentId = record.content_id;
            if (!mediaMap[contentId]) {
                mediaMap[contentId] = [];
            }
            mediaMap[contentId].push(record);
        });

        entries.forEach(entry => {
            if (mediaMap[entry.contentId]) {
                entry.attachedMedia = mediaMap[entry.contentId];
            }
        });
    },

    normalizeDate(dateString) {
        if (!dateString) return '';
        
        const date = new Date(dateString);
        if (isNaN(date.getTime())) return dateString;
        
        return date.toISOString().split('T')[0];
    },

    extractFilterOptions(entries) {
        const options = {};

        entries.forEach(entry => {
            Object.keys(entry).forEach(key => {
                if (key === 'contentId' || key === 'attachedMedia') return;
                
                const value = entry[key];
                if (value && value !== '') {
                    if (!options[key]) {
                        options[key] = new Set();
                    }
                    options[key].add(value);
                }
            });
        });

        Object.keys(options).forEach(key => {
            options[key] = Array.from(options[key]).sort();
        });

        return options;
    }
};

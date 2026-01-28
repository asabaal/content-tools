const Renderer = {
    monthNames: ['January', 'February', 'March', 'April', 'May', 'June', 
                 'July', 'August', 'September', 'October', 'November', 'December'],

    monthColors: [
        'rgba(255, 182, 193, 0.15)',   // January - light pink
        'rgba(173, 216, 230, 0.15)',   // February - light blue
        'rgba(144, 238, 144, 0.15)',   // March - light green
        'rgba(255, 218, 185, 0.15)',   // April - peach
        'rgba(221, 160, 221, 0.15)',   // May - plum
        'rgba(255, 255, 153, 0.15)',   // June - light yellow
        'rgba(255, 160, 122, 0.15)',   // July - light salmon
        'rgba(250, 128, 114, 0.12)',   // August - salmon
        'rgba(216, 191, 216, 0.15)',   // September - thistle
        'rgba(255, 200, 150, 0.15)',   // October - light orange
        'rgba(176, 224, 230, 0.15)',   // November - powder blue
        'rgba(255, 228, 225, 0.15)'    // December - misty rose
    ],

    getMonthName(monthValue) {
        const monthNum = parseInt(monthValue);
        if (isNaN(monthNum) || monthNum < 1 || monthNum > 12) {
            return monthValue || '-';
        }
        return this.monthNames[monthNum - 1];
    },

    getMonthColor(monthValue) {
        const monthNum = parseInt(monthValue);
        if (isNaN(monthNum) || monthNum < 1 || monthNum > 12) {
            return '';
        }
        return this.monthColors[monthNum - 1];
    },

    getShowColor(showName) {
        const colors = [
            'rgba(173, 216, 230, 0.12)',  // light blue
            'rgba(255, 182, 193, 0.12)',  // light pink
            'rgba(144, 238, 144, 0.12)',  // light green
            'rgba(255, 218, 185, 0.12)',  // peach
            'rgba(221, 160, 221, 0.12)',  // plum
            'rgba(255, 255, 153, 0.12)',  // light yellow
            'rgba(255, 160, 122, 0.12)',  // light salmon
            'rgba(230, 230, 250, 0.12)',  // lavender
            'rgba(152, 251, 152, 0.12)',  // pale green
            'rgba(255, 200, 150, 0.12)',  // light orange
            'rgba(176, 224, 230, 0.12)',  // powder blue
            'rgba(255, 228, 225, 0.12)',  // misty rose
            'rgba(135, 206, 250, 0.12)',  // light sky blue
            'rgba(255, 105, 180, 0.10)',  // hot pink (lighter)
            'rgba(154, 205, 50, 0.12)',   // yellow green
            'rgba(245, 222, 179, 0.12)',  // wheat
            'rgba(240, 128, 128, 0.12)',  // light coral
            'rgba(224, 255, 255, 0.12)',  // light cyan
            'rgba(250, 235, 215, 0.12)',  // antique white
            'rgba(238, 130, 238, 0.12)'   // violet (light)
        ];

        let hash1 = 0, hash2 = 0;
        for (let i = 0; i < showName.length; i++) {
            const char = showName.charCodeAt(i);
            hash1 = ((hash1 << 5) - hash1) + char;
            hash2 = ((hash2 << 3) - hash2) + char + i;
        }

        const combined = Math.abs(hash1 + hash2);
        const index = combined % colors.length;
        return colors[index];
    },

    renderFilterUI(filterOptions, onFilterChange) {
        const container = document.getElementById('filter-container');
        container.innerHTML = '';

        Object.keys(filterOptions).forEach(key => {
            const group = document.createElement('div');
            group.className = 'filter-group';

            const label = document.createElement('label');
            label.textContent = this.formatFilterLabel(key);
            group.appendChild(label);

            const select = document.createElement('select');
            select.id = `filter-${key}`;
            
            const allOption = document.createElement('option');
            allOption.value = '';
            allOption.textContent = 'All';
            select.appendChild(allOption);

            filterOptions[key].forEach(value => {
                const option = document.createElement('option');
                option.value = value;
                option.textContent = value;
                select.appendChild(option);
            });

            select.addEventListener('change', () => onFilterChange());
            group.appendChild(select);

            container.appendChild(group);
        });
    },

    formatFilterLabel(key) {
        return key.charAt(0).toUpperCase() + key.slice(1).replace(/([A-Z])/g, ' $1');
    },

    renderContentList(entries, onSelectEntry) {
        const container = document.getElementById('content-list');
        container.innerHTML = '';

        if (entries.length === 0) {
            container.innerHTML = '<div class="no-content">No content entries found</div>';
            return;
        }

        const table = document.createElement('table');
        table.className = 'content-table';

        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        
        const headers = ['Release Date', 'Show or Content Type', 'Season', 'Episode', 'Month', 'Media Source'];
        headers.forEach((header, index) => {
            const th = document.createElement('th');
            th.textContent = header;
            th.dataset.columnIndex = index;
            headerRow.appendChild(th);
        });
        
        thead.appendChild(headerRow);
        table.appendChild(thead);

        const tbody = document.createElement('tbody');
        entries.forEach(entry => {
            const row = this.createTableRow(entry, onSelectEntry);
            tbody.appendChild(row);
        });
        table.appendChild(tbody);

        container.appendChild(table);
    },

    createTableRow(entry, onSelectEntry) {
        const tr = document.createElement('tr');
        tr.className = 'table-row';
        tr.dataset.id = entry.contentId;

        tr.appendChild(this.createTableCell(entry.releaseDate || '-'));

        const showCell = this.createTableCell(entry.showType || 'Untitled');
        if (entry.showType) {
            const showColor = this.getShowColor(entry.showType);
            showCell.style.backgroundColor = showColor;
        }
        tr.appendChild(showCell);

        tr.appendChild(this.createTableCell(entry.season || '-'));
        tr.appendChild(this.createTableCell(entry.episode || '-'));

        const monthCell = this.createTableCell(this.getMonthName(entry.month));
        const monthColor = this.getMonthColor(entry.month);
        if (monthColor) {
            monthCell.style.backgroundColor = monthColor;
        }
        tr.appendChild(monthCell);

        tr.appendChild(this.createTableCell(entry.mediaSource || '-'));

        tr.addEventListener('click', () => onSelectEntry(entry));

        return tr;
    },

    createTableCell(text) {
        const td = document.createElement('td');
        td.textContent = text;
        return td;
    },

    renderDetailsPanel(entry) {
        const panel = document.getElementById('details-panel');
        const title = document.getElementById('details-title');
        const content = document.getElementById('details-content');

        title.textContent = entry.showType || 'Untitled';
        content.innerHTML = '';

        if (entry.contentId) {
            content.appendChild(this.createDetailItem('Content ID', entry.contentId));
        }

        const fields = [
            { key: 'releaseDate', label: 'Release Date' },
            { key: 'weekOf', label: 'Week Of' },
            { key: 'month', label: 'Month' },
            { key: 'season', label: 'Season' },
            { key: 'episode', label: 'Episode' },
            { key: 'mediaSource', label: 'Media Source' }
        ];

        fields.forEach(field => {
            if (entry[field.key] && entry[field.key] !== '') {
                content.appendChild(this.createDetailItem(field.label, entry[field.key]));
            }
        });

        this.renderAttachedMedia(entry);

        panel.classList.remove('hidden');
    },

    createDetailItem(label, value) {
        const div = document.createElement('div');
        div.className = 'detail-item';

        const labelEl = document.createElement('div');
        labelEl.className = 'detail-label';
        labelEl.textContent = label;
        div.appendChild(labelEl);

        const valueEl = document.createElement('div');
        valueEl.className = 'detail-value';
        valueEl.textContent = value;
        div.appendChild(valueEl);

        return div;
    },

    renderAttachedMedia(entry) {
        const container = document.getElementById('attached-content-items');
        
        if (entry.attachedMedia && entry.attachedMedia.length > 0) {
            container.innerHTML = '';
            entry.attachedMedia.forEach(media => {
                const mediaEl = this.createMediaElement(media);
                container.appendChild(mediaEl);
            });
        } else {
            container.innerHTML = '<div class="no-content">No media attached yet.</div>';
        }
    },

    createMediaElement(media) {
        const wrapper = document.createElement('div');
        wrapper.className = 'media-wrapper';

        const typeLabel = document.createElement('div');
        typeLabel.className = 'media-type-label';
        typeLabel.textContent = `${media.type.toUpperCase()} - ${media.source.toUpperCase()}`;
        wrapper.appendChild(typeLabel);

        if (media.source === 'local') {
            const element = this.createLocalMedia(media);
            wrapper.appendChild(element);
        } else if (media.source === 'remote') {
            const display = media.display || 'link';
            if (display === 'embed') {
                const element = this.createRemoteEmbed(media);
                if (element) {
                    wrapper.appendChild(element);
                } else {
                    wrapper.appendChild(this.createRemoteLink(media));
                }
            } else {
                wrapper.appendChild(this.createRemoteLink(media));
            }
        }

        return wrapper;
    },

    createLocalMedia(media) {
        const path = `media/${media.path}`;

        if (media.type === 'video') {
            const video = document.createElement('video');
            video.controls = true;
            video.style.width = '100%';
            video.style.maxHeight = '300px';
            video.style.borderRadius = '8px';
            const source = document.createElement('source');
            source.src = path;
            source.type = 'video/mp4';
            video.appendChild(source);
            return video;
        } else if (media.type === 'audio') {
            const audio = document.createElement('audio');
            audio.controls = true;
            audio.style.width = '100%';
            const source = document.createElement('source');
            source.src = path;
            audio.appendChild(source);
            return audio;
        } else if (media.type === 'image') {
            const img = document.createElement('img');
            img.src = path;
            img.style.width = '100%';
            img.style.maxHeight = '300px';
            img.style.borderRadius = '8px';
            img.style.objectFit = 'contain';
            return img;
        }
    },

    createRemoteEmbed(media) {
        if (media.type === 'video') {
            const video = document.createElement('video');
            video.controls = true;
            video.style.width = '100%';
            video.style.maxHeight = '300px';
            video.style.borderRadius = '8px';
            const source = document.createElement('source');
            source.src = media.url;
            source.type = 'video/mp4';
            video.appendChild(source);
            return video;
        } else if (media.type === 'audio') {
            const audio = document.createElement('audio');
            audio.controls = true;
            audio.style.width = '100%';
            const source = document.createElement('source');
            source.src = media.url;
            audio.appendChild(source);
            return audio;
        }
        return null;
    },

    createRemoteLink(media) {
        const link = document.createElement('a');
        link.href = media.url;
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
        link.className = 'media-link';
        link.innerHTML = `
            <span class="media-link-icon">🔗</span>
            <span class="media-link-text">View ${media.type} (external)</span>
        `;
        return link;
    },

    hideDetailsPanel() {
        const panel = document.getElementById('details-panel');
        panel.classList.add('hidden');
    },

    highlightSelectedEntry(entryId) {
        document.querySelectorAll('.table-row').forEach(el => {
            el.classList.remove('selected');
        });

        if (entryId) {
            const selected = document.querySelector(`[data-id="${entryId}"]`);
            if (selected) {
                selected.classList.add('selected');
                selected.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }
    }
};

const DataIngestion = {
    checkProtocol() {
        if (window.location.protocol === 'file:') {
            throw new Error('file:// protocol detected');
        }
    },

    async loadCSVFiles(dataPath = 'data/') {
        try {
            this.checkProtocol();
            
            const response = await fetch(`${dataPath}content.csv`);
            if (!response.ok) {
                throw new Error(`Failed to load content.csv: ${response.statusText}`);
            }
            const csvText = await response.text();
            return this.parseCSV(csvText);
        } catch (error) {
            console.error('Error loading CSV file:', error);
            throw error;
        }
    },

    async loadMediaJSON(dataPath = 'data/') {
        try {
            this.checkProtocol();
            
            const response = await fetch(`${dataPath}media.json`);
            if (!response.ok) {
                if (response.status === 404) {
                    return [];
                }
                throw new Error(`Failed to load media.json: ${response.statusText}`);
            }
            const data = await response.json();
            return data;
        } catch (error) {
            if (error.message.includes('404')) {
                return [];
            }
            console.error('Error loading media.json:', error);
            throw error;
        }
    },

    parseCSV(csvText) {
        const lines = csvText.trim().split('\n');
        if (lines.length < 2) {
            return [];
        }

        const headers = lines[0].split(',').map(h => h.trim());
        const rows = [];

        for (let i = 1; i < lines.length; i++) {
            const values = this.parseCSVLine(lines[i]);
            if (values.length === headers.length) {
                const row = {};
                headers.forEach((header, index) => {
                    row[header] = values[index] ? values[index].trim() : '';
                });
                rows.push(row);
            }
        }

        return rows;
    },

    parseCSVLine(line) {
        const result = [];
        let current = '';
        let inQuotes = false;

        for (let i = 0; i < line.length; i++) {
            const char = line[i];
            if (char === '"') {
                inQuotes = !inQuotes;
            } else if (char === ',' && !inQuotes) {
                result.push(current);
                current = '';
            } else {
                current += char;
            }
        }
        result.push(current);
        return result;
    }
};

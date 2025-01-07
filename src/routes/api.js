const express = require('express');
const router = express.Router();
const { apiClient } = require('../utils/apiClient');
const { logger } = require('../utils/logger');

// Get latest papers
router.get('/papers/latest', async (req, res) => {
    try {
        const papers = await apiClient.getLatestPapers(req.query.limit);
        res.json(papers);
    } catch (error) {
        logger.error('API - Failed to get latest papers:', error);
        res.status(500).json({ error: 'Failed to fetch latest papers' });
    }
});

// Search papers
router.get('/papers/search', async (req, res) => {
    try {
        const results = await apiClient.searchPapers(
            req.query.q,
            req.query.page,
            req.query.limit
        );
        res.json(results);
    } catch (error) {
        logger.error('API - Search failed:', error);
        res.status(500).json({ error: 'Search failed' });
    }
});

// Get nodes
router.get('/nodes', async (req, res) => {
    try {
        const nodes = await apiClient.getNodes();
        res.json(nodes);
    } catch (error) {
        logger.error('API - Failed to get nodes:', error);
        res.status(500).json({ error: 'Failed to fetch nodes' });
    }
});

// Get stats
router.get('/stats', async (req, res) => {
    try {
        const stats = await apiClient.getStats();
        res.json(stats);
    } catch (error) {
        logger.error('API - Failed to get stats:', error);
        res.status(500).json({ error: 'Failed to fetch stats' });
    }
});

module.exports = router; 
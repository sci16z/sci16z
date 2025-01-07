const express = require('express');
const router = express.Router();
const { apiClient } = require('../utils/apiClient');
const { logger } = require('../utils/logger');

router.get('/', async (req, res) => {
    try {
        const latestPapers = await apiClient.getLatestPapers(6);
        res.render('index', { 
            title: 'Sci16z - Decentralized AI Paper Analysis',
            papers: latestPapers
        });
    } catch (error) {
        logger.error('Error loading home page:', error);
        res.render('index', { 
            title: 'Sci16z - Decentralized AI Paper Analysis',
            papers: [],
            error: 'Failed to load latest papers'
        });
    }
});

router.get('/search', async (req, res) => {
    const { q, page = 1 } = req.query;
    try {
        const results = await apiClient.searchPapers(q, page);
        res.render('search', {
            title: `Search Results for "${q}" - Sci16z`,
            query: q,
            results,
            page: parseInt(page)
        });
    } catch (error) {
        logger.error('Search error:', error);
        res.render('search', {
            title: 'Search Results - Sci16z',
            query: q,
            results: { papers: [], total: 0 },
            page: parseInt(page),
            error: 'Search failed'
        });
    }
});

module.exports = router; 
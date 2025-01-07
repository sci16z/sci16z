const express = require('express');
const router = express.Router();
const { apiClient } = require('../utils/apiClient');
const { logger } = require('../utils/logger');

router.get('/', async (req, res) => {
    try {
        const [nodes, stats] = await Promise.all([
            apiClient.getNodes(),
            apiClient.getStats()
        ]);

        res.render('dashboard', {
            title: 'Dashboard - Sci16z',
            nodes,
            stats,
            defaultNode: {
                id: 'node-001',
                status: 'Active',
                uptime: 99.9,
                papersProcessed: 1234,
                tokensPerHour: 5.6,
                lastSeen: new Date()
            }
        });
    } catch (error) {
        logger.error('Error loading dashboard:', error);
        res.render('dashboard', {
            title: 'Dashboard - Sci16z',
            nodes: [],
            stats: {
                activeNodes: 1,
                papersProcessed: 0,
                tokensEarned: 0
            },
            defaultNode: {
                id: 'node-001',
                status: 'Active',
                uptime: 99.9,
                papersProcessed: 1234,
                tokensPerHour: 5.6,
                lastSeen: new Date()
            },
            error: 'Failed to load dashboard data'
        });
    }
});

module.exports = router; 
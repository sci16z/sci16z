const axios = require('axios');
const { logger } = require('./logger');

class ApiClient {
    constructor() {
        this.client = axios.create({
            baseURL: process.env.POOL_URL,
            timeout: 5000,
            headers: {
                'Authorization': `Bearer ${process.env.POOL_API_KEY}`
            }
        });
    }

    async searchPapers(query, page = 1, limit = 10) {
        try {
            const response = await this.client.get('/papers/search', {
                params: { query, page, limit }
            });
            return response.data;
        } catch (error) {
            logger.error('Failed to search papers:', error);
            throw error;
        }
    }

    async getLatestPapers(limit = 10) {
        try {
            const response = await this.client.get('/papers/latest', {
                params: { limit }
            });
            return response.data;
        } catch (error) {
            logger.error('Failed to get latest papers:', error);
            throw error;
        }
    }

    async getNodes() {
        try {
            const response = await this.client.get('/nodes');
            return response.data;
        } catch (error) {
            logger.error('Failed to get nodes:', error);
            throw error;
        }
    }

    async getStats() {
        try {
            const response = await this.client.get('/stats');
            return response.data;
        } catch (error) {
            logger.error('Failed to get stats:', error);
            throw error;
        }
    }

    async getPaperById(id) {
        try {
            const response = await this.client.get(`/papers/${id}`);
            return response.data;
        } catch (error) {
            logger.error(`Failed to get paper ${id}:`, error);
            throw error;
        }
    }
}

module.exports = {
    apiClient: new ApiClient()
}; 
require('dotenv').config();
const express = require('express');
const path = require('path');
const helmet = require('helmet');
const compression = require('compression');
const morgan = require('morgan');
const { logger } = require('./utils/logger');
const { apiClient } = require('./utils/apiClient');

// Import routes
const indexRouter = require('./routes/index');
const dashboardRouter = require('./routes/dashboard');
const apiRouter = require('./routes/api');

const app = express();

// View engine setup
app.set('views', path.join(__dirname, 'views'));
app.set('view engine', 'ejs');

// Middleware
app.use(helmet());
app.use(compression());
app.use(morgan('combined', { stream: { write: message => logger.info(message.trim()) } }));
app.use(express.json());
app.use(express.urlencoded({ extended: false }));
app.use(express.static(path.join(__dirname, 'public')));
app.use('/assets', express.static(path.join(__dirname, 'public/assets')));

// Routes
app.use('/', indexRouter);
app.use('/dashboard', dashboardRouter);
app.use('/api', apiRouter);

// Error handler
app.use((err, req, res, next) => {
    logger.error(err.stack);
    res.status(err.status || 500).render('error', {
        message: err.message,
        error: process.env.NODE_ENV === 'development' ? err : {}
    });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    logger.info(`Server is running on port ${PORT}`);
});

module.exports = app; 
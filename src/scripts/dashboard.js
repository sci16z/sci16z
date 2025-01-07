document.addEventListener('DOMContentLoaded', () => {
    // Initialize dashboard
    updateStats();
    loadNodes();
    
    // Update stats every minute
    setInterval(updateStats, 60000);
});

async function updateStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();
        
        document.getElementById('active-nodes').textContent = stats.activeNodes;
        document.getElementById('papers-processed').textContent = stats.papersProcessed.toLocaleString();
        document.getElementById('tokens-earned').textContent = stats.tokensEarned.toLocaleString();
    } catch (error) {
        console.error('Failed to update stats:', error);
    }
}

async function loadNodes() {
    const nodesGrid = document.getElementById('nodes-grid');
    const emptyState = nodesGrid.querySelector('.empty-state');
    
    try {
        const response = await fetch('/api/nodes');
        const nodes = await response.json();
        
        if (nodes.length <= 1) { // Only default node
            emptyState.classList.remove('hidden');
            return;
        }
        
        nodes.forEach(node => {
            if (node.id !== 'node-001') { // Skip default node
                const nodeCard = createNodeCard(node);
                nodesGrid.appendChild(nodeCard);
            }
        });
    } catch (error) {
        console.error('Failed to load nodes:', error);
        emptyState.classList.remove('hidden');
    }
}

function createNodeCard(node) {
    const card = document.createElement('div');
    card.className = 'node-card';
    card.innerHTML = `
        <div class="node-header">
            <h3>${node.id}</h3>
            <span class="status ${node.status.toLowerCase()}">${node.status}</span>
        </div>
        <div class="node-stats">
            <div class="stat">
                <label>Uptime</label>
                <span>${node.uptime}%</span>
            </div>
            <div class="stat">
                <label>Papers Processed</label>
                <span>${node.papersProcessed.toLocaleString()}</span>
            </div>
            <div class="stat">
                <label>Tokens/Hour</label>
                <span>${node.tokensPerHour}</span>
            </div>
        </div>
        <div class="node-footer">
            <span class="last-seen">Last seen: ${formatLastSeen(node.lastSeen)}</span>
        </div>
    `;
    return card;
}

function formatLastSeen(timestamp) {
    const diff = Date.now() - new Date(timestamp);
    const minutes = Math.floor(diff / 60000);
    
    if (minutes < 1) return 'Just now';
    if (minutes === 1) return '1 minute ago';
    if (minutes < 60) return `${minutes} minutes ago`;
    
    const hours = Math.floor(minutes / 60);
    if (hours === 1) return '1 hour ago';
    if (hours < 24) return `${hours} hours ago`;
    
    const days = Math.floor(hours / 24);
    if (days === 1) return '1 day ago';
    return `${days} days ago`;
} 
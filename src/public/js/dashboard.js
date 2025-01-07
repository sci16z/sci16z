// Add download tracking
async function trackDownload(fileId) {
    try {
        const nodeId = localStorage.getItem('nodeId') || 'anonymous';
        await fetch('/api/downloads/track', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                fileId: fileId,
                nodeId: nodeId
            })
        });
    } catch (error) {
        console.error('Failed to track download:', error);
    }
}

// Update download button handler
document.querySelector('.download-installer').addEventListener('click', async (e) => {
    e.preventDefault();
    
    // Track the download
    await trackDownload('installer.sh');
    
    // Start the download
    window.location.href = '/api/downloads/installer.sh';
}); 
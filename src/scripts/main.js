document.addEventListener('DOMContentLoaded', () => {
    // Load latest papers
    loadLatestPapers();
});

async function loadLatestPapers() {
    const papersGrid = document.getElementById('papers-grid');
    const emptyState = papersGrid.querySelector('.empty-state');
    
    try {
        const response = await fetch('/api/papers/latest');
        const papers = await response.json();
        
        if (papers.length === 0) {
            emptyState.classList.remove('hidden');
            return;
        }
        
        papers.forEach(paper => {
            const paperCard = createPaperCard(paper);
            papersGrid.appendChild(paperCard);
        });
    } catch (error) {
        console.error('Failed to load papers:', error);
        emptyState.classList.remove('hidden');
    }
}

function createPaperCard(paper) {
    const card = document.createElement('div');
    card.className = 'paper-card';
    card.innerHTML = `
        <h3>${paper.title}</h3>
        <p class="authors">${paper.authors.join(', ')}</p>
        <p class="abstract">${paper.abstract.substring(0, 200)}...</p>
        <div class="paper-footer">
            <span class="date">${new Date(paper.date).toLocaleDateString()}</span>
            <a href="/paper/${paper.id}" class="read-more">Read More</a>
        </div>
    `;
    return card;
} 
import re
from typing import Dict, Any, List
from utils.logger import get_logger
from core.model_manager import ModelManager

class PaperAnalyzer:
    def __init__(self, model_manager: ModelManager):
        self.logger = get_logger(__name__)
        self.model = model_manager
        self.max_section_length = 2000
        self.max_total_length = 8000

    async def analyze(self, text: str) -> Dict[str, Any]:
        """Analyze paper content"""
        try:
            # Preprocess text
            sections = self._split_sections(text)
            cleaned_sections = self._clean_sections(sections)
            
            # Extract key information
            title = await self._extract_title(cleaned_sections)
            abstract = await self._extract_abstract(cleaned_sections)
            keywords = await self._extract_keywords(abstract)
            
            # Analyze content
            main_points = await self._analyze_main_points(cleaned_sections)
            methodology = await self._analyze_methodology(cleaned_sections)
            findings = await self._analyze_findings(cleaned_sections)
            
            return {
                'title': title,
                'abstract': abstract,
                'keywords': keywords,
                'main_points': main_points,
                'methodology': methodology,
                'findings': findings
            }
            
        except Exception as e:
            self.logger.error(f"Failed to analyze paper: {str(e)}")
            raise

    def _split_sections(self, text: str) -> List[Dict[str, str]]:
        """Split paper into sections"""
        sections = []
        current_section = {'title': '', 'content': ''}
        
        for line in text.split('\n'):
            if self._is_section_header(line):
                if current_section['content']:
                    sections.append(current_section)
                current_section = {
                    'title': line.strip(),
                    'content': ''
                }
            else:
                current_section['content'] += line + '\n'
                
        if current_section['content']:
            sections.append(current_section)
            
        return sections

    def _clean_sections(self, sections: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Clean and normalize section content"""
        cleaned = []
        for section in sections:
            # Remove citations
            content = re.sub(r'\[\d+\]', '', section['content'])
            
            # Remove extra whitespace
            content = ' '.join(content.split())
            
            # Truncate long sections
            if len(content) > self.max_section_length:
                content = content[:self.max_section_length] + '...'
                
            cleaned.append({
                'title': section['title'],
                'content': content
            })
            
        return cleaned

    def _is_section_header(self, line: str) -> bool:
        """Check if line is a section header"""
        line = line.strip().lower()
        headers = ['abstract', 'introduction', 'background', 'methodology', 
                  'methods', 'results', 'discussion', 'conclusion']
        return any(line.startswith(h) for h in headers)

    async def _extract_title(self, sections: List[Dict[str, str]]) -> str:
        """Extract paper title"""
        # TODO: Implement title extraction
        return sections[0]['content'].split('\n')[0] if sections else ''

    async def _extract_abstract(self, sections: List[Dict[str, str]]) -> str:
        """Extract paper abstract"""
        for section in sections:
            if 'abstract' in section['title'].lower():
                return section['content']
        return ''

    async def _extract_keywords(self, abstract: str) -> List[str]:
        """Extract keywords from abstract"""
        # TODO: Implement keyword extraction using model
        return []

    async def _analyze_main_points(self, sections: List[Dict[str, str]]) -> List[str]:
        """Analyze main points of the paper"""
        # TODO: Implement main points analysis using model
        return []

    async def _analyze_methodology(self, sections: List[Dict[str, str]]) -> Dict[str, Any]:
        """Analyze research methodology"""
        # TODO: Implement methodology analysis using model
        return {}

    async def _analyze_findings(self, sections: List[Dict[str, str]]) -> List[str]:
        """Analyze research findings"""
        # TODO: Implement findings analysis using model
        return [] 
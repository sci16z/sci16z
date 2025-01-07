import os
import fitz  # PyMuPDF
from typing import Dict, Any, Optional, List
from utils.logger import get_logger
from network.downloader import Downloader

class PDFProcessor:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.downloader = Downloader()
        self.cache_dir = os.path.join(os.path.dirname(__file__), '../cache/pdf')
        os.makedirs(self.cache_dir, exist_ok=True)

    async def process(self, url: str) -> Optional[Dict[str, Any]]:
        """Process PDF document"""
        try:
            # Download PDF
            pdf_path = await self.download(url)
            if not pdf_path:
                return None
                
            # Extract content
            content = await self.extract_content(pdf_path)
            if not content:
                return None
                
            # Clean up temporary file
            os.remove(pdf_path)
            
            return content
            
        except Exception as e:
            self.logger.error(f"Failed to process PDF: {str(e)}")
            return None

    async def download(self, url: str) -> Optional[str]:
        """Download PDF file"""
        try:
            filename = os.path.join(
                self.cache_dir,
                f"{hash(url)}.pdf"
            )
            
            # Check cache first
            if os.path.exists(filename):
                return filename
                
            return await self.downloader.download_file(url, filename)
            
        except Exception as e:
            self.logger.error(f"Failed to download PDF: {str(e)}")
            return None

    async def extract_content(self, pdf_path: str) -> Optional[Dict[str, Any]]:
        """Extract content from PDF"""
        try:
            doc = fitz.open(pdf_path)
            
            content = {
                'metadata': self._extract_metadata(doc),
                'text': self._extract_text(doc),
                'sections': self._extract_sections(doc),
                'figures': await self._extract_figures(doc),
                'tables': await self._extract_tables(doc),
                'references': self._extract_references(doc)
            }
            
            doc.close()
            return content
            
        except Exception as e:
            self.logger.error(f"Failed to extract PDF content: {str(e)}")
            return None

    def _extract_metadata(self, doc: fitz.Document) -> Dict[str, Any]:
        """Extract PDF metadata"""
        try:
            metadata = doc.metadata
            return {
                'title': metadata.get('title', ''),
                'author': metadata.get('author', ''),
                'subject': metadata.get('subject', ''),
                'keywords': metadata.get('keywords', ''),
                'creator': metadata.get('creator', ''),
                'producer': metadata.get('producer', ''),
                'creation_date': metadata.get('creationDate', ''),
                'modification_date': metadata.get('modDate', ''),
                'page_count': doc.page_count
            }
        except Exception as e:
            self.logger.error(f"Failed to extract metadata: {str(e)}")
            return {}

    def _extract_text(self, doc: fitz.Document) -> str:
        """Extract text content"""
        try:
            text = ""
            for page in doc:
                text += page.get_text()
            return text
        except Exception as e:
            self.logger.error(f"Failed to extract text: {str(e)}")
            return ""

    def _extract_sections(self, doc: fitz.Document) -> List[Dict[str, Any]]:
        """Extract document sections"""
        try:
            sections = []
            current_section = {'title': '', 'content': '', 'page': 0}
            
            for page_num, page in enumerate(doc):
                blocks = page.get_text("dict")["blocks"]
                for block in blocks:
                    if block.get("type") == 0:  # Text block
                        text = ' '.join(line["text"] for line in block["lines"])
                        
                        # Check if this is a section header
                        if self._is_section_header(text, block):
                            if current_section['content']:
                                sections.append(current_section)
                            current_section = {
                                'title': text.strip(),
                                'content': '',
                                'page': page_num + 1
                            }
                        else:
                            current_section['content'] += text + '\n'
            
            if current_section['content']:
                sections.append(current_section)
                
            return sections
            
        except Exception as e:
            self.logger.error(f"Failed to extract sections: {str(e)}")
            return []

    async def _extract_figures(self, doc: fitz.Document) -> List[Dict[str, Any]]:
        """Extract figures from PDF"""
        try:
            figures = []
            for page_num, page in enumerate(doc):
                image_list = page.get_images()
                for img_index, img in enumerate(image_list):
                    try:
                        xref = img[0]
                        base_image = doc.extract_image(xref)
                        
                        # Save image temporarily
                        img_path = os.path.join(
                            self.cache_dir,
                            f"fig_{page_num}_{img_index}.{base_image['ext']}"
                        )
                        
                        with open(img_path, "wb") as f:
                            f.write(base_image["image"])
                            
                        figures.append({
                            'page': page_num + 1,
                            'path': img_path,
                            'type': base_image['ext'],
                            'size': len(base_image["image"])
                        })
                        
                    except Exception as e:
                        self.logger.warning(f"Failed to extract figure: {str(e)}")
                        continue
                        
            return figures
            
        except Exception as e:
            self.logger.error(f"Failed to extract figures: {str(e)}")
            return []

    async def _extract_tables(self, doc: fitz.Document) -> List[Dict[str, Any]]:
        """Extract tables from PDF"""
        # TODO: Implement table extraction
        return []

    def _extract_references(self, doc: fitz.Document) -> List[Dict[str, str]]:
        """Extract references from PDF"""
        # TODO: Implement reference extraction
        return []

    def _is_section_header(self, text: str, block: Dict[str, Any]) -> bool:
        """Check if text block is a section header"""
        try:
            # Check text characteristics
            text = text.strip().lower()
            if not text:
                return False
                
            # Common section headers
            headers = [
                'abstract', 'introduction', 'background',
                'methodology', 'methods', 'results',
                'discussion', 'conclusion', 'references'
            ]
            
            # Check if text starts with a common header
            is_common_header = any(text.startswith(h) for h in headers)
            
            # Check text formatting (size, bold, etc.)
            is_formatted = (
                block.get("lines", [{}])[0]
                .get("spans", [{}])[0]
                .get("flags", 0) & 2**4  # Check if bold
            )
            
            return is_common_header or is_formatted
            
        except Exception:
            return False 
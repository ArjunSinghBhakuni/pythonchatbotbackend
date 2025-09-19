import fitz  # PyMuPDF
import re
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class PDFProcessor:
    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF file"""
        try:
            doc = fitz.open(pdf_path)
            text = ""
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text += page.get_text()
                text += "\n"  # Add newline between pages
            
            doc.close()
            logger.info(f"Extracted text from PDF: {len(text)} characters")
            return text
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise
    
    def extract_text_from_pdf_content(self, pdf_content: bytes) -> str:
        """Extract text from PDF content (bytes)"""
        try:
            doc = fitz.open(stream=pdf_content, filetype="pdf")
            text = ""
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text += page.get_text()
                text += "\n"  # Add newline between pages
            
            doc.close()
            logger.info(f"Extracted text from PDF content: {len(text)} characters")
            return text
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF content: {e}")
            raise
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\[\]\"\']', ' ', text)
        
        # Remove multiple spaces
        text = re.sub(r' +', ' ', text)
        
        return text.strip()
    
    def split_text_into_chunks(self, text: str) -> List[Dict[str, Any]]:
        """Split text into overlapping chunks"""
        cleaned_text = self.clean_text(text)
        
        # Split by sentences first
        sentences = re.split(r'(?<=[.!?])\s+', cleaned_text)
        
        chunks = []
        current_chunk = ""
        chunk_index = 0
        
        for sentence in sentences:
            # If adding this sentence would exceed chunk size, save current chunk
            if len(current_chunk) + len(sentence) > self.chunk_size and current_chunk:
                chunks.append({
                    'content': current_chunk.strip(),
                    'chunk_index': chunk_index,
                    'metadata': {
                        'chunk_size': len(current_chunk),
                        'word_count': len(current_chunk.split())
                    }
                })
                chunk_index += 1
                
                # Start new chunk with overlap
                overlap_text = current_chunk[-self.chunk_overlap:] if len(current_chunk) > self.chunk_overlap else current_chunk
                current_chunk = overlap_text + " " + sentence
            else:
                current_chunk += " " + sentence if current_chunk else sentence
        
        # Add the last chunk if it has content
        if current_chunk.strip():
            chunks.append({
                'content': current_chunk.strip(),
                'chunk_index': chunk_index,
                'metadata': {
                    'chunk_size': len(current_chunk),
                    'word_count': len(current_chunk.split())
                }
            })
        
        logger.info(f"Created {len(chunks)} chunks from text")
        return chunks
    
    def chunk_text(self, text: str) -> List[str]:
        """Simple chunking method that returns list of strings"""
        chunks = self.split_text_into_chunks(text)
        return [chunk['content'] for chunk in chunks]
    
    def process_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Complete PDF processing pipeline"""
        try:
            # Extract text
            text = self.extract_text_from_pdf(pdf_path)
            
            # Split into chunks
            chunks = self.split_text_into_chunks(text)
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error processing PDF: {e}")
            raise


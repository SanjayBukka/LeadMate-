"""
Text Chunking Utility
Split text into manageable chunks for embeddings
"""
from typing import List


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """
    Split text into overlapping chunks
    
    Args:
        text: Input text to chunk
        chunk_size: Size of each chunk in characters
        overlap: Number of overlapping characters between chunks
    
    Returns:
        List of text chunks
    """
    if not text or len(text) == 0:
        return []
    
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        # Calculate end position
        end = start + chunk_size
        
        # If this is not the last chunk, try to break at a sentence or word boundary
        if end < text_length:
            # Look for sentence boundary (. ! ?)
            for i in range(end, max(start + chunk_size - 100, start), -1):
                if text[i] in '.!?\n':
                    end = i + 1
                    break
            else:
                # If no sentence boundary, look for word boundary
                for i in range(end, max(start + chunk_size - 50, start), -1):
                    if text[i].isspace():
                        end = i
                        break
        
        # Extract chunk
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # Move start position with overlap
        start = end - overlap if end < text_length else text_length
    
    return chunks


def chunk_text_by_paragraphs(text: str, max_chunk_size: int = 1000) -> List[str]:
    """
    Split text by paragraphs, combining small paragraphs into larger chunks
    
    Args:
        text: Input text to chunk
        max_chunk_size: Maximum size of each chunk
    
    Returns:
        List of text chunks
    """
    if not text:
        return []
    
    # Split by double newlines (paragraphs)
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    
    chunks = []
    current_chunk = ""
    
    for paragraph in paragraphs:
        # If adding this paragraph would exceed max size, save current chunk
        if current_chunk and len(current_chunk) + len(paragraph) + 2 > max_chunk_size:
            chunks.append(current_chunk.strip())
            current_chunk = paragraph
        else:
            # Add paragraph to current chunk
            if current_chunk:
                current_chunk += "\n\n" + paragraph
            else:
                current_chunk = paragraph
    
    # Add remaining chunk
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks


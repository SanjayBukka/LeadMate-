"""
Clean ChromaDB Script
Removes all ChromaDB data for testing from scratch
"""
import shutil
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def clean_chromadb(base_path: str = "./chroma_db"):
    """
    Clean all ChromaDB data
    
    WARNING: This will delete all ChromaDB data!
    Use this for testing from scratch.
    """
    base = Path(base_path)
    
    if not base.exists():
        logger.info(f"ChromaDB directory {base_path} does not exist. Nothing to clean.")
        return
    
    try:
        # Count files before deletion
        file_count = sum(1 for _ in base.rglob("*") if _.is_file())
        
        # Delete the entire directory
        shutil.rmtree(base)
        
        # Recreate empty directory
        base.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"✅ Cleaned ChromaDB: Removed {file_count} files")
        logger.info(f"ChromaDB directory reset: {base_path}")
        
    except Exception as e:
        logger.error(f"Error cleaning ChromaDB: {e}")
        raise


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        path = "./chroma_db"
    
    print("⚠️  WARNING: This will delete all ChromaDB data!")
    response = input("Are you sure? Type 'yes' to continue: ")
    
    if response.lower() == 'yes':
        clean_chromadb(path)
        print("✅ ChromaDB cleaned successfully!")
    else:
        print("❌ Cancelled.")


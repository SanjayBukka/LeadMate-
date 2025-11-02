"""
ChromaDB Cleanup Script
Clears all ChromaDB data for fresh testing
"""
import os
import shutil
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clear_chromadb(base_path: str = "./chroma_db"):
    """
    Clear all ChromaDB data
    
    Args:
        base_path: Path to ChromaDB directory
    """
    try:
        chromadb_path = Path(base_path)
        
        if not chromadb_path.exists():
            logger.info("ChromaDB directory doesn't exist. Nothing to clear.")
            return {
                "success": True,
                "message": "ChromaDB directory doesn't exist",
                "cleared": False
            }
        
        logger.info(f"Starting ChromaDB cleanup from: {chromadb_path.absolute()}")
        
        # Count items before deletion
        company_dirs = list(chromadb_path.glob("company_*"))
        total_items = len(list(chromadb_path.rglob("*"))) if chromadb_path.exists() else 0
        
        # Remove all contents
        for item in chromadb_path.iterdir():
            if item.is_dir():
                logger.info(f"Removing directory: {item.name}")
                shutil.rmtree(item)
            elif item.is_file():
                logger.info(f"Removing file: {item.name}")
                item.unlink()
        
        # Also check for chroma.sqlite3 at root level
        sqlite_file = chromadb_path / "chroma.sqlite3"
        if sqlite_file.exists():
            sqlite_file.unlink()
            logger.info("Removed chroma.sqlite3")
        
        logger.info(f"✅ ChromaDB cleanup complete! Removed {total_items} items from {len(company_dirs)} company directories")
        
        return {
            "success": True,
            "message": f"Cleared ChromaDB: {total_items} items from {len(company_dirs)} company directories",
            "items_cleared": total_items,
            "company_directories_cleared": len(company_dirs),
            "path": str(chromadb_path.absolute())
        }
        
    except Exception as e:
        logger.error(f"Error clearing ChromaDB: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"Error clearing ChromaDB: {str(e)}",
            "error": str(e)
        }


def clear_specific_company(company_id: str, base_path: str = "./chroma_db"):
    """
    Clear ChromaDB data for a specific company
    
    Args:
        company_id: Company/startup ID
        base_path: Path to ChromaDB directory
    """
    try:
        chromadb_path = Path(base_path)
        company_path = chromadb_path / f"company_{company_id}"
        
        if not company_path.exists():
            logger.info(f"Company directory doesn't exist: {company_path}")
            return {
                "success": True,
                "message": f"Company {company_id} directory doesn't exist",
                "cleared": False
            }
        
        logger.info(f"Clearing ChromaDB for company: {company_id}")
        
        # Count items
        total_items = len(list(company_path.rglob("*")))
        
        # Remove company directory
        shutil.rmtree(company_path)
        
        logger.info(f"✅ Cleared ChromaDB for company {company_id}: {total_items} items")
        
        return {
            "success": True,
            "message": f"Cleared ChromaDB for company {company_id}",
            "items_cleared": total_items,
            "company_id": company_id
        }
        
    except Exception as e:
        logger.error(f"Error clearing company ChromaDB: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"Error clearing company ChromaDB: {str(e)}",
            "error": str(e)
        }


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Clear specific company
        company_id = sys.argv[1]
        result = clear_specific_company(company_id)
        print(f"\n{result['message']}")
        if not result['success']:
            sys.exit(1)
    else:
        # Clear all ChromaDB
        print("⚠️  WARNING: This will delete ALL ChromaDB data!")
        print("Press Enter to continue, or Ctrl+C to cancel...")
        try:
            input()
        except KeyboardInterrupt:
            print("\nCancelled.")
            sys.exit(0)
        
        result = clear_chromadb()
        print(f"\n{result['message']}")
        if not result['success']:
            sys.exit(1)


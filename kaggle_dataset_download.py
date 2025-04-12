import os
import kaggle
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def download_career_dataset():
    """
    Download the career recommendation dataset from Kaggle
    """
    try:
        # Create a directory for the dataset if it doesn't exist
        dataset_dir = 'data'
        if not os.path.exists(dataset_dir):
            os.makedirs(dataset_dir)
            logger.info(f"Created directory: {dataset_dir}")
        
        # Download the dataset
        logger.info("Downloading career recommendation dataset from Kaggle...")
        kaggle.api.authenticate()
        kaggle.api.dataset_download_files(
            'breejeshdhar/career-recommendation-dataset',
            path=dataset_dir,
            unzip=True
        )
        logger.info(f"Dataset downloaded successfully to {dataset_dir}")
        
        # List the downloaded files
        files = os.listdir(dataset_dir)
        logger.info(f"Downloaded files: {files}")
        
        return True
    except Exception as e:
        logger.error(f"Error downloading dataset: {e}")
        return False

if __name__ == "__main__":
    download_career_dataset()
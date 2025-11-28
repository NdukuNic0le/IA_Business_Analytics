"""
Master ETL Pipeline Runner
Orchestrates the complete data pipeline from Raw to Processed to Final
You can use this on its own or sequentially use the two pipeline files raw to processed then processed to final
"""
import logging
from datetime import datetime
from transform.raw_to_processed import BronzeToSilver
from transform.processed_to_final import SilverToGold

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'../../logs/etl_master_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)

def run_complete_pipeline():
    """Execute complete ETL pipeline"""
    
    start_time = datetime.now()
    logging.info("="*50)
    logging.info("STARTING KIOTA ETL PIPELINE")
    logging.info("="*50)
    
    try:
        # Bronze to Silver
        logging.info("\n>>> BRONZE TO SILVER TRANSFORMATION")
        bronze_silver = BronzeToSilver()
        quality_metrics = bronze_silver.run_pipeline()
        
        # Silver to Gold
        logging.info("\n>>> SILVER TO GOLD TRANSFORMATION")
        silver_gold = SilverToGold()
        silver_gold.run_pipeline()
        
        # Final summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logging.info("\n" + "="*50)
        logging.info("ETL PIPELINE COMPLETE")
        logging.info(f"Duration: {duration:.2f} seconds")
        logging.info("="*50)
        
        return True
        
    except Exception as e:
        logging.error(f"Pipeline failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = run_complete_pipeline()
    exit(0 if success else 1)
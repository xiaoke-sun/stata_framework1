"""
Command-line interface for the spatial data processing framework.
"""

import argparse
import sys
from pathlib import Path
import logging
from typing import Optional

try:
    from .data_processor import SpatialDataProcessor
except ImportError:
    # For direct execution without package structure
    from data_processor import SpatialDataProcessor


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Process spatial data and select representative points"
    )
    
    parser.add_argument(
        "--city", 
        default="tk",
        help="City code (default: tk)"
    )
    
    parser.add_argument(
        "--year", 
        type=int, 
        default=2025,
        help="Processing year (default: 2025)"
    )
    
    parser.add_argument(
        "--dimension",
        help="Process single dimension (S, X1-X9). If not specified, processes all dimensions"
    )
    
    parser.add_argument(
        "--data-path",
        help="Path to input data file (for single dimension processing)"
    )
    
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Output directory (default: output)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize processor
        processor = SpatialDataProcessor(city=args.city, year=args.year)
        
        # Create output directory
        output_path = Path(args.output_dir)
        output_path.mkdir(exist_ok=True)
        
        if args.dimension:
            # Process single dimension
            logger.info(f"Processing single dimension: {args.dimension}")
            
            if args.dimension not in processor.dimensions:
                logger.error(f"Invalid dimension: {args.dimension}. Must be one of: {processor.dimensions}")
                sys.exit(1)
            
            stats = processor.process_dimension(
                dimension=args.dimension,
                data_path=args.data_path,
                output_dir=args.output_dir
            )
            
            print(f"\nProcessing completed for dimension {args.dimension}:")
            print(f"  Input points: {stats['total_input_points']}")
            print(f"  Selected points: {stats['selected_points']}")
            print(f"  Points per class: {stats['points_per_class']}")
            print(f"  Output files:")
            print(f"    Points: {stats['points_file']}")
            print(f"    Buffers: {stats['buffers_file']}")
            
        else:
            # Process all dimensions
            logger.info("Processing all dimensions")
            
            summary = processor.process_all_dimensions(output_dir=args.output_dir)
            
            print(f"\nProcessing completed for city {args.city}, year {args.year}:")
            print(f"  Dimensions processed: {summary['processed_dimensions']}/{summary['total_dimensions']}")
            print(f"  Success: {'Yes' if summary['processing_successful'] else 'No'}")
            
            if summary['dimension_stats']:
                print(f"\nDimension Summary:")
                for stats in summary['dimension_stats']:
                    print(f"  {stats['dimension']}: {stats['selected_points']} points selected")
            
            print(f"\nDetailed report saved to: output/{args.city}_{args.year}_processing_report.json")
    
    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
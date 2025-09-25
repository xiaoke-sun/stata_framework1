#!/usr/bin/env python3
"""
Example usage of the spatial data processing framework.
"""

import sys
from pathlib import Path
import geopandas as gpd
import matplotlib.pyplot as plt

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from data_processor import SpatialDataProcessor


def demo_single_dimension():
    """Demonstrate processing a single dimension."""
    print("=" * 60)
    print("DEMO: Processing Single Dimension")
    print("=" * 60)
    
    # Initialize processor
    processor = SpatialDataProcessor(city="demo", year=2025)
    
    # Process dimension S
    stats = processor.process_dimension("S", output_dir="demo_output")
    
    print(f"✓ Processed dimension: {stats['dimension']}")
    print(f"✓ Input points: {stats['total_input_points']}")
    print(f"✓ Selected points: {stats['selected_points']}")
    print(f"✓ Points per class: {stats['points_per_class']}")
    print(f"✓ Generated files:")
    print(f"  - Points: {stats['points_file']}")
    print(f"  - Buffers: {stats['buffers_file']}")
    
    return stats


def demo_all_dimensions():
    """Demonstrate processing all dimensions."""
    print("\n" + "=" * 60)
    print("DEMO: Processing All Dimensions")
    print("=" * 60)
    
    # Initialize processor
    processor = SpatialDataProcessor(city="demo", year=2025)
    
    # Process all dimensions
    summary = processor.process_all_dimensions(output_dir="demo_output")
    
    print(f"✓ City: {summary['city']}")
    print(f"✓ Year: {summary['year']}")
    print(f"✓ Dimensions processed: {summary['processed_dimensions']}/{summary['total_dimensions']}")
    print(f"✓ Success: {'Yes' if summary['processing_successful'] else 'No'}")
    
    if summary['dimension_stats']:
        print("\n📊 Summary by dimension:")
        for stats in summary['dimension_stats']:
            print(f"  {stats['dimension']}: {stats['selected_points']} points selected")
    
    return summary


def demo_visualization():
    """Demonstrate visualization of selected points."""
    print("\n" + "=" * 60)
    print("DEMO: Visualization")
    print("=" * 60)
    
    try:
        # Read the generated data
        points_file = "demo_output/demo_2025_S_representative_points.gpkg"
        buffers_file = "demo_output/demo_2025_S_buffers.gpkg"
        
        if Path(points_file).exists() and Path(buffers_file).exists():
            points_gdf = gpd.read_file(points_file)
            buffers_gdf = gpd.read_file(buffers_file)
            
            print(f"✓ Loaded {len(points_gdf)} representative points")
            print(f"✓ Loaded {len(buffers_gdf)} buffer zones")
            
            # Create visualization
            fig, ax = plt.subplots(1, 1, figsize=(12, 8))
            
            # Plot buffers first (as background)
            buffers_gdf.plot(ax=ax, color='lightblue', alpha=0.5, edgecolor='blue', linewidth=0.5)
            
            # Plot points colored by class
            colors = {'class_1': 'red', 'class_2': 'green', 'class_3': 'blue', 
                     'class_4': 'orange', 'class_5': 'purple'}
            
            for class_name, color in colors.items():
                class_points = points_gdf[points_gdf['class'] == class_name]
                if len(class_points) > 0:
                    class_points.plot(ax=ax, color=color, markersize=100, alpha=0.8, 
                                    edgecolor='black', linewidth=1, label=class_name)
            
            # Add point numbers as text
            for idx, row in points_gdf.iterrows():
                ax.annotate(row['No'], (row.geometry.x, row.geometry.y), 
                           fontsize=12, ha='center', va='center', fontweight='bold')
            
            ax.set_title('Representative Points and Buffer Zones\n(Dimension S)', fontsize=14, fontweight='bold')
            ax.legend(title='Classes', loc='upper right')
            ax.grid(True, alpha=0.3)
            
            # Save the plot
            output_file = "demo_output/visualization_demo.png"
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            print(f"✓ Visualization saved to: {output_file}")
            
            return True
        else:
            print("❌ Demo data files not found. Run demo_single_dimension() first.")
            return False
            
    except Exception as e:
        print(f"❌ Visualization failed: {str(e)}")
        return False


def main():
    """Run all demonstrations."""
    print("🚀 Spatial Data Processing Framework - Demo")
    
    # Demo 1: Single dimension processing
    demo_single_dimension()
    
    # Demo 2: All dimensions processing
    demo_all_dimensions()
    
    # Demo 3: Visualization
    demo_visualization()
    
    print("\n" + "=" * 60)
    print("✅ All demonstrations completed!")
    print("=" * 60)
    
    print("\n📁 Generated files in demo_output/:")
    demo_output = Path("demo_output")
    if demo_output.exists():
        for file_path in sorted(demo_output.glob("*")):
            print(f"  - {file_path.name}")
    
    print("\n💡 Usage Tips:")
    print("  - Use the CLI: python main.py --city tk --year 2025")
    print("  - Process single dimension: python main.py --dimension S")
    print("  - Enable verbose output: python main.py --verbose")
    print("  - Custom output directory: python main.py --output-dir results")


if __name__ == "__main__":
    main()
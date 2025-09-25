"""
Tests for the spatial data processor.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import geopandas as gpd
import numpy as np
from shapely.geometry import Point

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data_processor import SpatialDataProcessor


class TestSpatialDataProcessor(unittest.TestCase):
    """Test cases for SpatialDataProcessor."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.processor = SpatialDataProcessor(city="test", year=2024)
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test processor initialization."""
        self.assertEqual(self.processor.city, "test")
        self.assertEqual(self.processor.year, 2024)
        self.assertEqual(len(self.processor.dimensions), 10)  # S + X1-X9
        self.assertEqual(len(self.processor.class_names), 5)  # class_1 to class_5
        self.assertEqual(len(self.processor.number_symbols), 10)  # ①-⑩
    
    def test_create_sample_data(self):
        """Test sample data creation."""
        gdf = self.processor._create_sample_data("S", n_points=50)
        
        self.assertEqual(len(gdf), 50)
        self.assertTrue(all(isinstance(geom, Point) for geom in gdf.geometry))
        self.assertTrue(all(cls in self.processor.class_names for cls in gdf['class']))
        self.assertEqual(gdf.crs, 'EPSG:4326')
        
        # Check that all classes are represented
        unique_classes = set(gdf['class'].unique())
        self.assertTrue(len(unique_classes) >= 3)  # Should have reasonable class diversity
    
    def test_select_representative_points(self):
        """Test representative point selection."""
        # Create test data with known distribution
        gdf = self.processor._create_sample_data("S", n_points=100)
        
        selected = self.processor.select_representative_points(gdf)
        
        # Should select exactly 10 points (or less if not enough data)
        self.assertLessEqual(len(selected), 10)
        self.assertGreater(len(selected), 0)
        
        # Should have 'No' column with special characters
        self.assertTrue('No' in selected.columns)
        self.assertTrue(all(no in self.processor.number_symbols for no in selected['No'] if no))
    
    def test_create_buffers(self):
        """Test buffer creation."""
        # Create test points
        gdf = self.processor._create_sample_data("S", n_points=10)
        
        buffers = self.processor.create_buffers(gdf)
        
        self.assertEqual(len(buffers), len(gdf))
        self.assertTrue('buffer_distance' in buffers.columns)
        self.assertEqual(buffers['buffer_distance'].iloc[0], self.processor.buffer_distance)
        
        # Check that geometries are actually buffers (should be polygons)
        self.assertTrue(all(geom.geom_type == 'Polygon' for geom in buffers.geometry))
    
    def test_spatially_distributed_selection(self):
        """Test spatial distribution of selected points."""
        # Create points in a line to test spatial distribution
        points_data = []
        for i in range(20):
            points_data.append({
                'geometry': Point(100 + i * 0.01, 30),  # Points in a line
                'class': f'class_{(i % 5) + 1}',
                'value': i
            })
        
        gdf = gpd.GeoDataFrame(points_data, crs='EPSG:4326')
        
        # Select 4 points
        selected_records = self.processor._select_spatially_distributed_points(gdf, 4)
        
        self.assertEqual(len(selected_records), 4)
        
        # Check that selected points are reasonably distributed
        selected_gdf = gpd.GeoDataFrame(selected_records, crs='EPSG:4326')
        x_coords = [point.geometry.x for _, point in selected_gdf.iterrows()]
        
        # Points should span the range better than just picking the first 4
        x_range = max(x_coords) - min(x_coords)
        self.assertGreater(x_range, 0.02)  # Should span more than 2 point intervals
    
    def test_numbering_system(self):
        """Test the numbering system."""
        # Create test data
        test_data = []
        for i, class_name in enumerate(self.processor.class_names):
            for j in range(2):  # 2 points per class
                test_data.append({
                    'geometry': Point(100 + i + j * 0.01, 30),
                    'class': class_name,
                    'value': i * 2 + j
                })
        
        gdf = gpd.GeoDataFrame(test_data, crs='EPSG:4326')
        numbered_gdf = self.processor._add_numbering(gdf)
        
        # Should have 10 numbered points
        self.assertEqual(len(numbered_gdf), 10)
        
        # Check numbering
        numbers = numbered_gdf['No'].tolist()
        expected_numbers = self.processor.number_symbols[:10]
        
        # All numbers should be from our symbol set
        self.assertTrue(all(num in expected_numbers for num in numbers if num))
        
        # Should have unique numbers
        non_empty_numbers = [num for num in numbers if num]
        self.assertEqual(len(non_empty_numbers), len(set(non_empty_numbers)))
    
    def test_process_dimension(self):
        """Test processing a single dimension."""
        stats = self.processor.process_dimension("S", output_dir=self.temp_dir)
        
        # Check statistics
        self.assertEqual(stats['dimension'], "S")
        self.assertGreater(stats['total_input_points'], 0)
        self.assertGreater(stats['selected_points'], 0)
        self.assertLessEqual(stats['selected_points'], 10)
        
        # Check output files exist
        self.assertTrue(Path(stats['points_file']).exists())
        self.assertTrue(Path(stats['buffers_file']).exists())
        
        # Check file contents
        points_gdf = gpd.read_file(stats['points_file'])
        buffers_gdf = gpd.read_file(stats['buffers_file'])
        
        self.assertEqual(len(points_gdf), stats['selected_points'])
        self.assertEqual(len(buffers_gdf), stats['selected_points'])
        self.assertTrue('No' in points_gdf.columns)
        self.assertTrue('buffer_distance' in buffers_gdf.columns)


class TestCLIIntegration(unittest.TestCase):
    """Integration tests for CLI functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_cli_imports(self):
        """Test that CLI module can be imported."""
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
            import cli
            self.assertTrue(hasattr(cli, 'main'))
        except ImportError as e:
            self.fail(f"CLI module import failed: {e}")


if __name__ == '__main__':
    unittest.main()
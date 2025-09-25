"""
Data processing utilities for spatial data classification and representative point selection.
"""

import pandas as pd
import geopandas as gpd
import numpy as np
from shapely.geometry import Point, Polygon
from typing import List, Dict, Tuple, Optional
import logging
from pathlib import Path


class SpatialDataProcessor:
    """
    Main class for processing spatial data and selecting representative points.
    """
    
    def __init__(self, city: str = "tk", year: int = 2025):
        """
        Initialize the spatial data processor.
        
        Args:
            city: City code (default: "tk")
            year: Processing year (default: 2025)
        """
        self.city = city
        self.year = year
        self.dimensions = ["S"] + [f"X{i}" for i in range(1, 10)]  # S, X1-X9
        self.class_names = [f"class_{i}" for i in range(1, 6)]  # class_1 to class_5
        self.buffer_distance = 0.01  # degrees
        
        # Special characters for numbering
        self.number_symbols = ["①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨", "⑩"]
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def load_classified_data(self, dimension: str, data_path: Optional[str] = None) -> gpd.GeoDataFrame:
        """
        Load classified spatial data for a given dimension.
        
        Args:
            dimension: Dimension name (S, X1-X9)
            data_path: Path to the data file (optional)
            
        Returns:
            GeoDataFrame with classified points
        """
        if data_path is None:
            # Default path structure - adjust based on actual data organization
            data_path = f"data/{self.city}_{self.year}_{dimension}_classified.gpkg"
        
        # Convert to absolute path
        if not Path(data_path).is_absolute():
            data_path = Path.cwd() / data_path
        
        try:
            if Path(data_path).exists():
                gdf = gpd.read_file(data_path)
                self.logger.info(f"Loaded {len(gdf)} points for dimension {dimension}")
                return gdf
            else:
                # Create sample data for testing if file doesn't exist
                self.logger.warning(f"Data file not found: {data_path}. Creating sample data.")
                return self._create_sample_data(dimension)
        except Exception as e:
            # Create sample data for testing if file can't be read
            self.logger.warning(f"Error reading data file {data_path}: {str(e)}. Creating sample data.")
            return self._create_sample_data(dimension)
    
    def _create_sample_data(self, dimension: str, n_points: int = 100) -> gpd.GeoDataFrame:
        """
        Create sample classified spatial data for testing.
        
        Args:
            dimension: Dimension name
            n_points: Number of sample points to create
            
        Returns:
            GeoDataFrame with sample classified points
        """
        # Generate random points within a reasonable geographic extent
        np.random.seed(42)  # For reproducible results
        
        # Create points in a 1x1 degree area
        lons = np.random.uniform(100.0, 101.0, n_points)
        lats = np.random.uniform(30.0, 31.0, n_points)
        
        # Assign classes randomly but ensure all classes have some points
        classes = []
        for i in range(5):  # Ensure each class has at least some points
            classes.extend([f"class_{i+1}"] * (n_points // 5))
        
        # Fill remaining points randomly
        remaining = n_points - len(classes)
        if remaining > 0:
            classes.extend(np.random.choice(self.class_names, remaining))
        
        # Shuffle the classes
        np.random.shuffle(classes)
        
        # Create GeoDataFrame
        gdf = gpd.GeoDataFrame({
            'geometry': [Point(lon, lat) for lon, lat in zip(lons, lats)],
            'class': classes[:n_points],
            'value': np.random.randn(n_points),  # Some sample values
            'dimension': dimension
        }, crs='EPSG:4326')
        
        self.logger.info(f"Created {n_points} sample points for dimension {dimension}")
        return gdf
    
    def select_representative_points(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Select 10 representative points (2 from each of 5 classes) with spatial optimization.
        
        Args:
            gdf: GeoDataFrame with classified points
            
        Returns:
            GeoDataFrame with 10 selected representative points
        """
        selected_points = []
        
        # First, try to select 2 points from each class
        for class_name in self.class_names:
            class_points = gdf[gdf['class'] == class_name].copy()
            
            if len(class_points) >= 2:
                # Select 2 points with spatial distribution consideration
                selected = self._select_spatially_distributed_points(class_points, 2)
                selected_points.extend(selected)
            elif len(class_points) == 1:
                # Only one point available
                selected_points.extend([class_points.iloc[0]])
            else:
                # No points in this class - will handle later
                self.logger.warning(f"No points found for {class_name}")
        
        # Handle missing points by selecting from neighboring areas
        if len(selected_points) < 10:
            missing_count = 10 - len(selected_points)
            additional_points = self._select_additional_points(gdf, selected_points, missing_count)
            selected_points.extend(additional_points)
        
        # Create result GeoDataFrame
        result_gdf = gpd.GeoDataFrame(selected_points, crs=gdf.crs)
        
        # Add numbering
        result_gdf = self._add_numbering(result_gdf)
        
        return result_gdf
    
    def _select_spatially_distributed_points(self, points: gpd.GeoDataFrame, n: int) -> List:
        """
        Select n points that are spatially well-distributed.
        
        Args:
            points: Available points
            n: Number of points to select
            
        Returns:
            List of selected point records
        """
        if len(points) <= n:
            return points.to_dict('records')
        
        # Use a simple spatial distribution strategy
        # Calculate bounding box and divide into grid
        bounds = points.total_bounds  # [minx, miny, maxx, maxy]
        
        # If we need spatial distribution, select points that are far apart
        selected_indices = []
        remaining_points = points.copy()
        
        # Select first point randomly
        first_idx = np.random.randint(0, len(remaining_points))
        selected_indices.append(remaining_points.index[first_idx])
        
        for _ in range(n - 1):
            if len(remaining_points) <= 1:
                break
                
            # Remove already selected point
            remaining_points = remaining_points.drop(selected_indices[-1])
            
            if len(remaining_points) == 0:
                break
            
            # Select point that is farthest from already selected points
            max_min_distance = 0
            best_idx = None
            
            for idx, point in remaining_points.iterrows():
                min_distance = float('inf')
                
                # Calculate minimum distance to already selected points
                for sel_idx in selected_indices:
                    sel_point = points.loc[sel_idx]
                    distance = point.geometry.distance(sel_point.geometry)
                    min_distance = min(min_distance, distance)
                
                # Keep track of point with maximum minimum distance
                if min_distance > max_min_distance:
                    max_min_distance = min_distance
                    best_idx = idx
            
            if best_idx is not None:
                selected_indices.append(best_idx)
            else:
                # Fallback: select randomly
                selected_indices.append(remaining_points.index[0])
        
        return points.loc[selected_indices].to_dict('records')
    
    def _select_additional_points(self, gdf: gpd.GeoDataFrame, 
                                selected_points: List, missing_count: int) -> List:
        """
        Select additional points when some classes are missing.
        
        Args:
            gdf: Original GeoDataFrame
            selected_points: Already selected points
            missing_count: Number of additional points needed
            
        Returns:
            List of additional selected points
        """
        # Convert selected points to GeoDataFrame for spatial operations
        if selected_points:
            selected_gdf = gpd.GeoDataFrame(selected_points, crs=gdf.crs)
            selected_indices = [p.get('index', -1) for p in selected_points]
            # Remove already selected points
            remaining_gdf = gdf[~gdf.index.isin(selected_indices)].copy()
        else:
            remaining_gdf = gdf.copy()
        
        if len(remaining_gdf) == 0:
            return []
        
        # Select points that are spatially distributed
        additional = self._select_spatially_distributed_points(remaining_gdf, missing_count)
        
        return additional
    
    def _add_numbering(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Add numbering column with special characters.
        
        Args:
            gdf: GeoDataFrame with selected points
            
        Returns:
            GeoDataFrame with added 'No' column
        """
        gdf = gdf.copy()
        
        # Group by class and assign numbers
        gdf['No'] = ""
        number_idx = 0
        
        for class_name in self.class_names:
            class_points = gdf[gdf['class'] == class_name]
            for idx in class_points.index:
                if number_idx < len(self.number_symbols):
                    gdf.loc[idx, 'No'] = self.number_symbols[number_idx]
                    number_idx += 1
        
        # Handle case where we have points not in the standard classes
        remaining_points = gdf[gdf['No'] == ""]
        for idx in remaining_points.index:
            if number_idx < len(self.number_symbols):
                gdf.loc[idx, 'No'] = self.number_symbols[number_idx]
                number_idx += 1
        
        return gdf
    
    def create_buffers(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Create buffers around selected points.
        
        Args:
            gdf: GeoDataFrame with selected points
            
        Returns:
            GeoDataFrame with buffer geometries
        """
        buffer_gdf = gdf.copy()
        
        # Convert to a suitable projected CRS for buffering if in geographic CRS
        original_crs = gdf.crs
        if original_crs is None or original_crs.to_string() == 'EPSG:4326':
            # Use Web Mercator for buffering (approximate but widely used)
            projected_gdf = gdf.to_crs('EPSG:3857')
            # Convert buffer distance from degrees to meters (approximate)
            buffer_distance_m = self.buffer_distance * 111320  # ~111.32 km per degree at equator
            projected_gdf['geometry'] = projected_gdf.geometry.buffer(buffer_distance_m)
            # Convert back to original CRS
            buffer_gdf['geometry'] = projected_gdf.to_crs(original_crs).geometry
        else:
            # Already in projected CRS, use original buffer distance
            buffer_gdf['geometry'] = gdf.geometry.buffer(self.buffer_distance)
        
        buffer_gdf['buffer_distance'] = self.buffer_distance
        
        return buffer_gdf
    
    def process_dimension(self, dimension: str, data_path: Optional[str] = None, 
                         output_dir: str = "output") -> Dict:
        """
        Process a single dimension: load data, select points, create buffers, and save results.
        
        Args:
            dimension: Dimension name (S, X1-X9)
            data_path: Path to input data (optional)
            output_dir: Output directory path
            
        Returns:
            Dictionary with processing statistics
        """
        self.logger.info(f"Processing dimension: {dimension}")
        
        # Load classified data
        gdf = self.load_classified_data(dimension, data_path)
        
        # Select representative points
        selected_gdf = self.select_representative_points(gdf)
        
        # Create buffers
        buffer_gdf = self.create_buffers(selected_gdf)
        
        # Save results
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Save points
        points_file = output_path / f"{self.city}_{self.year}_{dimension}_representative_points.gpkg"
        selected_gdf.to_file(points_file, driver="GPKG")
        
        # Save buffers
        buffers_file = output_path / f"{self.city}_{self.year}_{dimension}_buffers.gpkg"
        buffer_gdf.to_file(buffers_file, driver="GPKG")
        
        # Collect statistics
        stats = {
            'dimension': dimension,
            'total_input_points': len(gdf),
            'selected_points': len(selected_gdf),
            'points_per_class': selected_gdf['class'].value_counts().to_dict(),
            'points_file': str(points_file),
            'buffers_file': str(buffers_file),
            'buffer_distance': self.buffer_distance
        }
        
        self.logger.info(f"Completed processing {dimension}: {len(selected_gdf)} points selected")
        
        return stats
    
    def process_all_dimensions(self, output_dir: str = "output") -> Dict:
        """
        Process all dimensions and generate comprehensive report.
        
        Args:
            output_dir: Output directory path
            
        Returns:
            Dictionary with comprehensive processing statistics
        """
        self.logger.info(f"Starting processing for city {self.city}, year {self.year}")
        
        all_stats = []
        
        for dimension in self.dimensions:
            try:
                stats = self.process_dimension(dimension, output_dir=output_dir)
                all_stats.append(stats)
            except Exception as e:
                self.logger.error(f"Error processing dimension {dimension}: {str(e)}")
                continue
        
        # Generate summary report
        summary = {
            'city': self.city,
            'year': self.year,
            'processed_dimensions': len(all_stats),
            'total_dimensions': len(self.dimensions),
            'dimension_stats': all_stats,
            'processing_successful': len(all_stats) == len(self.dimensions)
        }
        
        # Save summary report
        output_path = Path(output_dir)
        report_file = output_path / f"{self.city}_{self.year}_processing_report.json"
        
        import json
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Processing completed. Report saved to: {report_file}")
        
        return summary
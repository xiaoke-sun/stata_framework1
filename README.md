# Stata Framework for Spatial Data Processing

A Python framework for processing spatial data and selecting representative points from classified datasets.

## Features

- **Representative Point Selection**: Select 10 representative points (2 from each of 5 classes) with spatial distribution optimization
- **Buffer Generation**: Create 0.01-degree buffers around selected points
- **Multi-dimensional Processing**: Process multiple dimensions (S, X1-X9) simultaneously
- **Smart Class Handling**: Automatically handle missing classes by selecting from neighboring points
- **Special Numbering System**: Use special characters (①②③④⑤⑥⑦⑧⑨⑩) for point numbering
- **GPKG Output**: Generate GeoPackage files for points and buffers
- **Processing Reports**: Generate detailed statistics and processing reports

## Installation

1. Clone the repository:
```bash
git clone https://github.com/xiaoke-sun/stata_framework1.git
cd stata_framework1
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install the package:
```bash
pip install -e .
```

## Usage

### Command Line Interface

Process all dimensions for city "tk" in year 2025:
```bash
python main.py --city tk --year 2025
```

Process a single dimension:
```bash
python main.py --dimension S --city tk --year 2025
```

With custom data path:
```bash
python main.py --dimension X1 --data-path data/custom_data.gpkg --output-dir results
```

Enable verbose logging:
```bash
python main.py --verbose
```

### Python API

```python
from src.data_processor import SpatialDataProcessor

# Initialize processor
processor = SpatialDataProcessor(city="tk", year=2025)

# Process all dimensions
summary = processor.process_all_dimensions(output_dir="output")

# Process single dimension
stats = processor.process_dimension("S", output_dir="output")
```

## Data Format

The framework expects classified spatial data with the following structure:
- **Geometry**: Point geometries in any CRS (will be processed in EPSG:4326)
- **Class column**: Classification results (class_1, class_2, class_3, class_4, class_5)
- **Additional attributes**: Any additional columns will be preserved

## Output Files

For each dimension, the framework generates:
- `{city}_{year}_{dimension}_representative_points.gpkg`: Selected representative points
- `{city}_{year}_{dimension}_buffers.gpkg`: Buffer zones around selected points
- `{city}_{year}_processing_report.json`: Comprehensive processing statistics

## Selection Algorithm

1. **Primary Selection**: Select 2 points from each of the 5 classes
2. **Spatial Distribution**: Use distance-based optimization to ensure points are well-distributed
3. **Missing Class Handling**: If a class has no points, select additional points from other classes
4. **Numbering**: Assign special character numbers (①-⑩) based on class order

## Requirements

- Python 3.8+
- GeoPandas 0.14.0+
- Pandas 2.0.0+
- NumPy 1.24.0+
- Shapely 2.0.0+
- Scikit-learn 1.3.0+
- And other dependencies listed in requirements.txt
#!/usr/bin/env python3
"""
Utilities for processing basement pipe survey data
"""

import yaml
import json
from pathlib import Path
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from datetime import datetime

class BasementSurveyProcessor:
    def __init__(self, yaml_file: str):
        self.yaml_file = Path(yaml_file)
        self.data = self.load_survey_data()
    
    def load_survey_data(self) -> Dict:
        """Load survey data from YAML file"""
        with open(self.yaml_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def calculate_total_lengths(self) -> Dict[str, float]:
        """Calculate total pipe lengths by diameter"""
        lengths = {'DN110': 0, 'DN75': 0, 'DN50': 0}
        
        # DN110 segments
        for segment in self.data['basement_survey']['layers']['DN110_main_distribution']['segments']:
            lengths['DN110'] += segment['length']
        
        # DN75 segments  
        for segment in self.data['basement_survey']['layers']['DN75_stair_distribution']['segments']:
            lengths['DN75'] += segment['length']
            
        # DN50 segments
        for column in self.data['basement_survey']['layers']['DN50_vertical_columns']['columns']:
            for segment in column['segments']:
                lengths['DN50'] += segment['length']
                
        return lengths
    
    def estimate_materials(self) -> Dict[str, Dict]:
        """Estimate required materials based on lengths"""
        lengths = self.calculate_total_lengths()
        
        # Material costs per meter (RON) - rough estimates
        costs_per_meter = {
            'DN110': 45,  # PPR PN20
            'DN75': 35,   # PPR PN20  
            'DN50': 25    # PPR PN20
        }
        
        # Add 15% waste factor
        waste_factor = 1.15
        
        materials = {}
        total_cost = 0
        
        for diameter, length in lengths.items():
            adjusted_length = length * waste_factor
            cost = adjusted_length * costs_per_meter[diameter]
            total_cost += cost
            
            materials[diameter] = {
                'length_needed': round(adjusted_length, 1),
                'cost_per_meter': costs_per_meter[diameter],
                'total_cost': round(cost, 2)
            }
        
        # Add fittings (approximately 30% of pipe cost)
        fittings_cost = total_cost * 0.3
        
        materials['fittings'] = {
            'estimated_cost': round(fittings_cost, 2),
            'description': 'Coturi, teuri, reducții, racorduri'
        }
        
        materials['total_estimated_cost'] = round(total_cost + fittings_cost, 2)
        
        return materials
    
    def generate_2d_plot(self, output_file: str = 'basement_plan.png'):
        """Generate 2D visualization of the pipe layout"""
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))
        
        # Set up the plot
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)
        ax.set_xlabel('X (metri)')
        ax.set_ylabel('Y (metri)')
        ax.set_title('Plan Subsol - Rețea Apă Rece')
        
        # Color mapping
        colors = {
            'DN110': '#FF0000',  # Red
            'DN75': '#0000FF',   # Blue  
            'DN50': '#00FF00'    # Green
        }
        
        # Draw DN110 segments
        dn110_data = self.data['basement_survey']['layers']['DN110_main_distribution']
        for segment in dn110_data['segments']:
            start = segment['start_point'][:2]  # x, y only
            end = segment['end_point'][:2]
            ax.plot([start[0], end[0]], [start[1], end[1]], 
                   color=colors['DN110'], linewidth=4, label='DN110' if segment == dn110_data['segments'][0] else "")
        
        # Draw DN75 segments
        dn75_data = self.data['basement_survey']['layers']['DN75_stair_distribution']
        for segment in dn75_data['segments']:
            start = segment['start_point'][:2]
            end = segment['end_point'][:2]
            ax.plot([start[0], end[0]], [start[1], end[1]], 
                   color=colors['DN75'], linewidth=3, label='DN75' if segment == dn75_data['segments'][0] else "")
        
        # Draw DN50 segments
        dn50_data = self.data['basement_survey']['layers']['DN50_vertical_columns']
        for i, column in enumerate(dn50_data['columns']):
            for segment in column['segments']:
                start = segment['start_point'][:2]
                end = segment['end_point'][:2]
                ax.plot([start[0], end[0]], [start[1], end[1]], 
                       color=colors['DN50'], linewidth=2, 
                       label='DN50' if i == 0 and segment == column['segments'][0] else "")
        
        # Add connection points
        layers = self.data['basement_survey']['layers']
        
        # DN110 connection points
        for point in layers['DN110_main_distribution']['connection_points']:
            coords = point['coordinates'][:2]
            ax.plot(coords[0], coords[1], 'ro', markersize=8)
            ax.annotate(point['id'], (coords[0], coords[1]), xytext=(5, 5), 
                       textcoords='offset points', fontsize=8)
        
        # DN75 connection points
        for point in layers['DN75_stair_distribution']['connection_points']:
            coords = point['coordinates'][:2]
            ax.plot(coords[0], coords[1], 'bs', markersize=6)
            ax.annotate(point['id'], (coords[0], coords[1]), xytext=(5, 5), 
                       textcoords='offset points', fontsize=8)
        
        ax.legend()
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.show()
        
        return output_file
    
    def generate_cost_report(self) -> str:
        """Generate detailed cost analysis report"""
        materials = self.estimate_materials()
        lengths = self.calculate_total_lengths()
        
        report = f"""
RAPORT ESTIMARE COSTURI - SCHIMBARE COLOANĂ APĂ RECE
===============================================

Data: {datetime.now().strftime('%d.%m.%Y %H:%M')}
Proiect: {self.data['basement_survey']['metadata']['project_name']}

LUNGIMI MĂSURATE:
-----------------
DN110 (comună cu alte scări): {lengths['DN110']:.1f} m
DN75 (comună pe scară): {lengths['DN75']:.1f} m  
DN50 (coloane verticale): {lengths['DN50']:.1f} m

MATERIALE NECESARE (cu 15% rezervă):
----------------------------------
"""
        
        for diameter, details in materials.items():
            if diameter != 'total_estimated_cost' and diameter != 'fittings':
                report += f"{diameter}: {details['length_needed']} m × {details['cost_per_meter']} RON/m = {details['total_cost']} RON\n"
        
        report += f"""
Fitinguri și accesorii: {materials['fittings']['estimated_cost']} RON
{materials['fittings']['description']}

TOTAL ESTIMAT MATERIALE: {materials['total_estimated_cost']} RON

COSTURI SUPLIMENTARE ESTIMATE:
-----------------------------
Manoperă instalator: ~{materials['total_estimated_cost'] * 1.2:.0f} RON
Manoperă zidărie/finisaje: ~{materials['total_estimated_cost'] * 0.3:.0f} RON
Autorizații și avize: ~500 RON
Diverse (transport, imprevizite): ~{materials['total_estimated_cost'] * 0.1:.0f} RON

TOTAL ESTIMAT PROIECT: ~{materials['total_estimated_cost'] * 2.1 + 500:.0f} RON

NOTĂ: Aceste sunt estimări preliminare. Pentru costuri exacte
consultați oferte de la instalatori autorizați.
"""
        
        return report
    
    def export_for_cad(self, output_file: str = 'basement_cad_data.json'):
        """Export data in format suitable for CAD import"""
        cad_data = {
            'layers': [],
            'entities': []
        }
        
        # Define layers
        for layer_name, layer_data in self.data['basement_survey']['layers'].items():
            cad_data['layers'].append({
                'name': layer_data['name'],
                'color': layer_data['color'],
                'lineweight': {'DN110': 0.7, 'DN75': 0.5, 'DN50': 0.3}.get(layer_name.split('_')[0], 0.3)
            })
        
        # Extract entities (lines, points)
        entity_id = 1
        
        for layer_name, layer_data in self.data['basement_survey']['layers'].items():
            layer_short = layer_name.split('_')[0]
            
            if 'segments' in layer_data:
                # Line segments
                for segment in layer_data['segments']:
                    cad_data['entities'].append({
                        'id': entity_id,
                        'type': 'LINE',
                        'layer': layer_data['name'],
                        'start': segment['start_point'],
                        'end': segment['end_point'],
                        'properties': {
                            'diameter': segment['diameter'],
                            'length': segment['length'],
                            'notes': segment.get('notes', '')
                        }
                    })
                    entity_id += 1
            
            if 'columns' in layer_data:
                # Vertical columns
                for column in layer_data['columns']:
                    for segment in column['segments']:
                        cad_data['entities'].append({
                            'id': entity_id,
                            'type': 'LINE',
                            'layer': layer_data['name'],
                            'start': segment['start_point'],
                            'end': segment['end_point'],
                            'properties': {
                                'diameter': 50,
                                'length': segment['length'],
                                'column_id': column['id'],
                                'serves': column['serves_apartments']
                            }
                        })
                        entity_id += 1
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(cad_data, f, indent=2, ensure_ascii=False)
        
        return output_file

# Example usage
if __name__ == "__main__":
    processor = BasementSurveyProcessor('basement_survey.yaml')
    
    # Generate cost report
    cost_report = processor.generate_cost_report()
    print(cost_report)
    
    # Generate 2D plot
    plot_file = processor.generate_2d_plot()
    print(f"Plan generat: {plot_file}")
    
    # Export for CAD
    cad_file = processor.export_for_cad()
    print(f"Date CAD exportate: {cad_file}")
    
    # Calculate materials
    materials = processor.estimate_materials()
    print(f"\nMateriale necesare: {materials}")
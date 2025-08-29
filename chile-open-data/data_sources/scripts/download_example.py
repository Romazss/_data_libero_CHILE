#!/usr/bin/env python3
"""
Script de descarga de ejemplo - Fase 1
Biblioteca de Datos Abiertos de Chile

Este script demuestra cómo descargar datasets usando la configuración
definida en sources.yaml.
"""

import yaml
import requests
import os
from pathlib import Path
from typing import Dict, List
import argparse
import sys

def load_sources(sources_path: Path) -> List[Dict]:
    """Carga la configuración de fuentes desde sources.yaml"""
    if not sources_path.exists():
        raise FileNotFoundError(f"No se encontró {sources_path}")
    
    with open(sources_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    # Soporta tanto 'datasets' como 'sources'
    datasets = data.get('datasets', data.get('sources', []))
    if not datasets:
        raise ValueError("No se encontraron datasets en la configuración")
    
    return datasets

def check_dataset_availability(dataset: Dict) -> Dict:
    """Verifica si un dataset está disponible"""
    url = dataset['url']
    method = dataset.get('method', 'HEAD').upper()
    timeout = dataset.get('timeout', 10)
    
    try:
        if method == 'HEAD':
            response = requests.head(url, timeout=timeout, allow_redirects=True)
        else:
            response = requests.get(url, timeout=timeout, stream=True)
        
        return {
            'id': dataset['id'],
            'name': dataset['name'],
            'url': url,
            'status': 'available' if response.status_code < 400 else 'unavailable',
            'status_code': response.status_code,
            'category': dataset['category']
        }
    except requests.RequestException as e:
        return {
            'id': dataset['id'],
            'name': dataset['name'],
            'url': url,
            'status': 'error',
            'error': str(e),
            'category': dataset['category']
        }

def download_dataset(dataset: Dict, output_dir: Path, dry_run: bool = False) -> bool:
    """
    Descarga un dataset (simulado en esta versión de ejemplo)
    En una implementación completa, aquí se haría la descarga real
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if dry_run:
        print(f"[DRY-RUN] Descargaría: {dataset['name']} -> {output_dir}")
        return True
    
    # En una implementación real, aquí iría la lógica de descarga específica
    # por tipo de dataset (CSV, API, scraping, etc.)
    print(f"⚠️  Descarga simulada: {dataset['name']}")
    print(f"   URL: {dataset['url']}")
    print(f"   Categoría: {dataset['category']}")
    
    # Crear un archivo de ejemplo
    example_file = output_dir / f"{dataset['id']}_metadata.txt"
    with open(example_file, 'w', encoding='utf-8') as f:
        f.write(f"Dataset: {dataset['name']}\n")
        f.write(f"URL: {dataset['url']}\n")
        f.write(f"Categoría: {dataset['category']}\n")
        f.write(f"Descripción: {dataset.get('description', 'Sin descripción')}\n")
    
    print(f"   Metadata guardada en: {example_file}")
    return True

def main():
    parser = argparse.ArgumentParser(description='Descarga datasets de Chile')
    parser.add_argument('--sources', '-s', 
                       default='data_sources/config/sources.yaml',
                       help='Ruta al archivo sources.yaml')
    parser.add_argument('--output', '-o',
                       default='downloads',
                       help='Directorio de salida')
    parser.add_argument('--dataset', '-d',
                       help='ID específico de dataset a descargar')
    parser.add_argument('--check-only', '-c',
                       action='store_true',
                       help='Solo verificar disponibilidad, no descargar')
    parser.add_argument('--dry-run',
                       action='store_true',
                       help='Simular descarga sin ejecutar')
    parser.add_argument('--category',
                       help='Filtrar por categoría específica')
    
    args = parser.parse_args()
    
    # Configurar rutas
    sources_path = Path(args.sources)
    output_dir = Path(args.output)
    
    try:
        # Cargar configuración
        datasets = load_sources(sources_path)
        print(f"📂 Cargados {len(datasets)} datasets desde {sources_path}")
        
        # Filtrar por dataset específico
        if args.dataset:
            datasets = [ds for ds in datasets if ds['id'] == args.dataset]
            if not datasets:
                print(f"❌ Dataset '{args.dataset}' no encontrado")
                sys.exit(1)
        
        # Filtrar por categoría
        if args.category:
            datasets = [ds for ds in datasets if ds['category'] == args.category]
            if not datasets:
                print(f"❌ No se encontraron datasets en la categoría '{args.category}'")
                sys.exit(1)
        
        # Verificar disponibilidad
        print("\n🔍 Verificando disponibilidad de datasets...")
        results = []
        for dataset in datasets:
            result = check_dataset_availability(dataset)
            results.append(result)
            
            status_emoji = "✅" if result['status'] == 'available' else "❌"
            print(f"{status_emoji} {result['name']} ({result['category']}) - {result['status']}")
        
        if args.check_only:
            print(f"\n📊 Resumen: {len([r for r in results if r['status'] == 'available'])} disponibles de {len(results)}")
            return
        
        # Descargar datasets disponibles
        available_datasets = [ds for ds, result in zip(datasets, results) 
                            if result['status'] == 'available']
        
        if not available_datasets:
            print("\n❌ No hay datasets disponibles para descargar")
            return
        
        print(f"\n⬇️  Descargando {len(available_datasets)} datasets...")
        success_count = 0
        
        for dataset in available_datasets:
            dataset_dir = output_dir / dataset['category'] / dataset['id']
            if download_dataset(dataset, dataset_dir, args.dry_run):
                success_count += 1
        
        print(f"\n✅ Proceso completado: {success_count}/{len(available_datasets)} datasets procesados")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

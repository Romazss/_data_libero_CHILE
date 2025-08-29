#!/usr/bin/env python3
"""
Generador de reportes de estado - Biblioteca de Datos Abiertos de Chile
Crea reportes periódicos sobre la disponibilidad y estado de los datasets
"""

import json
import yaml
from datetime import datetime, timezone
from pathlib import Path
import argparse
import sys
import subprocess
import os

def load_sources(sources_path: Path) -> list:
    """Carga la configuración de fuentes"""
    with open(sources_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return data.get('datasets', data.get('sources', []))

def get_git_info():
    """Obtiene información del repositorio Git"""
    try:
        commit = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode().strip()
        branch = subprocess.check_output(['git', 'branch', '--show-current']).decode().strip()
        return {"commit": commit, "branch": branch}
    except:
        return {"commit": "unknown", "branch": "unknown"}

def generate_status_report(sources_path: Path, output_format: str = "markdown"):
    """Genera un reporte de estado completo"""
    
    # Ejecutar verificación de datasets
    script_path = sources_path.parent / "scripts" / "download_example.py"
    result = subprocess.run([
        sys.executable, str(script_path), "--check-only"
    ], capture_output=True, text=True, cwd=sources_path.parent.parent)
    
    # Cargar configuración
    datasets = load_sources(sources_path)
    
    # Información del sistema
    git_info = get_git_info()
    timestamp = datetime.now(timezone.utc)
    
    if output_format == "json":
        return generate_json_report(datasets, result, git_info, timestamp)
    else:
        return generate_markdown_report(datasets, result, git_info, timestamp)

def generate_markdown_report(datasets, result, git_info, timestamp):
    """Genera reporte en formato Markdown"""
    
    # Parsear resultado del script
    output_lines = result.stdout.split('\n')
    summary_line = [line for line in output_lines if "disponibles de" in line]
    available_count = len([line for line in output_lines if "✅" in line])
    total_count = len(datasets)
    
    report = f"""# 📊 Reporte de Estado - Biblioteca de Datos Abiertos de Chile

**Generado:** {timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}  
**Commit:** `{git_info['commit']}`  
**Branch:** `{git_info['branch']}`  

## 📈 Resumen Ejecutivo

- **Total de datasets:** {total_count}
- **Disponibles:** {available_count} ({available_count/total_count*100:.1f}%)
- **No disponibles:** {total_count - available_count} ({(total_count-available_count)/total_count*100:.1f}%)

## 📋 Estado Detallado

| Dataset | Categoría | Estado | Fuente |
|---------|-----------|--------|--------|
"""
    
    # Agregar cada dataset
    for dataset in datasets:
        name = dataset['name']
        category = dataset['category']
        url = dataset['url']
        
        # Determinar estado basado en el output
        status = "❌ No disponible"
        for line in output_lines:
            if name in line and "✅" in line:
                status = "✅ Disponible"
                break
        
        report += f"| {name} | {category} | {status} | [Link]({url}) |\n"
    
    # Agregar categorías
    categories = {}
    for dataset in datasets:
        cat = dataset['category']
        categories[cat] = categories.get(cat, 0) + 1
    
    report += f"\n## 🏷️ Por Categoría\n\n"
    for category, count in sorted(categories.items()):
        report += f"- **{category.title()}:** {count} dataset(s)\n"
    
    # Output del script
    report += f"\n## 🔍 Log de Verificación\n\n```\n{result.stdout}\n```\n"
    
    if result.stderr:
        report += f"\n## ⚠️ Errores\n\n```\n{result.stderr}\n```\n"
    
    report += f"\n---\n*Reporte generado automáticamente por `generate_report.py`*\n"
    
    return report

def generate_json_report(datasets, result, git_info, timestamp):
    """Genera reporte en formato JSON"""
    
    # Parsear resultado del script
    output_lines = result.stdout.split('\n')
    available_count = len([line for line in output_lines if "✅" in line])
    total_count = len(datasets)
    
    dataset_status = []
    for dataset in datasets:
        name = dataset['name']
        status = "down"
        for line in output_lines:
            if name in line and "✅" in line:
                status = "up"
                break
        
        dataset_status.append({
            "id": dataset['id'],
            "name": name,
            "category": dataset['category'],
            "url": dataset['url'],
            "status": status
        })
    
    report = {
        "generated_at": timestamp.isoformat(),
        "git_info": git_info,
        "summary": {
            "total_datasets": total_count,
            "available_count": available_count,
            "unavailable_count": total_count - available_count,
            "availability_percentage": round(available_count/total_count*100, 1)
        },
        "datasets": dataset_status,
        "raw_output": result.stdout,
        "errors": result.stderr if result.stderr else None
    }
    
    return json.dumps(report, indent=2, ensure_ascii=False)

def main():
    parser = argparse.ArgumentParser(description='Generar reporte de estado de datasets')
    parser.add_argument('--sources', '-s',
                       default='data_sources/config/sources.yaml',
                       help='Ruta al archivo sources.yaml')
    parser.add_argument('--output', '-o',
                       help='Archivo de salida (default: stdout)')
    parser.add_argument('--format', '-f',
                       choices=['markdown', 'json'],
                       default='markdown',
                       help='Formato de salida')
    
    args = parser.parse_args()
    
    sources_path = Path(args.sources)
    if not sources_path.exists():
        print(f"❌ Error: No se encontró {sources_path}", file=sys.stderr)
        sys.exit(1)
    
    try:
        report = generate_status_report(sources_path, args.format)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"✅ Reporte generado: {args.output}")
        else:
            print(report)
            
    except Exception as e:
        print(f"❌ Error generando reporte: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Script para generar JSONs de módulos desde 3 archivos CSV
=========================================================

Lee:
  - ex(modulo).csv
  - ex(lecciones).csv
  - ex(ejercicios).csv

Genera:
  - module_01.json
  - module_02.json
  - ...

Uso:
  python generate_modules_from_csv.py
"""

import csv
import json
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict


def parse_array(value: str) -> List[str]:
    """Convierte string separado por ; en array"""
    if not value or value.strip() == "":
        return []
    return [item.strip() for item in value.split(";") if item.strip()]


def parse_dict(value: str) -> Dict[str, str]:
    """Convierte string con pares clave:valor separados por ; en dict"""
    if not value or value.strip() == "":
        return {}
    
    result = {}
    pairs = value.split(";")
    for pair in pairs:
        if ":" in pair:
            key, val = pair.split(":", 1)
            result[key.strip()] = val.strip()
    return result


def parse_test_cases(value: str) -> List[Dict[str, str]]:
    """Convierte string con pares input>output separados por ; en array de test cases"""
    if not value or value.strip() == "":
        return []
    
    result = []
    cases = value.split(";")
    for case in cases:
        if ">" in case:
            inp, out = case.split(">", 1)
            result.append({
                "input": inp.strip(),
                "expected_output": out.strip()
            })
    return result


def parse_boolean(value: str) -> bool:
    """Convierte string a boolean"""
    if isinstance(value, bool):
        return value
    return str(value).lower() in ["true", "1", "yes", "si", "sí"]


def create_exercise(row: Dict[str, str]) -> Dict[str, Any]:
    """Crea un ejercicio desde una fila del CSV"""
    exercise_type = row["ejercicio_type"].strip()
    
    # Campos comunes a todos
    exercise = {
        "type": exercise_type,
        "title": row["ejercicio_title"].strip(),
        "points": int(row["ejercicio_points"])
    }
    
    # Campos específicos por tipo
    if exercise_type == "question":
        exercise["description"] = row["ejercicio_description"].strip()
        exercise["options"] = parse_array(row["ejercicio_options"])
        exercise["correct_answer"] = row["ejercicio_correct_answer"].strip()
    
    elif exercise_type == "complete":
        exercise["text"] = row["ejercicio_text"].strip()
        exercise["options"] = parse_array(row["ejercicio_options"])
        exercise["correct_answer"] = row["ejercicio_correct_answer"].strip()
    
    elif exercise_type == "make_code":
        exercise["description"] = row["ejercicio_description"].strip()
        exercise["code"] = row["ejercicio_code"].strip()
        exercise["solution"] = row["ejercicio_solution"].strip()
        exercise["test_cases"] = parse_test_cases(row["ejercicio_test_cases"])
    
    elif exercise_type == "study":
        exercise["flashcards"] = parse_dict(row["ejercicio_flashcards"])
    
    elif exercise_type == "unit_concepts":
        exercise["concepts"] = parse_dict(row["ejercicio_concepts"])
    
    return exercise


def read_csv_utf8(filepath: str) -> List[Dict[str, str]]:
    """Lee CSV con encoding UTF-8 y delimitador punto y coma"""
    with open(filepath, 'r', encoding='utf-8-sig') as f:  # utf-8-sig elimina BOM
        reader = csv.DictReader(f, delimiter=';')  # Excel usa ; como separador
        return list(reader)


def generate_modules(modulos_csv: str, lecciones_csv: str, ejercicios_csv: str, output_dir: str):
    """Genera JSONs de módulos desde los 3 CSV"""
    
    print("📖 Leyendo archivos CSV...")
    modulos_data = read_csv_utf8(modulos_csv)
    lecciones_data = read_csv_utf8(lecciones_csv)
    ejercicios_data = read_csv_utf8(ejercicios_csv)
    
    print(f"   - {len(modulos_data)} módulos")
    print(f"   - {len(lecciones_data)} lecciones")
    print(f"   - {len(ejercicios_data)} ejercicios")
    
    # Mostrar encabezados para debug
    if modulos_data:
        print(f"\n🔍 Encabezados en modulos: {list(modulos_data[0].keys())}")
    if lecciones_data:
        print(f"🔍 Encabezados en lecciones: {list(lecciones_data[0].keys())}")
    if ejercicios_data:
        print(f"🔍 Encabezados en ejercicios: {list(ejercicios_data[0].keys())}")
    print()
    
    # Agrupar ejercicios por (modulo_order, leccion_order)
    ejercicios_por_leccion = defaultdict(list)
    for row in ejercicios_data:
        # Saltar filas vacías o incompletas
        if not row.get("modulo_order") or not row.get("leccion_order") or not row.get("ejercicio_order"):
            continue
        
        try:
            key = (int(row["modulo_order"]), int(row["leccion_order"]))
            ejercicio = create_exercise(row)
            ejercicios_por_leccion[key].append((int(row["ejercicio_order"]), ejercicio))
        except (ValueError, KeyError) as e:
            print(f"⚠️  Saltando fila incompleta en ejercicios: {e}")
            continue
    
    # Ordenar ejercicios por su order
    for key in ejercicios_por_leccion:
        ejercicios_por_leccion[key].sort(key=lambda x: x[0])
    
    # Agrupar lecciones por modulo_order
    lecciones_por_modulo = defaultdict(list)
    for row in lecciones_data:
        # Saltar filas vacías o incompletas
        if not row.get("modulo_order") or not row.get("leccion_order"):
            continue
        
        try:
            modulo_order = int(row["modulo_order"])
            leccion_order = int(row["leccion_order"])
        except ValueError:
            continue
        
        # Obtener ejercicios de esta lección
        ejercicios = [ej[1] for ej in ejercicios_por_leccion.get((modulo_order, leccion_order), [])]
        
        leccion = {
            "title": row["leccion_title"].strip(),
            "description": row["leccion_description"].strip(),
            "order": leccion_order,
            "xp_reward": int(row["leccion_xp_reward"]),
            "is_private": parse_boolean(row["leccion_private"]),
            "exercises": ejercicios
        }
        
        lecciones_por_modulo[modulo_order].append((leccion_order, leccion))
    
    # Ordenar lecciones por su order
    for modulo_order in lecciones_por_modulo:
        lecciones_por_modulo[modulo_order].sort(key=lambda x: x[0])
    
    # Crear directorio de salida
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"\n📁 Generando JSONs en: {output_dir}\n")
    
    # Generar JSONs de módulos
    for row in modulos_data:
        modulo_order = int(row["modulo_order"])
        
        # Obtener lecciones de este módulo
        lecciones = [lec[1] for lec in lecciones_por_modulo.get(modulo_order, [])]
        
        module = {
            "title": row["modulo_title"].strip(),
            "description": row["modulo_description"].strip(),
            "order": modulo_order,
            "estimate_time": int(row["modulo_estimate_time"]),
            "lessons": lecciones
        }
        
        # Generar archivo JSON
        filename = f"module_{modulo_order:02d}.json"
        filepath = output_path / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(module, f, indent=2, ensure_ascii=False)
        
        num_lecciones = len(lecciones)
        num_ejercicios = sum(len(lec["exercises"]) for lec in lecciones)
        print(f"✓ {filename} - {num_lecciones} lecciones, {num_ejercicios} ejercicios")
    
    print(f"\n✅ {len(modulos_data)} módulos generados exitosamente")
    print(f"\n📋 Siguiente paso:")
    print(f"   1. Revisa los JSONs en {output_dir}/")
    print(f"   2. Abre ThunderClient")
    print(f"   3. POST http://localhost:8000/modules/")
    print(f"   4. Auth: Bearer [token_de_profesor]")
    print(f"   5. Body: Copia y pega cada JSON")


if __name__ == "__main__":
    # Archivos de entrada (en carpeta de Descargas del usuario)
    home = str(Path.home())
    MODULOS_CSV = f"{home}/Descargas/ex(modulo).csv"
    LECCIONES_CSV = f"{home}/Descargas/ex(lecciones).csv"
    EJERCICIOS_CSV = f"{home}/Descargas/ex(ejercicios).csv"
    
    # Directorio de salida
    OUTPUT_DIR = "modules_output"
    
    try:
        generate_modules(MODULOS_CSV, LECCIONES_CSV, EJERCICIOS_CSV, OUTPUT_DIR)
    except FileNotFoundError as e:
        print(f"❌ Error: No se encontró el archivo {e.filename}")
        print(f"\nAsegúrate de que los 3 CSV estén en: {home}/Descargas/")
        print(f"   - ex(modulo).csv")
        print(f"   - ex(lecciones).csv")
        print(f"   - ex(ejercicios).csv")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

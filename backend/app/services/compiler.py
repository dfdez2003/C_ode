from typing import Dict, List, Tuple

async def compile_and_run_code(code: str, test_cases: List[Dict[str, str]]) -> Tuple[bool, str]:
    """
    Simula la llamada al servicio externo de compilación.
    En la implementación real, esto sería una petición HTTP/gRPC.
    Retorna (es_correcto, mensaje_de_error_o_salida).
    """
    # Simulamos que el código es correcto si pasa el primer caso de prueba
    if not code:
        return (False, "Code cannot be empty.")
        
    # Lógica de compilación simulada
    if "return 0" in code:
        # Si tiene un return 0 (simula éxito), pasamos la prueba
        return (True, "All test cases passed.")
    else:
        return (False, "Code failed to meet test case requirements.")
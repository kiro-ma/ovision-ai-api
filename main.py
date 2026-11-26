import argparse

from inferences.services.pipeline import (
    AP10K_KEYPOINTS,
    BASE_IMAGE_WIDTH,
    DEFAULT_MODEL_PATH,
    FOCAL_CALIBRATION_CONSTANT,
    SKELETON_GROUPS,
    calcular_distancia,
    calcular_peso_schaeffer_kg,
    deduzir_distancia_camera,
    desenhar_painel_onevision,
    desenhar_painel_ovision,
    estimar_biometria_autonoma,
    executar_inferencia,
    executar_inferencia_imagem,
    extrair_identificador_modelo,
    extrair_valor_gabarito,
    gerar_caminho_saida_incremental,
    resolver_modelo_padrao,
    selecionar_apoio_biomecanico,
)

__all__ = [
    "AP10K_KEYPOINTS",
    "BASE_IMAGE_WIDTH",
    "DEFAULT_MODEL_PATH",
    "FOCAL_CALIBRATION_CONSTANT",
    "SKELETON_GROUPS",
    "calcular_distancia",
    "calcular_peso_schaeffer_kg",
    "deduzir_distancia_camera",
    "desenhar_painel_onevision",
    "desenhar_painel_ovision",
    "estimar_biometria_autonoma",
    "executar_inferencia",
    "executar_inferencia_imagem",
    "extrair_identificador_modelo",
    "extrair_valor_gabarito",
    "gerar_caminho_saida_incremental",
    "resolver_modelo_padrao",
    "selecionar_apoio_biomecanico",
]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Ovision - Estimativa Autônoma de Pose, Biometria e Peso de Caprinos"
    )
    parser.add_argument("--image", type=str, default="inputs/010-dist160-v3.jpg", help="Caminho da imagem do animal")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL_PATH, help="Pesos do modelo treinado")
    parser.add_argument(
        "--dist",
        type=float,
        default=None,
        help="Distância da câmera ao animal em cm (se omitida, deduz do arquivo ou usa 160 cm)",
    )
    parser.add_argument("--conf", type=float, default=0.25, help="Limiar de confiança")
    parser.add_argument(
        "--imgsz",
        type=int,
        default=1280,
        help="Resolução de inferência (padrão: 1280 para preservar precisão nas patas)",
    )
    parser.add_argument(
        "--test-gt",
        type=str,
        default=None,
        help="Caminho opcional do JSON de gabarito apenas para verificação de teste",
    )
    args = parser.parse_args()

    executar_inferencia(args.image, args.model, args.dist, args.conf, args.test_gt, imgsz=args.imgsz)

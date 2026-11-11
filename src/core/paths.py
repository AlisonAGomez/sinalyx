"""
Definicao central de caminhos do projeto Sinalyx.

Manter os caminhos neste arquivo evita repeticao de strings e facilita a
manutencao da estrutura de pastas.
"""

import os
from pathlib import Path

import src.core.config  # Carrega .env antes de definir os caminhos durante a importação.

# Diretório raiz do projeto.
BASE_DIR = Path(__file__).resolve().parents[2]

# Dados operacionais podem ficar fora do diretório da aplicação instalada.
DEFAULT_DATA_DIR = BASE_DIR / "data"
DEFAULT_MODELS_DIR = DEFAULT_DATA_DIR / "models"


def _resolver_raiz_configurada(nome_variavel: str, padrao: Path) -> Path:
    """Resolve a pasta configurada; caminhos relativos partem da raiz do projeto."""
    configurado = os.getenv(nome_variavel, "").strip()
    if not configurado:
        return padrao
    caminho = Path(configurado).expanduser()
    return (caminho if caminho.is_absolute() else BASE_DIR / caminho).resolve()


DATA_DIR = _resolver_raiz_configurada("SINALYX_DATA_DIR", DEFAULT_DATA_DIR)
MODELS_DIR = _resolver_raiz_configurada("SINALYX_MODELS_DIR", DEFAULT_MODELS_DIR)

# Pastas principais de dados e arquivos de apoio.
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

AUTOENCODER_DIR = MODELS_DIR / "autoencoder"

# Arquivos centrais usados pelos fluxos de processamento e pela API.
FEATURES_FILE = PROCESSED_DIR / "features.csv"

ISOLATION_MODEL_FILE = MODELS_DIR / "isolation.pkl"
SCALER_FILE = MODELS_DIR / "scaler.joblib"

AUTOENCODER_MODEL_FILE = AUTOENCODER_DIR / "model.keras"
# O limite de classificação do Autoencoder passou a ser salvo na raiz de data/models
# para simplificar auditoria e alinhamento entre treino e análise.
AUTOENCODER_THRESHOLD_FILE = MODELS_DIR / "threshold.pkl"
# Compatibilidade com arquivos de apoio antigos que ainda guardavam o limite de classificação
# dentro de data/models/autoencoder/.
LEGACY_AUTOENCODER_THRESHOLD_FILE = AUTOENCODER_DIR / "threshold.pkl"
ENSEMBLE_CONFIG_FILE = MODELS_DIR / "ensemble.json"
ISOLATION_STATS_FILE = MODELS_DIR / "isolation_stats.json"
AUTOENCODER_STATS_FILE = MODELS_DIR / "autoencoder_stats.json"

VALIDATION_PREDICTIONS_FILE = PROCESSED_DIR / "validation_predictions.csv"
VALIDATION_REPORT_FILE = MODELS_DIR / "validation_report.json"

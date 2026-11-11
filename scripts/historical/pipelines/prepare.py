"""Fluxo de processamento de preparacao de dados do Sinalyx.

Este script Lê conjuntos de dados brutos, padroniza colunas, normaliza rotulos e
gera as características que serao usadas nos modelos.
"""

import os
from typing import List

import pandas as pd

from src.core.paths import RAW_DIR, PROCESSED_DIR, FEATURES_FILE
from src.features.constants import BASE_FEATURE_COLUMNS
from src.features.engineering import add_engineered_features


def process_cicids(df: pd.DataFrame) -> pd.DataFrame:
    """Converte um Tabela de dados do conjunto de dados CICIDS para o formato padrão usado no projeto.

    Campos de saída:
        - connections
        - bytes
        - packets
        - packet_size
        - ports
        - rótulo
    """
    df = df.copy()
    df.columns = df.columns.str.strip()

    return pd.DataFrame(
        {
            "connections": pd.to_numeric(
                df.get("Flow Duration", 0), errors="coerce"
            ).fillna(0),
            "bytes": pd.to_numeric(
                df.get("Total Length of Fwd Packets", 0), errors="coerce"
            ).fillna(0),
            "packets": pd.to_numeric(
                df.get("Total Fwd Packets", 0), errors="coerce"
            ).fillna(0),
            "packet_size": pd.to_numeric(
                df.get("Average Packet Size", 0), errors="coerce"
            ).fillna(0),
            "ports": pd.to_numeric(
                df.get("Destination Port", 0), errors="coerce"
            ).fillna(0),
            "label": df.get("Label", "BENIGN").astype(str),
        }
    )


def process_unsw(df: pd.DataFrame) -> pd.DataFrame:
    """Converte um Tabela de dados do conjunto de dados UNSW-NB15 para o formato padrão usado no projeto.

    Neste projeto, o arquivo UNSW foi carregado sem cabeçalho.
    Por isso, a extração é feita por posição de coluna.

    Mapeamento utilizado:
        - connections -> coluna 1   (dur)
        - bytes       -> coluna 7   (sbytes)
        - packets     -> coluna 16  (spkts)
        - packet_size -> coluna 7   (sbytes, usado como aproximação)
        - ports       -> coluna 3   (sport)
        - rótulo       -> última coluna
    """
    df = df.copy()

    return pd.DataFrame(
        {
            "connections": pd.to_numeric(df.iloc[:, 1], errors="coerce").fillna(0),
            "bytes": pd.to_numeric(df.iloc[:, 7], errors="coerce").fillna(0),
            "packets": pd.to_numeric(df.iloc[:, 16], errors="coerce").fillna(0),
            "packet_size": pd.to_numeric(df.iloc[:, 7], errors="coerce").fillna(0),
            "ports": pd.to_numeric(df.iloc[:, 3], errors="coerce").fillna(0),
            "label": df.iloc[:, -1].astype(str),
        }
    )


def load_csv_file(file_path: str) -> pd.DataFrame:
    """Lê um arquivo CSV tentando separador vírgula primeiro e ponto e vírgula em seguida.

    Parâmetros:
        file_path: Caminho completo do arquivo CSV.

    Retorno:
        Tabela de dados com o conteúdo do arquivo.

    Erros:
        Exception: Repassa o erro caso nenhum formato consiga ser lido.
    """
    try:
        return pd.read_csv(file_path, sep=",", low_memory=False, skipinitialspace=True)
    except Exception:
        return pd.read_csv(file_path, sep=";", low_memory=False, skipinitialspace=True)


def identify_and_process_dataset(df: pd.DataFrame, file_name: str) -> pd.DataFrame | None:
    """Identifica o tipo do conjunto de dados e aplica o processamento correspondente.

    Regras atuais:
        - CICIDS: presença da coluna 'Flow Duration'
        - UNSW: ausência de header e mais de 40 colunas

    Parâmetros:
        df: Tabela de dados carregado do arquivo.
        file_name: Nome do arquivo, usado apenas para logs.

    Retorno:
        Tabela de dados padronizado ou None se o formato não for reconhecido.
    """
    normalized_df = df.copy()
    normalized_df.columns = normalized_df.columns.astype(str).str.strip()

    if "Flow Duration" in normalized_df.columns:
        print(f"[INFO] Dataset CICIDS identificado: {file_name}")
        return process_cicids(normalized_df)

    if normalized_df.shape[1] > 40:
        print(f"[INFO] Dataset UNSW identificado: {file_name}")
        return process_unsw(normalized_df)

    print(f"[WARNING] Formato de dataset não reconhecido: {file_name}")
    return None


def load_all_csvs(folder: str) -> pd.DataFrame:
    """Lê todos os arquivos CSV de uma pasta, identifica o conjunto de dados de cada arquivo
    e converte tudo para um formato único.

    Parâmetros:
        folder: Pasta onde os arquivos CSV estão armazenados.

    Retorno:
        Tabela de dados consolidado contendo todos os dados padronizados.

    Erros:
        RuntimeError: Caso nenhum conjunto de dados válido seja encontrado.
    """
    processed_frames: List[pd.DataFrame] = []

    for file_name in os.listdir(folder):
        if not file_name.endswith(".csv"):
            continue

        file_path = os.path.join(folder, file_name)
        print(f"[INFO] Carregando arquivo: {file_name}")

        df = load_csv_file(file_path)

        if df.empty:
            print(f"[WARNING] Arquivo vazio ignorado: {file_name}")
            continue

        processed_df = identify_and_process_dataset(df, file_name)

        if processed_df is not None:
            processed_frames.append(processed_df)

    if not processed_frames:
        raise RuntimeError("Nenhum dataset válido foi encontrado em data/raw.")

    return pd.concat(processed_frames, ignore_index=True)


def normalize_labels(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza os rótulos de classe para criar a coluna binária 'target'.

    Convenção:
        - 0 = tráfego benigno/normal
        - 1 = ataque/anomalia

    Parâmetros:
        df: Tabela de dados contendo a coluna 'rótulo'.

    Retorno:
        Tabela de dados com a coluna adicional 'target'.
    """
    df = df.copy()
    df["label"] = df["label"].astype(str).str.strip()

    benign_aliases = {
        "BENIGN",
        "Benign",
        "benign",
        "Normal",
        "normal",
        "NORMAL",
        "0",
        "0.0",
    }

    df["target"] = df["label"].apply(lambda value: 0 if value in benign_aliases else 1)
    return df


def add_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """Adiciona características derivadas e transformações logarítmicas ao conjunto de dados.

    Compatibilidade:
        - As 5 características canônicas do projeto são preservadas sem renomear.
        - O fluxo de processamento atual pode alternar entre características base e estendidas.
        - As novas colunas ficam disponíveis para análise exploratória
          e futuras iterações do modelo sem quebrar o fluxo existente.

    Características adicionadas:
        - bytes_per_packet
        - bytes_per_connection
        - packets_per_connection
        - log1p_connections
        - log1p_bytes
        - log1p_packets
        - log1p_packet_size
        - log1p_ports

    Parâmetros:
        df: Tabela de dados padronizado contendo ao menos as características canônicas.

    Retorno:
        Tabela de dados com colunas adicionais derivadas.
    """
    output = df.copy()
    engineered_df = add_engineered_features(output[BASE_FEATURE_COLUMNS].copy())

    for column in engineered_df.columns:
        output[column] = engineered_df[column]

    return output


def save_processed_dataset(df: pd.DataFrame) -> None:
    """Salva o conjunto de dados processado no caminho definido em FEATURES_FILE.

    Parâmetros:
        df: Tabela de dados final padronizado, com rótulos normalizados e
        colunas derivadas adicionais.
    """
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(FEATURES_FILE, index=False)


def main() -> None:
    """Executa o fluxo de processamento de preparação de dados:
        1. Lê todos os CSVs em data/raw
        2. Identifica o tipo de conjunto de dados
        3. Padroniza as colunas para o formato do projeto
        4. Normaliza os rótulos
        5. Gera características derivadas e versões log-transformadas
        6. Salva o resultado em data/processed/features.csv
    """
    df = load_all_csvs(str(RAW_DIR))
    df = normalize_labels(df)
    df = add_derived_features(df)
    save_processed_dataset(df)

    print("[INFO] Dados unificados com sucesso.")
    print(
        "[INFO] Features adicionais geradas: "
        "bytes_per_packet, bytes_per_connection, packets_per_connection "
        "e colunas log1p_*."
    )
    print(f"[INFO] Arquivo gerado em: {FEATURES_FILE}")


if __name__ == "__main__":
    main()

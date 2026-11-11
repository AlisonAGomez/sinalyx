"""Contrato operacional reduzido e isolamento de falhas de explicabilidade."""

import json
import logging
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

LOGGER = logging.getLogger(__name__)


class ComponentContributionItem(BaseModel):
    """Participação relativa e efeito calculado de um componente na explicação."""
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    shapley_value: float
    absolute_contribution: float = Field(ge=0)
    relative_share_percent: float = Field(ge=0, le=100)
    direction: Literal["toward_anomaly", "toward_normal", "neutral"]


class ComponentContributionComponents(BaseModel):
    """Agrupa as contribuições de regras e dos dois modelos."""
    model_config = ConfigDict(extra="forbid")
    autoencoder: ComponentContributionItem
    isolation_forest: ComponentContributionItem
    security_rules: ComponentContributionItem


class ComponentContributionsPayload(BaseModel):
    """Participação na magnitude Shapley; não representa probabilidade."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    methodology: Literal["exact_shapley_v1"]
    baseline_type: Literal["zero_signal_reference"]
    baseline_value: float = Field(ge=-1, le=1)
    full_value: float = Field(ge=-1, le=1)
    decision_span: float
    efficiency_residual: float
    components: ComponentContributionComponents


def projetar_contribuicoes(valor):
    """Valida objeto ou JSON já calculado; nunca calcula Shapley no transporte."""
    if valor is None:
        return None
    try:
        if isinstance(valor, str):
            valor = json.loads(valor)
        return ComponentContributionsPayload.model_validate(valor).model_dump(mode="json")
    except Exception:
        # Nunca inclui mensagem da exceção, sinais ou identificadores operacionais.
        LOGGER.error("component_contributions: falha de serializacao; metadado indisponivel")
        return None


def calcular_contribuicoes_seguras(*, decisao_oficial, ensemble_oficial, **entrada):
    """Falhas do metadado não interrompem nem modificam a decisão de segurança."""
    try:
        from src.models.component_contribution import (
            CAMPOS_CONTEXTO, PARTICIPANTES, TOLERANCIA,
            calculate_component_contribution, verificar_paridade,
        )
        # A seleção dos campos já remove rótulos de avaliação e identificadores antes do cálculo.
        for campo in ("features", "metadata"):
            entrada[campo] = {
                k: v for k, v in (entrada.get(campo) or {}).items() if k in CAMPOS_CONTEXTO
            }
        resultado = calculate_component_contribution(**entrada)
        completa = resultado["coalitions"]["+".join(PARTICIPANTES)]
        verificar_paridade(completa["decision"], decisao_oficial)
        for campo in ("score", "pred", "threshold", "if_weight", "ae_weight"):
            if not abs(completa["ensemble"][campo] - ensemble_oficial[campo]) <= TOLERANCIA:
                raise ValueError("Paridade do Ensemble divergente")
        reduzido = {k: resultado[k] for k in ComponentContributionsPayload.model_fields}
        return projetar_contribuicoes(reduzido)
    except Exception:
        LOGGER.error("component_contributions: falha de calculo ou paridade; metadado indisponivel")
        return None

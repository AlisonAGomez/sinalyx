import { expect, it } from 'vitest'
import { formatarConfianca } from '@/utils/formatters'

it.each([
  [0.8000000000000001, '0,80'], [0, '0,00'], [1, '1,00'], [0.375, '0,38'],
  [null, 'Não informado'], [undefined, 'Não informado'], [NaN, 'Não informado'],
  [Infinity, 'Não informado'], [-Infinity, 'Não informado'], ['0.8', 'Não informado'],
])('formata confiança somente para apresentação: %s → %s', (valor, esperado) => {
  expect(formatarConfianca(valor)).toBe(esperado)
})

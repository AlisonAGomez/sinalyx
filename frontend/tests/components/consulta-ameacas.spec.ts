import { mount } from '@vue/test-utils'
import { expect, it } from 'vitest'
import ConsultaAmeacas from '@/components/ui/ConsultaAmeacas.vue'
import { comportamentosConsulta, featuresConsulta, referenciasConsulta } from '@/content/consultaAmeacas'
import { janela } from '../fixtures/api'

it('documenta exatamente as 13 features oficiais na ordem, sem contexto experimental', () => {
  expect(featuresConsulta.map(item => item.chave)).toEqual([
    'connections', 'bytes', 'packets', 'packet_size', 'ports',
    'bytes_per_packet', 'bytes_per_connection', 'packets_per_connection',
    'log1p_connections', 'log1p_bytes', 'log1p_packets', 'log1p_packet_size', 'log1p_ports',
  ])
  const tela = mount(ConsultaAmeacas, { props: { janela: janela(1) } })
  expect(tela.get('[data-testid="feature-reference"]').findAll('dt')).toHaveLength(13)
  expect(featuresConsulta.every(item => item.definicao && item.unidade && item.uso && item.limite)).toBe(true)
  expect(tela.findAll('a').map(item => item.attributes('href'))).toEqual(referenciasConsulta.map(item => item.url))
  expect(tela.findAll('a').every(item => item.attributes('rel') === 'noopener noreferrer')).toBe(true)
})

it('inicia neutra e mantém a consulta independente da decisão, sem alterar o objeto recebido', async () => {
  const registro = Object.freeze(janela(2, {
    final_label: 'anomaly', attack_type: 'port_scan', risk_level: 'high', confidence: 0.87,
    decision_source: 'heuristic', features: Object.freeze({ connections: 12, bytes: 240, packets: 4, packet_size: 60, ports: 3, ctx_brute_force_hint: true }),
  }))
  const antes = JSON.stringify(registro)
  const tela = mount(ConsultaAmeacas, { props: { janela: registro } })
  expect(tela.get('select').element).toHaveProperty('value', '')
  expect(tela.text()).toContain('Selecione um comportamento para consultar')
  expect(tela.text()).toContain('Escolha um tipo de comportamento para conhecer os sinais de tráfego que podem estar associados a ele.')
  expect(tela.find('[aria-label="Decisão do Sinalyx"]').exists()).toBe(false)
  expect(tela.text()).not.toContain('Varredura de portas')
  expect(tela.text()).not.toContain('Volume e repetição de registros')
  for (const categoria of comportamentosConsulta) {
    await tela.get('select').setValue(categoria.id)
    expect(tela.get('[aria-label="Padrões associados"]').text()).toContain(categoria.descricao)
    expect(tela.get('[aria-label="Padrões associados"]').text()).toContain(categoria.limite)
    expect(tela.findAll('a').map(item => item.attributes('href'))).toEqual(referenciasConsulta.map(item => item.url))
  }
  expect(JSON.stringify(registro)).toBe(antes)
  expect(tela.text()).not.toContain('ctx_brute_force_hint')
  expect(tela.find('progress, [role="progressbar"]').exists()).toBe(false)
  expect(tela.text()).toContain('não confirmam isoladamente um ataque')
  expect(tela.text()).toContain('Ela não determina a classificação da janela.')
})

it('funciona sem features e volta ao estado neutro ao trocar a janela', async () => {
  const tela = mount(ConsultaAmeacas, { props: { janela: janela(1) } })
  await tela.get('select').setValue('dos')
  expect(tela.text()).toContain('não comprova DDoS')
  await tela.setProps({ janela: janela(2, { features: { connections: 0 } }) })
  expect(tela.get('select').element).toHaveProperty('value', '')
  expect(tela.text()).not.toContain('Volume e repetição de registros')
  expect(tela.get('[data-testid="feature-reference"]').findAll('dt')).toHaveLength(13)
})

it('apresenta categorias com limites de observabilidade, sem confirmação automática', async () => {
  const tela = mount(ConsultaAmeacas, { props: { janela: janela(1) } })
  expect(tela.findAll('option')).toHaveLength(5)
  await tela.get('select').setValue('dos')
  expect(tela.get('[aria-label="Padrões associados"]').text()).toContain('não comprova DDoS')
  await tela.get('select').setValue('brute-force')
  expect(tela.get('[aria-label="Padrões associados"]').text()).toContain('não confirmam falhas de senha')
  await tela.get('select').setValue('port-scan')
  expect(tela.get('[aria-label="Padrões associados"]').text()).toContain('não comprova intenção')
  await tela.get('select').setValue('anomalo')
  expect(tela.get('[aria-label="Padrões associados"]').text()).toContain('não mostram qual feature causou a decisão')
})

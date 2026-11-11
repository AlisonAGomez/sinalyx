/** Termo de busca compartilhado entre o cabeçalho e as páginas. */

import { computed, ref } from 'vue'

const globalSearch = ref('')

/** Compartilha o termo de busca entre o cabeçalho e as telas de consulta. */
export function useGlobalSearch() {
  const trimmedSearch = computed(() => globalSearch.value.trim())

  return {
    globalSearch,
    trimmedSearch,
  }
}

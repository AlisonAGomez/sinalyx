import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useAuth } from '@/composables/useAuth'

/** Aceita somente os destinos internos já permitidos pelo login anterior. */
function safeRedirect(value: unknown): string {
  if (typeof value !== 'string') return '/'
  return value.startsWith('/') && !value.startsWith('//') ? value : '/'
}

/** Compartilha o envio do formulário entre as duas apresentações, sem criar outra sessão. */
export function useLoginForm() {
  const email = ref('')
  const password = ref('')
  const showPassword = ref(false)
  const loading = ref(false)
  const error = ref('')
  const auth = useAuth()
  const router = useRouter()
  const route = useRoute()

  async function handleLogin(): Promise<void> {
    loading.value = true
    error.value = ''
    try {
      await auth.login(email.value.trim(), password.value)
      await router.push(safeRedirect(route.query.redirect))
    } catch {
      error.value = 'Não foi possível entrar. Verifique seus dados e tente novamente.'
    } finally {
      loading.value = false
    }
  }

  return { email, password, showPassword, loading, error, handleLogin }
}

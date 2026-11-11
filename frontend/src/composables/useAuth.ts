/** Sessão compartilhada do painel. A API continua responsável pelas permissões. */

import { computed, ref } from 'vue'

import { getCurrentUser, loginUser } from '@/services/api'
import type { AuthUser } from '@/types/api'

const TOKEN_KEY = 'sinalyx_access_token'
const USER_KEY = 'sinalyx_user'

/** Recupera a apresentação inicial da conta salva; permissões ainda precisam ser verificadas na API. */
function readStoredUser(): AuthUser | null {
  const raw = window.localStorage.getItem(USER_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw) as AuthUser
  } catch {
    window.localStorage.removeItem(USER_KEY)
    return null
  }
}

const token = ref(window.localStorage.getItem(TOKEN_KEY) ?? '')
const currentUser = ref<AuthUser | null>(readStoredUser())
const loadingUser = ref(false)
// O usuário em localStorage serve apenas para apresentação inicial. O papel é revalidado
// no servidor uma vez por carregamento da aplicação antes de liberar rotas protegidas.
const sessionValidated = ref(false)

/** Atualiza o estado da sessão e guarda o token e os dados públicos da conta no navegador. */
function persistSession(accessToken: string, user: AuthUser): void {
  token.value = accessToken
  currentUser.value = user
  window.localStorage.setItem(TOKEN_KEY, accessToken)
  window.localStorage.setItem(USER_KEY, JSON.stringify(user))
}

/** Remove a sessão do estado da aplicação e do armazenamento do navegador. */
function clearSession(): void {
  token.value = ''
  currentUser.value = null
  sessionValidated.value = false
  window.localStorage.removeItem(TOKEN_KEY)
  window.localStorage.removeItem(USER_KEY)
}

/** Compartilha a sessão entre telas e verifica a conta na API antes de liberar a navegação. */
export function useAuth() {
  const isAuthenticated = computed(() => Boolean(token.value && currentUser.value && sessionValidated.value))
  const isAdmin = computed(() => sessionValidated.value && currentUser.value?.role === 'admin')

  /** Envia as credenciais para a API e registra a sessão devolvida. */
  async function login(email: string, password: string): Promise<void> {
    const response = await loginUser(email.trim(), password)
    persistSession(response.access_token, response.user)
    sessionValidated.value = true
  }

  /** Confere a conta na API e limpa a sessão quando ela não pode mais ser usada. */
  async function loadMe(): Promise<AuthUser | null> {
    if (!token.value) {
      clearSession()
      return null
    }
    loadingUser.value = true
    try {
      const user = await getCurrentUser()
      persistSession(token.value, user)
      sessionValidated.value = true
      return user
    } catch {
      clearSession()
      return null
    } finally {
      loadingUser.value = false
    }
  }

  /** Limpa a sessão atual; a navegação após a saída fica a cargo de quem chamou. */
  function logout(): void {
    clearSession()
  }

  return {
    token,
    currentUser,
    loadingUser,
    sessionValidated,
    isAuthenticated,
    isAdmin,
    login,
    logout,
    loadMe,
  }
}

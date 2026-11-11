<!-- Administração de contas. A disponibilidade visual das ações não substitui a autorização na API. -->
<template>
  <section class="space-y-5" qa-id="page-admin-users" data-testid="page-admin-users" data-qa-page="admin-users">
    <PageHeader
      eyebrow="Administração"
      title="Usuários e permissões"
      description="Gerencie contas, papéis de acesso e status dos usuários autorizados a utilizar o Sinalyx."
    >
      <template #actions>
        <span v-if="meta" class="rounded-md border border-slate-800 bg-surface-900 px-3 py-2 text-sm text-slate-500">
          {{ meta.returned }} de {{ meta.total }}
        </span>
      </template>
    </PageHeader>

    <div class="grid gap-4 xl:grid-cols-[0.9fr_1.3fr]">
      <form
        class="panel space-y-3 p-4"
        qa-id="admin-user-form"
        data-testid="admin-user-form"
        data-qa-section="user-management"
        @submit.prevent="saveUser"
      >
        <div>
          <p class="text-xs font-medium text-slate-500">{{ editingUser ? 'Editar usuário' : 'Novo usuário' }}</p>
          <h2 class="mt-1 text-sm font-semibold text-white">Crie contas para acesso ao painel administrativo.</h2>
        </div>

        <label class="block text-sm">
          <span class="text-slate-300">Nome</span>
          <input
            v-model="form.name"
            class="field mt-2 h-10 w-full"
            name="user-name"
            qa-id="admin-user-name"
            data-testid="admin-user-name"
            aria-label="Nome do usuário"
            maxlength="120"
            required
          />
        </label>
        <label class="block text-sm">
          <span class="text-slate-300">Email</span>
          <input
            v-model="form.email"
            class="field mt-2 h-10 w-full"
            type="email"
            name="user-email"
            qa-id="admin-user-email"
            data-testid="admin-user-email"
            aria-label="Email do usuário"
            autocomplete="username"
            maxlength="254"
            required
            :disabled="editingProtectedUser"
          />
        </label>
        <label class="block text-sm">
          <span class="text-slate-300">Senha</span>
          <input
            v-model="form.password"
            class="field mt-2 h-10 w-full"
            type="password"
            name="user-password"
            qa-id="admin-user-password"
            data-testid="admin-user-password"
            aria-label="Senha do usuário"
            autocomplete="new-password"
            minlength="8"
            maxlength="128"
            :required="!editingUser"
            placeholder="Obrigatória para novo usuário"
          />
        </label>
        <div class="grid gap-3 sm:grid-cols-2">
          <label class="block text-sm">
            <span class="text-slate-300">Papel</span>
            <select
              v-model="form.role"
              class="field mt-2 h-10 w-full"
              name="user-role"
              qa-id="admin-user-role"
              data-testid="admin-user-role"
              aria-label="Papel do usuário"
              :disabled="editingProtectedUser"
            >
              <option value="user">Usuário</option>
              <option value="admin">Administrador</option>
            </select>
          </label>
          <label class="flex items-center gap-2 pt-7 text-sm text-slate-300">
            <input
              v-model="form.is_active"
              type="checkbox"
              name="user-active"
              qa-id="admin-user-active"
              data-testid="admin-user-active"
              aria-label="Usuário ativo"
              :disabled="editingProtectedUser"
            />
            Ativo
          </label>
        </div>

        <p v-if="editingProtectedUser" class="rounded-md border border-sky-400/20 bg-sky-400/10 px-3 py-2 text-sm text-sky-100">
          Administrador protegido: esta conta não pode ser desativada, removida, rebaixada ou ter o email alterado.
        </p>

        <p
          v-if="feedback"
          class="rounded-md border border-slate-800 bg-surface-850 px-3 py-2 text-sm text-slate-300"
          qa-id="admin-user-feedback"
          data-testid="admin-user-feedback"
          role="status"
        >
          {{ feedback }}
        </p>

        <div class="flex flex-wrap gap-2">
          <button class="btn btn-primary" type="submit" qa-id="admin-user-save" data-testid="admin-user-save" :disabled="saving">
            {{ saving ? 'Salvando…' : editingUser ? 'Salvar alterações' : 'Criar usuário' }}
          </button>
          <button class="btn btn-secondary" type="button" qa-id="admin-user-clear" data-testid="admin-user-clear" :disabled="saving" @click="resetForm()">
            Limpar
          </button>
        </div>
      </form>

      <div>
        <LoadingState v-if="loading" />
        <ErrorState v-else-if="error" :message="error" />
        <div v-else class="panel overflow-hidden" qa-id="admin-users-table" data-testid="admin-users-table">
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-slate-800 text-sm">
              <thead class="bg-surface-850 text-left text-xs uppercase text-slate-500">
                <tr>
                  <th class="px-4 py-3 font-medium">Nome</th>
                  <th class="px-4 py-3 font-medium">Email</th>
                  <th class="px-4 py-3 font-medium">Papel</th>
                  <th class="px-4 py-3 font-medium">Status</th>
                  <th class="px-4 py-3 font-medium">Ações</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-800">
                <tr
                  v-for="user in users"
                  :key="user.id"
                  :qa-id="`admin-user-row-${user.id}`"
                  :data-testid="`admin-user-row-${user.id}`"
                >
                  <td class="px-4 py-3 font-medium text-white text-wrap-safe">
                    {{ user.name }}
                  </td>
                  <td class="whitespace-nowrap px-4 py-3 text-slate-300">{{ user.email }}</td>
                  <td class="px-4 py-3 text-slate-300">{{ user.role === 'admin' ? 'Administrador' : 'Usuário' }}</td>
                  <td class="px-4 py-3">
                    <StatusBadge :value="user.is_active" />
                  </td>
                  <td class="px-4 py-3">
                    <div v-if="isProtectedAdmin(user)" class="flex flex-wrap gap-2">
                      <span
                        class="rounded-md border border-slate-700 bg-surface-850 px-3 py-2 text-sm font-medium text-slate-300"
                        :qa-id="`admin-user-protected-${user.id}`"
                        :data-testid="`admin-user-protected-${user.id}`"
                      >
                        Protegido
                      </span>
                    </div>
                    <div v-else class="flex flex-wrap gap-2">
                      <button
                        class="btn btn-secondary"
                        type="button"
                        :qa-id="`admin-user-edit-${user.id}`"
                        :data-testid="`admin-user-edit-${user.id}`"
                        @click="editUser(user)"
                      >
                        Editar
                      </button>
                      <button
                        class="btn"
                        :class="user.is_active ? 'btn-secondary' : 'btn-success'"
                        type="button"
                        :qa-id="`admin-user-toggle-status-${user.id}`"
                        :data-testid="`admin-user-toggle-status-${user.id}`"
                        title="Alterar status"
                        :disabled="busyUserId === user.id"
                        @click="toggleStatus(user)"
                      >
                        {{ user.is_active ? 'Desativar' : 'Ativar' }}
                      </button>
                      <button
                        class="btn btn-danger"
                        type="button"
                        :qa-id="`admin-user-remove-${user.id}`"
                        :data-testid="`admin-user-remove-${user.id}`"
                        :disabled="user.id === currentUser?.id || busyUserId === user.id"
                        :title="removeTitle(user)"
                        @click="removeUser(user)"
                      >
                        Remover
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'

import ErrorState from '@/components/ui/ErrorState.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import {
  createAdminUser,
  deleteAdminUser,
  getAdminUsers,
  updateAdminUser,
  updateAdminUserStatus,
} from '@/services/api'
import type { AuthUser, PaginationMeta, UserPayload, UserRole } from '@/types/api'
import { useAuth } from '@/composables/useAuth'

const users = ref<AuthUser[]>([])
const meta = ref<PaginationMeta | null>(null)
const loading = ref(true)
const error = ref('')
const feedback = ref('')
const saving = ref(false)
const busyUserId = ref<number | null>(null)
const editingUser = ref<AuthUser | null>(null)
const { currentUser } = useAuth()
const editingProtectedUser = computed(() => isProtectedAdmin(editingUser.value))
const form = reactive<{
  name: string
  email: string
  password: string
  role: UserRole
  is_active: boolean
}>({
  name: '',
  email: '',
  password: '',
  role: 'user',
  is_active: true,
})

/** Identifica a conta administrativa protegida para orientar os controles visuais. */
function isProtectedAdmin(user: AuthUser | null | undefined): boolean {
  return user?.is_protected === true
}

/** Escolhe o texto do controle de remoção conforme a proteção da conta. */
function removeTitle(user: AuthUser): string {
  if (isProtectedAdmin(user)) {
    return 'O administrador supremo nao pode ser removido.'
  }
  if (user.id === currentUser.value?.id) {
    return 'Nao e possivel remover o proprio usuario.'
  }
  return 'Remover usuario'
}

/** Carrega as contas e controla os estados de espera e erro da tela. */
async function loadUsers(): Promise<void> {
  loading.value = true
  error.value = ''
  try {
    const response = await getAdminUsers(100, 0)
    users.value = response.users
    meta.value = response.meta
  } catch {
    error.value = 'Não foi possível carregar os usuários.'
  } finally {
    loading.value = false
  }
}

/** Limpa os campos de edição e retorna o formulário ao estado inicial. */
function resetForm(clearFeedback = true): void {
  editingUser.value = null
  form.name = ''
  form.email = ''
  form.password = ''
  form.role = 'user'
  form.is_active = true
  if (clearFeedback) feedback.value = ''
}

/** Preenche o formulário com os dados públicos da conta selecionada. */
function editUser(user: AuthUser): void {
  editingUser.value = user
  form.name = user.name
  form.email = user.email
  form.password = ''
  form.role = user.role
  form.is_active = isProtectedAdmin(user) ? true : user.is_active
  feedback.value = ''
}

/** Envia a criação ou edição da conta e atualiza a listagem após sucesso. */
async function saveUser(): Promise<void> {
  if (saving.value) return
  feedback.value = ''
  saving.value = true
  const payload: UserPayload = {
    name: form.name.trim(),
    email: form.email.trim(),
    role: editingProtectedUser.value ? 'admin' : form.role,
    is_active: editingProtectedUser.value ? true : form.is_active,
  }
  if (form.password) payload.password = form.password

  try {
    if (editingUser.value) {
      await updateAdminUser(editingUser.value.id, payload)
      feedback.value = 'Usuário atualizado com sucesso.'
    } else {
      await createAdminUser({ ...payload, password: form.password })
      feedback.value = 'Usuário criado com sucesso.'
    }
    resetForm(false)
    await loadUsers()
  } catch {
    feedback.value = 'Não foi possível salvar o usuário.'
  } finally {
    saving.value = false
  }
}

/** Solicita a mudança de estado da conta e atualiza a lista após sucesso. */
async function toggleStatus(user: AuthUser): Promise<void> {
  if (isProtectedAdmin(user)) {
    feedback.value = 'O administrador supremo nao pode ser desativado.'
    return
  }
  const action = user.is_active ? 'desativar' : 'ativar'
  const confirmed = window.confirm(`Deseja ${action} o usuário ${user.email}?`)
  if (!confirmed) {
    return
  }
  busyUserId.value = user.id
  try {
    await updateAdminUserStatus(user.id, !user.is_active)
    await loadUsers()
  } catch {
    feedback.value = 'Não foi possível alterar o status do usuário.'
  } finally {
    busyUserId.value = null
  }
}

/** Solicita a remoção autorizada da conta selecionada e atualiza a tela. */
async function removeUser(user: AuthUser): Promise<void> {
  if (isProtectedAdmin(user)) {
    feedback.value = 'O administrador supremo nao pode ser removido.'
    return
  }
  if (user.id === currentUser.value?.id) {
    feedback.value = 'Não é possível remover o próprio usuário autenticado.'
    return
  }
  const confirmed = window.confirm(`Remover definitivamente o usuário ${user.email}?`)
  if (!confirmed) {
    return
  }
  busyUserId.value = user.id
  try {
    await deleteAdminUser(user.id)
    feedback.value = 'Usuário removido com sucesso.'
    if (editingUser.value?.id === user.id) resetForm(false)
    await loadUsers()
  } catch {
    feedback.value = 'Não foi possível remover o usuário.'
  } finally {
    busyUserId.value = null
  }
}

onMounted(loadUsers)
</script>

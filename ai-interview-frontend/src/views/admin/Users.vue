<template>
  <div>
    <div class="page-header">
      <h1 class="admin-page-title">&#x1F465; 用户管理</h1>
      <input v-model="keyword" class="search-input" placeholder="搜索邮箱/姓名..." @input="debouncedSearch" />
    </div>

    <div class="table-container">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>邮箱</th>
            <th>姓名</th>
            <th>状态</th>
            <th>注册时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in users" :key="u.id">
            <td>{{ u.id }}</td>
            <td>{{ u.email }}</td>
            <td>{{ u.first_name }} {{ u.last_name }}</td>
            <td><span :class="['badge', u.is_active ? 'badge-green' : 'badge-red']">{{ u.is_active ? '正常' : '禁用' }}</span></td>
            <td>{{ formatDate(u.created_at) }}</td>
            <td>
              <button :class="u.is_active ? 'btn-danger btn-sm' : 'btn-primary btn-sm'" @click="toggleActive(u)">
                {{ u.is_active ? '禁用' : '启用' }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <div class="admin-pagination" v-if="total > perPage">
        <button class="btn-sm" :disabled="page <= 1" @click="page--; loadUsers()">上一页</button>
        <span>{{ page }} / {{ Math.ceil(total / perPage) }}</span>
        <button class="btn-sm" :disabled="page >= Math.ceil(total / perPage)" @click="page++; loadUsers()">下一页</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { adminUserApi } from '../../api/adminApi'

const users = ref([])
const total = ref(0)
const page = ref(1)
const perPage = 20
const keyword = ref('')
let searchTimer = null

function formatDate(str) {
  if (!str) return ''
  return new Date(str).toLocaleString('zh-CN')
}

async function loadUsers() {
  try {
    const data = await adminUserApi.list({ page: page.value, per_page: perPage, keyword: keyword.value || undefined })
    users.value = data.items
    total.value = data.total
  } catch (e) { console.error(e) }
}

function debouncedSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => { page.value = 1; loadUsers() }, 300)
}

async function toggleActive(user) {
  try {
    const data = await adminUserApi.toggleActive(user.id)
    user.is_active = data.is_active
  } catch (e) { console.error(e) }
}

onMounted(loadUsers)
</script>

<style scoped>
.admin-page-title {
  font-family: var(--font-display);
  font-size: var(--text-2xl);
  font-weight: 400;
  letter-spacing: -0.02em;
}
.search-input {
  width: 240px;
  height: 40px;
  padding: 0 var(--space-4);
  border: 1px solid var(--c-border);
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
  background: var(--c-surface);
}
.search-input:focus {
  border-color: var(--c-primary);
  box-shadow: var(--shadow-glow);
}
</style>

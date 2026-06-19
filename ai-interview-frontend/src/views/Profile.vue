<template>
  <div class="container">
    <div class="profile-page">
      <h2 class="page-title">个人中心</h2>

      <div class="card avatar-section">
        <div class="avatar-wrapper" @click="$refs.avatarInput.click()">
          <img v-if="profile.avatar" :src="avatarUrl" class="avatar-img" alt="avatar" />
          <div v-else class="avatar-placeholder">{{ initials }}</div>
          <div class="avatar-overlay">&#x1F4F7;</div>
          <input ref="avatarInput" type="file" accept="image/*" @change="handleAvatarChange" hidden />
        </div>
        <div class="avatar-info">
          <p class="avatar-name">{{ profile.first_name || '' }} {{ profile.last_name || '' }}</p>
          <p class="avatar-email">{{ profile.email }}</p>
        </div>
      </div>

      <div class="card section-card">
        <h3 class="section-title">基本信息</h3>
        <div class="form-row">
          <div class="form-group">
            <label>姓</label>
            <input v-model="form.last_name" placeholder="姓" />
          </div>
          <div class="form-group">
            <label>名</label>
            <input v-model="form.first_name" placeholder="名" />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>性别</label>
            <select v-model="form.gender">
              <option value="">未设置</option>
              <option value="male">男</option>
              <option value="female">女</option>
            </select>
          </div>
          <div class="form-group">
            <label>手机号</label>
            <input v-model="form.phone" placeholder="手机号" />
          </div>
        </div>
        <div class="form-group">
          <label>学校</label>
          <input v-model="form.university" placeholder="学校名称" />
        </div>
        <div class="form-group">
          <label>求职目标</label>
          <input v-model="form.career_goal" placeholder="例如：Python后端开发工程师" />
        </div>
        <div class="form-group">
          <label>所在城市</label>
          <input v-model="form.location" placeholder="例如：上海" />
        </div>
        <button class="btn-primary full-btn" @click="handleSaveProfile" :disabled="saving">
          {{ saving ? '保存中...' : '保存信息' }}
        </button>
      </div>

      <div class="card section-card">
        <h3 class="section-title">修改密码</h3>
        <div class="form-group">
          <label>当前密码</label>
          <div class="password-wrapper">
            <input v-model="pwForm.old_password" :type="showOldPw ? 'text' : 'password'" placeholder="输入当前密码" />
            <button type="button" class="password-toggle" @click="showOldPw = !showOldPw" tabindex="-1">
              {{ showOldPw ? '&#x1F648;' : '&#x1F441;' }}
            </button>
          </div>
        </div>
        <div class="form-group">
          <label>新密码</label>
          <div class="password-wrapper">
            <input v-model="pwForm.new_password" :type="showNewPw ? 'text' : 'password'" placeholder="至少6位" />
            <button type="button" class="password-toggle" @click="showNewPw = !showNewPw" tabindex="-1">
              {{ showNewPw ? '&#x1F648;' : '&#x1F441;' }}
            </button>
          </div>
        </div>
        <div class="form-group">
          <label>确认新密码</label>
          <div class="password-wrapper">
            <input v-model="pwForm.confirm_password" :type="showConfirmPw ? 'text' : 'password'" placeholder="再次输入新密码" />
            <button type="button" class="password-toggle" @click="showConfirmPw = !showConfirmPw" tabindex="-1">
              {{ showConfirmPw ? '&#x1F648;' : '&#x1F441;' }}
            </button>
          </div>
        </div>
        <button class="btn-primary full-btn" @click="handleChangePassword" :disabled="changingPw">
          {{ changingPw ? '修改中...' : '修改密码' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getProfile, updateProfile, uploadAvatar, changePassword } from '../api/user'
import { useToastStore } from '../stores/toast'

const toast = useToastStore()

const profile = ref({})
const form = ref({ first_name: '', last_name: '', gender: '', phone: '', university: '', career_goal: '', location: '' })
const pwForm = ref({ old_password: '', new_password: '', confirm_password: '' })
const showOldPw = ref(false)
const showNewPw = ref(false)
const showConfirmPw = ref(false)
const saving = ref(false)
const changingPw = ref(false)

const avatarUrl = computed(() => {
  if (!profile.value.avatar) return ''
  return profile.value.avatar
})

const initials = computed(() => {
  const f = profile.value.first_name || ''
  const l = profile.value.last_name || ''
  return (l.charAt(0) + f.charAt(0)).toUpperCase() || 'U'
})

onMounted(async () => {
  try {
    const data = await getProfile()
    profile.value = data
    form.value = {
      first_name: data.first_name || '',
      last_name: data.last_name || '',
      gender: data.gender || '',
      phone: data.phone || '',
      university: data.university || '',
      career_goal: data.career_goal || '',
      location: data.location || ''
    }
  } catch (e) {
    toast.error('加载个人信息失败')
  }
})

async function handleAvatarChange(e) {
  const file = e.target.files[0]
  if (!file) return
  try {
    const data = await uploadAvatar(file)
    profile.value.avatar = data.avatar
    toast.success('头像已更新')
  } catch (e) {
    toast.error('头像上传失败: ' + e.message)
  }
}

async function handleSaveProfile() {
  saving.value = true
  try {
    await updateProfile(form.value)
    profile.value = { ...profile.value, ...form.value }
    toast.success('保存成功')
  } catch (e) {
    toast.error('保存失败: ' + e.message)
  } finally {
    saving.value = false
  }
}

async function handleChangePassword() {
  if (!pwForm.value.old_password) {
    toast.warning('请输入当前密码')
    return
  }
  if (pwForm.value.new_password !== pwForm.value.confirm_password) {
    toast.warning('两次密码不一致')
    return
  }
  if (pwForm.value.new_password.length < 6) {
    toast.warning('新密码至少6位')
    return
  }
  changingPw.value = true
  try {
    await changePassword(pwForm.value.old_password, pwForm.value.new_password)
    toast.success('密码修改成功')
    pwForm.value = { old_password: '', new_password: '', confirm_password: '' }
  } catch (e) {
    toast.error('修改失败: ' + e.message)
  } finally {
    changingPw.value = false
  }
}
</script>

<style scoped>
.profile-page { max-width: 560px; margin: var(--space-6) auto; }
.page-title {
  font-family: var(--font-display);
  margin-bottom: var(--space-6);
  font-size: var(--text-3xl);
  font-weight: 400;
  letter-spacing: -0.03em;
}

/* 头像区 */
.avatar-section {
  display: flex; align-items: center; gap: var(--space-6);
  padding: var(--space-8);
}
.avatar-wrapper {
  width: 92px; height: 92px; border-radius: 50%; position: relative;
  cursor: pointer; overflow: hidden; flex-shrink: 0;
  border: 3px solid var(--c-primary);
  box-shadow: var(--shadow-sm);
  transition: box-shadow var(--duration-fast);
}
.avatar-wrapper:hover {
  box-shadow: var(--shadow-lg);
}
.avatar-img { width: 100%; height: 100%; object-fit: cover; }
.avatar-placeholder {
  width: 100%; height: 100%;
  background: var(--c-primary);
  color: white; display: flex; align-items: center; justify-content: center;
  font-size: 28px; font-weight: 600;
  font-family: var(--font-mono);
}
.avatar-overlay {
  position: absolute; inset: 0; background: rgba(0,0,0,0.4);
  display: flex; align-items: center; justify-content: center;
  font-size: 24px; opacity: 0; transition: opacity 0.2s;
}
.avatar-wrapper:hover .avatar-overlay { opacity: 1; }
.avatar-name {
  font-family: var(--font-display);
  font-size: var(--text-xl);
  font-weight: 400;
  letter-spacing: -0.02em;
}
.avatar-email { font-size: var(--text-sm); color: var(--c-text-secondary); margin-top: var(--space-1); }

/* 段落卡片 */
.section-card { margin-top: var(--space-4); }
.section-title {
  font-family: var(--font-display);
  margin-bottom: var(--space-5);
  font-size: var(--text-lg);
  font-weight: 400;
  letter-spacing: -0.01em;
  padding-bottom: var(--space-3);
  border-bottom: 2px solid var(--c-border-light);
}
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-3); }
.full-btn { width: 100%; margin-top: var(--space-2); padding: 12px; font-weight: 600; letter-spacing: 0.02em; }

@media (max-width: 640px) {
  .avatar-section { flex-direction: column; text-align: center; }
  .form-row { grid-template-columns: 1fr; }
}
</style>

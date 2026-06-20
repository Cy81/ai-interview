import api from './request'

export function login(email, password, rememberMe = false) {
  return api.post('/auth/login', { email, password, remember_me: rememberMe })
}

export function register(data) {
  return api.post('/auth/register', data)
}

export function sendVerificationCode(email, codeType) {
  return api.post('/auth/send-verification-code', { email, code_type: codeType })
}

export function verifyEmail(email, code) {
  return api.post('/auth/verify-email', { email, code })
}

export function refreshToken(refreshToken) {
  return api.post('/auth/refresh', { refresh_token: refreshToken })
}

export function logout(refreshToken) {
  return api.post('/auth/logout', { refresh_token: refreshToken })
}

export function sendPasswordResetCode(email) {
  return api.post('/auth/password-reset/send-code', { email })
}

export function verifyPasswordResetCode(email, code) {
  return api.post('/auth/password-reset/verify-code', { email, code })
}

export function resetPassword(resetToken, newPassword, confirmPassword) {
  return api.post('/auth/password-reset/reset', {
    reset_token: resetToken,
    new_password: newPassword,
    confirm_password: confirmPassword
  })
}

export function getCurrentUser() {
  return api.get('/auth/me')
}

export function updateProfile(data) {
  return api.put('/auth/me', data)
}

export function changePassword(oldPassword, newPassword) {
  return api.post('/auth/me/change-password', {
    old_password: oldPassword,
    new_password: newPassword
  })
}

import client from './client';

export default {
  login(email, password) {
    return client.post('/auth/login', { email, password });
  },
  register(payload) {
    return client.post('/auth/register', {
      // step 1
      email:       payload.email,
      password:    payload.password,
      firstName:   payload.firstName,
      lastName:    payload.lastName,
      dateOfBirth: payload.dateOfBirth || null,
      sex:         payload.sex,
      // step 2 — required
      phone:       payload.phone,
      middleName:        payload.middleName        ?? null,
      heightCm:          payload.heightCm          ?? null,
      weightKg:          payload.weightKg          ?? null,
      smoker:            payload.smoker            ?? null,
      alcoholFrequency:  payload.alcoholFrequency  ?? null,
      physicalActivity:  payload.physicalActivity  ?? null,
      dietType:          payload.dietType          ?? null,
      chronicDiseases:    payload.chronicDiseases    ?? null,
      allergies:          payload.allergies          ?? null,
      currentMedications: payload.currentMedications ?? null,
      familyHistory:      payload.familyHistory      ?? null,
      emergencyContactName:     payload.emergencyContactName     ?? null,
      emergencyContactPhone:    payload.emergencyContactPhone    ?? null,
      emergencyContactRelation: payload.emergencyContactRelation ?? null,
    });
  },
  refresh(refreshToken) {
    return client.post('/auth/refresh', { refreshToken });
  },
  logout(refreshToken) {
    return client.post('/auth/logout', { refreshToken });
  },
  me() {
    return client.get('/auth/me');
  },
  changePassword(currentPassword, newPassword) {
    return client.post('/auth/change-password', { currentPassword, newPassword });
  },
};

<template>
  <div v-if="note" class="doctor-note">
    <h4><i class="fa-solid fa-user-doctor"></i> {{ $t('results.headers.doctorNote') }}</h4>
    <p>{{ note }}</p>
  </div>
</template>

<script>
export default {
  name: "DoctorNote",
  props: { note: { type: String, default: null } },
};
</script>

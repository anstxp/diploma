<template>
  <div class="patient-card" :class="{ clickable: isAccepted }" @click="onCardClick">
    <div class="avatar">
      <img v-if="patient.avatarUrl" :src="patient.avatarUrl" :alt="patient.fullName" />
      <span v-else>{{ initials }}</span>
    </div>
    <div class="info">
      <div class="name">{{ patient.fullName || (patient.firstName + " " + patient.lastName) }}</div>
      <div class="meta">
        <span v-if="patient.age != null">{{ patient.age }} {{ $t('patients.card.yearShort') }}</span>
        <span v-if="patient.email">{{ patient.email }}</span>
      </div>
      <div class="status">
        <span :class="['status-pill', statusClass]">{{ statusLabel }}</span>
      </div>
    </div>
    <div class="actions" @click.stop>
      <button v-if="canRespond" class="btn-small" @click="$emit('accept', patient.linkId)">
        {{ $t('patients.card.accept') }}
      </button>
      <button v-if="canRespond" class="btn-outline btn-small" @click="$emit('decline', patient.linkId)">
        {{ $t('patients.card.decline') }}
      </button>
      <router-link
        v-if="isAccepted"
        :to="`/doctors/patients/${patient.userId}`"
        class="btn-small"
      >
        {{ $t('patients.card.view') }}
      </router-link>
      <button
        v-if="isAccepted"
        class="btn-outline btn-small revoke-btn"
        @click.stop="$emit('revoke', patient.linkId)"
      >
        {{ $t('patients.card.revoke') }}
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: "PatientCard",
  props: {
    patient: { type: Object, required: true },
  },
  emits: ["accept", "decline", "revoke"],
  computed: {
    initials() {
      const fn = this.patient.firstName || "?";
      const ln = this.patient.lastName || "";
      return (fn[0] + (ln[0] || "")).toUpperCase();
    },
    statusLabel() {
      const map = {
        Pending:  this.$t('patients.card.statusPending'),
        Accepted: this.$t('patients.card.statusAccepted'),
        Rejected: this.$t('patients.card.statusRejected'),
        Declined: this.$t('patients.card.statusRejected'), // legacy alias
        Revoked:  this.$t('patients.card.statusRevoked'),
      };
      return map[this.patient.status] || this.patient.status;
    },
    statusClass() {
      const map = {
        Pending: "monitor",
        Accepted: "normal",
        Rejected: "urgent",
        Declined: "urgent",
        Revoked: "urgent",
      };
      return map[this.patient.status] || "info";
    },
    canRespond() {
      return this.patient.status === "Pending" && this.patient.canRespond;
    },
    isAccepted() {
      return this.patient.status === "Accepted";
    },
  },
  methods: {
    onCardClick() {
      if (this.isAccepted && this.patient.userId) {
        this.$router.push(`/doctors/patients/${this.patient.userId}`);
      }
    },
  },
};
</script>

<style scoped lang="scss">
.patient-card {
  background: white;
  border: var(--border);
  border-radius: 0.6rem;
  padding: 1.4rem;
  display: grid;
  grid-template-columns: 5rem 1fr auto;
  gap: 1.4rem;
  align-items: center;
  transition: all 0.15s;

  &.clickable {
    cursor: pointer;
    &:hover { border-color: var(--purple); box-shadow: var(--box-shadow); }
  }

  .avatar {
    width: 5rem;
    height: 5rem;
    border-radius: 50%;
    background: var(--purple);
    color: white;
    font-weight: 600;
    font-size: 1.6rem;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;

    img { width: 100%; height: 100%; object-fit: cover; display: block; }
  }

  .info {
    .name {
      font-size: 1.5rem;
      color: var(--black);
      font-weight: 600;
      margin-bottom: 0.2rem;
      text-transform: none;
    }

    .meta {
      display: flex;
      gap: 1rem;
      font-size: 1.2rem;
      color: var(--light-color);
      text-transform: none;
      margin-bottom: 0.4rem;
    }
  }

  .status-pill {
    display: inline-block;
    padding: 0.3rem 0.8rem;
    border-radius: 0.3rem;
    font-size: 1.1rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.05rem;

    &.normal  { background: var(--severity-normal-bg);  color: var(--severity-normal-text); }
    &.monitor { background: var(--severity-monitor-bg); color: var(--severity-monitor-text); }
    &.urgent  { background: var(--severity-urgent-bg);  color: var(--severity-urgent-text); }
    &.info    { background: rgba(65, 90, 119, 0.12);    color: var(--purple); }
  }

  .actions {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
    .btn-small, .btn-outline { white-space: nowrap; }
    .revoke-btn { color: var(--severity-urgent-text); border-color: var(--severity-urgent-text); }
  }
}

@media (max-width: 600px) {
  .patient-card {
    grid-template-columns: 4.4rem 1fr;
    .actions {
      grid-column: 1 / -1;
      flex-direction: row;
      justify-content: flex-end;
    }
  }
}
</style>

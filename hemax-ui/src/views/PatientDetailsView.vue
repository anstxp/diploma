<template>
  <BottomNavbarComponent />
  <HeaderComponent />
  <NavbarComponent />

  <main class="page">
    <button class="link-back" @click="$router.push('/patients')">
      <i class="fa-solid fa-arrow-left"></i> {{ $t('patientDetails.backToList') }}
    </button>

    <div v-if="loading" class="loader">{{ $t('patientDetails.loading') }}</div>

    <div v-else-if="!patient" class="empty-state">
      <i class="fa-solid fa-circle-exclamation"></i>
      <p>{{ $t('patientDetails.notFound') }}</p>
      <p class="muted">{{ $t('patientDetails.notFoundHint') }}</p>
    </div>

    <template v-else>
      <div class="patient-header">
        <div class="patient-avatar">
          <img v-if="patient.patientAvatarUrl || profile?.avatarUrl"
               :src="patient.patientAvatarUrl || profile.avatarUrl"
               :alt="patient.patientName" />
          <span v-else>{{ initials }}</span>
        </div>
        <div class="patient-info">
          <h1>{{ patient.patientName || $t('patientDetails.unknownPatient') }}</h1>
          <div class="meta">
            <span class="status-pill" :class="statusClass">{{ statusLabel }}</span>
            <span v-if="patient.patientAge != null" class="meta-item">
              <i class="fa-solid fa-cake-candles"></i>
              {{ patient.patientAge }} {{ ageWord(patient.patientAge) }}
            </span>
            <span v-if="profile?.sex && profile.sex !== 'Unknown'" class="meta-item">
              <i class="fa-solid fa-venus-mars"></i>
              {{ sexLabel(profile.sex) }}
            </span>
            <span v-if="patient.patientEmail" class="meta-item">
              <i class="fa-solid fa-envelope"></i> {{ patient.patientEmail }}
            </span>
            <span v-if="profile?.phone" class="meta-item">
              <i class="fa-solid fa-phone"></i> {{ profile.phone }}
            </span>
            <span v-if="patient.createdAt" class="meta-item">
              <i class="fa-solid fa-calendar"></i>
              {{ $t('patientDetails.connectedAt', { date: formatDate(patient.respondedAt || patient.createdAt) }) }}
            </span>
          </div>
          <p v-if="patient.note" class="note">{{ patient.note }}</p>
        </div>
      </div>

      <section class="medical-card-block">
        <div class="block-head">
          <h2><i class="fa-solid fa-notes-medical"></i> {{ $t('patientDetails.medicalCardTitle') }}</h2>
        </div>

        <div v-if="loadingProfile" class="loader">{{ $t('patientDetails.loadingMedicalCard') }}</div>

        <div v-else-if="profileError" class="empty-state small">
          <i class="fa-solid fa-circle-exclamation"></i>
          <p>{{ profileError }}</p>
        </div>

        <div v-else-if="profile" class="card-grid">
          <!-- Anthropometrics -->
          <div class="card">
            <h3>{{ $t('patientDetails.anthroTitle') }}</h3>
            <dl>
              <div><dt>{{ $t('patientDetails.heightLabel') }}</dt><dd>{{ fmtNumber(profile.heightCm, $t('patientDetails.heightUnit')) }}</dd></div>
              <div><dt>{{ $t('patientDetails.weightLabel') }}</dt><dd>{{ fmtNumber(profile.weightKg, $t('patientDetails.weightUnit')) }}</dd></div>
              <div v-if="profile.bmi"><dt>{{ $t('patientDetails.bmiLabel') }}</dt><dd>{{ profile.bmi }}</dd></div>
              <div v-if="profile.waistCm"><dt>{{ $t('patientDetails.waistLabel') }}</dt><dd>{{ profile.waistCm }} {{ $t('patientDetails.waistUnit') }}</dd></div>
            </dl>
          </div>

          <!-- Vitals -->
          <div v-if="hasVitals" class="card">
            <h3>{{ $t('patientDetails.vitalsTitle') }}</h3>
            <dl>
              <div v-if="profile.typicalSystolicBp || profile.typicalDiastolicBp">
                <dt>{{ $t('patientDetails.bpLabel') }}</dt>
                <dd>
                  {{ profile.typicalSystolicBp || $t('patientDetails.noValue') }} /
                  {{ profile.typicalDiastolicBp || $t('patientDetails.noValue') }} {{ $t('patientDetails.bpUnit') }}
                </dd>
              </div>
              <div v-if="profile.typicalRestingPulse">
                <dt>{{ $t('patientDetails.pulseLabel') }}</dt>
                <dd>{{ profile.typicalRestingPulse }} {{ $t('patientDetails.pulseUnit') }}</dd>
              </div>
            </dl>
          </div>

          <!-- Lifestyle -->
          <div class="card">
            <h3>{{ $t('patientDetails.lifestyleTitle') }}</h3>
            <dl>
              <div>
                <dt>{{ $t('patientDetails.smokerLabel') }}</dt>
                <dd>{{ profile.smoker ? $t('patientDetails.smokerYes') : $t('patientDetails.smokerNo') }}</dd>
              </div>
              <div v-if="profile.alcoholFrequency && profile.alcoholFrequency !== 'Unknown'">
                <dt>{{ $t('patientDetails.alcoholLabel') }}</dt>
                <dd>{{ alcoholLabel(profile.alcoholFrequency) }}</dd>
              </div>
              <div v-if="profile.physicalActivity && profile.physicalActivity !== 'Unknown'">
                <dt>{{ $t('patientDetails.activityLabel') }}</dt>
                <dd>{{ activityLabel(profile.physicalActivity) }}</dd>
              </div>
              <div v-if="profile.dietType && profile.dietType !== 'Unknown'">
                <dt>{{ $t('patientDetails.dietLabel') }}</dt>
                <dd>{{ profile.dietType }}</dd>
              </div>
            </dl>
          </div>

          <!-- Medical history (full width) -->
          <div v-if="hasHistory" class="card wide">
            <h3>{{ $t('patientDetails.historyTitle') }}</h3>
            <div class="history-block">
              <div v-if="profile.chronicDiseases">
                <strong>{{ $t('patientDetails.chronicLabel') }}</strong>
                <p class="multi">{{ profile.chronicDiseases }}</p>
              </div>
              <div v-if="profile.allergies">
                <strong>{{ $t('patientDetails.allergiesLabel') }}</strong>
                <p class="multi">{{ profile.allergies }}</p>
              </div>
              <div v-if="profile.currentMedications">
                <strong>{{ $t('patientDetails.medicationsLabel') }}</strong>
                <p class="multi">{{ profile.currentMedications }}</p>
              </div>
              <div v-if="profile.familyHistory">
                <strong>{{ $t('patientDetails.familyLabel') }}</strong>
                <p class="multi">{{ profile.familyHistory }}</p>
              </div>
            </div>
          </div>

          <!-- Emergency contact -->
          <div v-if="hasEmergency" class="card">
            <h3>{{ $t('patientDetails.emergencyTitle') }}</h3>
            <dl>
              <div v-if="profile.emergencyContactName">
                <dt>{{ $t('patientDetails.emergencyName') }}</dt><dd>{{ profile.emergencyContactName }}</dd>
              </div>
              <div v-if="profile.emergencyContactPhone">
                <dt>{{ $t('patientDetails.emergencyPhone') }}</dt><dd>{{ profile.emergencyContactPhone }}</dd>
              </div>
              <div v-if="profile.emergencyContactRelation">
                <dt>{{ $t('patientDetails.emergencyRelation') }}</dt><dd>{{ profile.emergencyContactRelation }}</dd>
              </div>
            </dl>
          </div>
        </div>

        <div v-else class="empty-state small">
          <i class="fa-solid fa-folder-open"></i>
          <p>{{ $t('patientDetails.emptyMedicalCard') }}</p>
        </div>
      </section>

      <section class="analyses-block">
        <div class="block-head">
          <h2><i class="fa-solid fa-flask"></i> {{ $t('patientDetails.analysesTitle') }}</h2>
          <div class="filters">
            <button
              v-for="k in kinds"
              :key="k.id"
              :class="['tab', { active: filter === k.id }]"
              @click="filter = k.id"
            >
              {{ filterLabel(k.id) }}
            </button>
          </div>
        </div>

        <div v-if="loadingAnalyses" class="loader">{{ $t('patientDetails.loadingAnalyses') }}</div>

        <div v-else-if="filtered.length === 0" class="empty-state small">
          <i class="fa-solid fa-flask"></i>
          <p v-if="analyses.length === 0">{{ $t('patientDetails.emptyNoAnalyses') }}</p>
          <p v-else>{{ $t('patientDetails.emptyFilter') }}</p>
        </div>

        <div v-else class="analyses-grid">
          <router-link
            v-for="a in filtered"
            :key="a.id"
            :to="`/analyses/${a.id}`"
            class="analysis-card"
          >
            <div class="card-head">
              <span class="kind">{{ shortKind(a.type) }}</span>
              <SeverityBadge :severity="a.severityLabel || a.severity" />
            </div>
            <div class="card-body">
              <h3>{{ kindName(a.type) }}</h3>
              <p v-if="a.topFlag" class="flag">⚑ {{ a.topFlag }}</p>
              <p v-else-if="a.summaryUa" class="meta">{{ summaryShort(a.summaryUa) }}</p>
              <p v-else class="meta">{{ $t('patientDetails.defaultSummary') }}</p>
            </div>
            <div class="card-foot">
              <span><i class="fa-solid fa-clock"></i> {{ formatDate(a.createdAt) }}</span>
              <span v-if="a.hasDoctorReview || a.doctorReviewedAt" class="reviewed">
                <i class="fa-solid fa-user-doctor"></i> {{ $t('patientDetails.reviewed') }}
              </span>
            </div>
          </router-link>
        </div>
      </section>
    </template>
  </main>

  <FooterComponent />
</template>

<script>
import HeaderComponent from "@/components/nav-components/header/header-component.vue";
import NavbarComponent from "@/components/nav-components/navbar/navbar-component.vue";
import FooterComponent from "@/components/nav-components/footer/footer-component.vue";
import BottomNavbarComponent from "@/components/nav-components/bottom-navbar/bottom-navbar-component.vue";
import SeverityBadge from "@/components/analysis-components/common/SeverityBadge.vue";
import patientsApi from "@/api/patients";
import profileApi from "@/api/profile";
import analysesApi, { ANALYSIS_TYPE_NAME } from "@/api/analyses";

const KIND_SHORT = { Cbc: "CBC", Chem: "CHEM", Risk: "RISK", Neuro: "NEURO", Derma: "DERMA" };

export default {
  name: "PatientDetailsView",
  components: { HeaderComponent, NavbarComponent, FooterComponent, BottomNavbarComponent, SeverityBadge },
  data() {
    return {
      loading: true,
      loadingProfile: false,
      loadingAnalyses: false,
      patient: null,
      profile: null,
      profileError: null,
      analyses: [],
      filter: "all",
      kinds: [
        { id: "all"   },
        { id: "Cbc"   },
        { id: "Chem"  },
        { id: "Risk"  },
        { id: "Neuro" },
        { id: "Derma" },
      ],
    };
  },
  computed: {
    patientId() { return this.$route.params.patientId; },
    initials() {
      const n = this.patient?.patientName || "";
      const parts = n.split(" ").filter(Boolean);
      return ((parts[0]?.[0] || "") + (parts[1]?.[0] || "")).toUpperCase() || "?";
    },
    statusLabel() {
      const s = this.patient?.statusName || this.patient?.status;
      const map = {
        Pending:  this.$t('patients.card.statusPending'),
        Accepted: this.$t('patients.card.statusAccepted'),
        Rejected: this.$t('patients.card.statusRejected'),
        Declined: this.$t('patients.card.statusRejected'),
        Revoked:  this.$t('patients.card.statusRevoked'),
      };
      return map[s] || s;
    },
    statusClass() {
      const s = this.patient?.statusName || this.patient?.status;
      const map = {
        Accepted: "normal", Pending: "monitor",
        Rejected: "urgent", Declined: "urgent", Revoked: "urgent",
      };
      return map[s] || "info";
    },
    filtered() {
      if (this.filter === "all") return this.analyses;
      return this.analyses.filter((a) => a.type === this.filter);
    },
    hasVitals() {
      return this.profile && (
        this.profile.typicalSystolicBp || this.profile.typicalDiastolicBp ||
        this.profile.typicalRestingPulse
      );
    },
    hasHistory() {
      return this.profile && (
        this.profile.chronicDiseases || this.profile.allergies ||
        this.profile.currentMedications || this.profile.familyHistory
      );
    },
    hasEmergency() {
      return this.profile && (
        this.profile.emergencyContactName ||
        this.profile.emergencyContactPhone ||
        this.profile.emergencyContactRelation
      );
    },
  },
  async mounted() {
    await this.loadPatient();
    if (this.patient) {
      await Promise.all([this.loadAnalyses(), this.loadProfile()]);
    }
  },
  methods: {
    async loadPatient() {
      this.loading = true;
      try {
        const { data } = await patientsApi.myPatients();
        const list = data.items || data || [];
        this.patient = list.find((p) =>
          p.patientId === this.patientId || p.id === this.patientId
        ) || null;
      } catch {
        this.$store.dispatch("flash", {
          type: "error",
          message: this.$t('patientDetails.patientLoadError'),
        });
      } finally {
        this.loading = false;
      }
    },

    async loadProfile() {
      this.loadingProfile = true;
      this.profileError = null;
      try {
        const { data } = await profileApi.getByUserId(this.patientId);
        this.profile = data;
      } catch (e) {
        const status = e.response?.status;
        if (status === 403) {
          this.profileError = this.$t('patientDetails.noAccessMedical');
        } else if (status === 404) {
          this.profileError = this.$t('patientDetails.notFoundMedical');
        } else {
          this.profileError =
            e.response?.data?.detail || this.$t('patientDetails.errorLoadMedical');
        }
      } finally {
        this.loadingProfile = false;
      }
    },

    async loadAnalyses() {
      this.loadingAnalyses = true;
      try {
        const { data } = await analysesApi.list({ userId: this.patientId, pageSize: 100 });
        const items = data.items || data || [];
        this.analyses = items.map((a) => ({
          ...a,
          type: a.typeName || (typeof a.type === "number" ? ANALYSIS_TYPE_NAME[a.type] : a.type),
          severityLabel: a.severityName || a.severity,
        }));
      } catch (e) {
        this.$store.dispatch("flash", {
          type: "error",
          message: e.response?.data?.detail || this.$t('patientDetails.loadAnalysesError'),
        });
      } finally {
        this.loadingAnalyses = false;
      }
    },

    filterLabel(id) {
      const key = id === "all" ? "all" : id.toLowerCase();
      return this.$t(`analyses.filters.${key}`);
    },

    kindName(t) {
      const path = `analyses.kindNamesShort.${t}`;
      const v = this.$t(path);
      return v === path ? t : v;
    },

    shortKind(t) { return KIND_SHORT[t] || t; },

    formatDate(iso) {
      if (!iso) return this.$t('patientDetails.noValue');
      const lang = this.$locale === "en" ? "en-US" : "uk-UA";
      return new Date(iso).toLocaleDateString(lang, {
        day: "numeric", month: "short", year: "numeric",
      });
    },

    summaryShort(s) {
      if (!s) return "";
      return s.length > 80 ? s.slice(0, 80) + "…" : s;
    },

    ageWord(age) {
      if (this.$locale === "en") {
        return age === 1
          ? this.$t('patientDetails.ageYearEn')
          : this.$t('patientDetails.ageYearsEn');
      }
      // Ukrainian pluralization
      const n = age % 100;
      if (n >= 11 && n <= 14) return this.$t('patientDetails.ageYearMany');
      const last = age % 10;
      if (last === 1) return this.$t('patientDetails.ageYear1');
      if (last >= 2 && last <= 4) return this.$t('patientDetails.ageYear234');
      return this.$t('patientDetails.ageYearMany');
    },

    sexLabel(sex) {
      if (sex === "Male")   return this.$t('patientDetails.sexMale');
      if (sex === "Female") return this.$t('patientDetails.sexFemale');
      return this.$t('patientDetails.noValue');
    },

    alcoholLabel(v) {
      const path = `patientDetails.alcoholValues.${v}`;
      const out = this.$t(path);
      return out === path ? v : out;
    },

    activityLabel(v) {
      const path = `patientDetails.activityValues.${v}`;
      const out = this.$t(path);
      return out === path ? v : out;
    },

    fmtNumber(value, unit) {
      if (value == null) return this.$t('patientDetails.noValue');
      return `${value} ${unit}`;
    },
  },
};
</script>

<style scoped lang="scss">
.link-back {
  background: transparent;
  color: var(--purple);
  font-size: 1.3rem;
  cursor: pointer;
  margin-bottom: 1.5rem;
  font-family: inherit;
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  text-transform: none;
  &:hover { text-decoration: underline; }
}

.loader {
  text-align: center;
  padding: 4rem 2rem;
  color: var(--light-color);
  font-size: 1.4rem;
}

.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  color: var(--light-color);
  font-size: 1.4rem;
  display: flex; flex-direction: column; align-items: center; gap: 1rem;

  i { font-size: 4rem; color: var(--purple); }
  .muted { font-size: 1.2rem; }

  &.small { padding: 2.5rem 1.5rem; i { font-size: 2.8rem; } }
}

.patient-header {
  display: flex;
  gap: 2rem;
  background: white;
  border: var(--border);
  border-radius: 0.6rem;
  padding: 2rem;
  margin-bottom: 2rem;
  align-items: flex-start;

  .patient-avatar {
    width: 8rem; height: 8rem;
    border-radius: 50%;
    background: var(--purple);
    color: white;
    font-weight: 600;
    font-size: 2.4rem;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    overflow: hidden;
    img { width: 100%; height: 100%; object-fit: cover; display: block; }
  }

  .patient-info {
    flex: 1; min-width: 0;

    h1 {
      font-size: 2.4rem; color: var(--black); margin-bottom: 0.6rem;
      text-transform: none; font-weight: 600;
    }

    .meta {
      display: flex; flex-wrap: wrap; gap: 1.2rem;
      font-size: 1.2rem; color: var(--light-color);

      .status-pill {
        padding: 0.3rem 1rem; border-radius: 999px;
        font-size: 1.1rem; font-weight: 600; text-transform: uppercase;
        letter-spacing: 0.05em;

        &.normal  { background: rgba(46, 160, 67, 0.12);  color: #2ea043; }
        &.monitor { background: rgba(218, 165, 32, 0.12); color: #b88600; }
        &.urgent  { background: rgba(226, 75, 74, 0.12);  color: #a32d2d; }
        &.info    { background: rgba(65, 90, 119, 0.12);  color: var(--purple); }
      }

      .meta-item {
        display: inline-flex; align-items: center; gap: 0.4rem;
        text-transform: none;
        i { color: var(--purple); }
      }
    }

    .note {
      margin-top: 1rem;
      padding: 0.8rem 1.2rem;
      background: rgba(65, 90, 119, 0.04);
      border-left: 3px solid var(--purple);
      border-radius: 0.3rem;
      color: var(--black);
      font-size: 1.3rem;
      text-transform: none;
    }
  }
}

.medical-card-block,
.analyses-block {
  margin-bottom: 2.5rem;

  .block-head {
    display: flex; justify-content: space-between; align-items: center; gap: 1rem;
    margin-bottom: 1.2rem; flex-wrap: wrap;

    h2 {
      font-size: 1.8rem; color: var(--black); text-transform: none;
      font-weight: 600;
      i { color: var(--purple); margin-right: 0.5rem; }
    }
  }
}

.medical-card-block .card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(28rem, 1fr));
  gap: 1.5rem;

  .card {
    background: white;
    border: var(--border);
    border-radius: 0.6rem;
    padding: 1.6rem;

    &.wide { grid-column: 1 / -1; }

    h3 {
      font-size: 1.4rem;
      color: var(--purple);
      margin-bottom: 1rem;
      text-transform: lowercase;
      font-weight: 600;
      letter-spacing: 0.02em;
    }

    dl {
      margin: 0;
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 0.5rem 1rem;

      div { display: contents; }
      dt { font-size: 1.2rem; color: var(--light-color); text-transform: none; }
      dd { font-size: 1.3rem; color: var(--black); margin: 0; text-transform: none; }
    }

    .history-block {
      display: flex; flex-direction: column; gap: 1rem;

      strong {
        display: block;
        font-size: 1.2rem;
        color: var(--purple);
        text-transform: lowercase;
        margin-bottom: 0.3rem;
        font-weight: 600;
      }

      .multi {
        font-size: 1.3rem;
        color: var(--black);
        text-transform: none;
        white-space: pre-wrap;
        line-height: 1.5;
      }
    }
  }
}

.analyses-block .filters {
  display: flex; gap: 0.5rem; flex-wrap: wrap;

  .tab {
    background: transparent;
    border: 1px solid rgba(0,0,0,0.1);
    border-radius: 0.4rem;
    padding: 0.6rem 1.2rem;
    font-size: 1.2rem;
    color: var(--light-color);
    cursor: pointer;
    text-transform: lowercase;
    font-family: inherit;

    &.active { border-color: var(--purple); color: var(--purple); background: rgba(65, 90, 119, 0.04); }
    &:hover:not(.active) { color: var(--black); }
  }
}

.analyses-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(28rem, 1fr));
  gap: 1.5rem;

  .analysis-card {
    background: white;
    border: var(--border);
    border-radius: 0.6rem;
    padding: 1.4rem;
    text-decoration: none;
    color: inherit;
    transition: box-shadow 0.15s, transform 0.15s;

    &:hover { box-shadow: var(--box-shadow); transform: translateY(-2px); }

    .card-head {
      display: flex; justify-content: space-between; align-items: center;
      margin-bottom: 0.8rem;

      .kind {
        font-size: 1.1rem; font-weight: 700; color: var(--purple);
        letter-spacing: 0.1em;
      }
    }

    .card-body h3 {
      font-size: 1.5rem; color: var(--black); margin-bottom: 0.4rem;
      text-transform: none; font-weight: 600;
    }

    .card-body .flag { font-size: 1.3rem; color: #a32d2d; text-transform: none; }
    .card-body .meta { font-size: 1.2rem; color: var(--light-color); text-transform: none; }

    .card-foot {
      margin-top: 1rem;
      padding-top: 0.8rem;
      border-top: 1px solid rgba(0,0,0,0.05);
      display: flex; justify-content: space-between;
      font-size: 1.1rem; color: var(--light-color);
      text-transform: none;

      i { color: var(--purple); margin-right: 0.3rem; }
      .reviewed i { color: #2ea043; }
    }
  }
}

@media (max-width: 768px) {
  .patient-header { flex-direction: column; align-items: center; text-align: center; }
  .patient-header .patient-info .meta { justify-content: center; }
  .medical-card-block .card-grid { grid-template-columns: 1fr; }
}
</style>

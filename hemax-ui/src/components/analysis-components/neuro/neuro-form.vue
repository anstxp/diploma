<template>
  <form class="analysis-form" @submit.prevent="onSubmit">
    <div class="disclaimer">
      <i class="fa-solid fa-circle-info"></i>
      <p>
        {{ $t('analysis.neuro.disclaimerText') }}
        {{ $t('analysis.neuro.crisisHotline') }}
      </p>
    </div>

    <div class="section">
      <h3 class="section-title">
        <i class="fa-solid fa-clipboard-question"></i>
        {{ $t('analysis.neuro.questionnaireTitle') }}
        <small>{{ $t('analysis.neuro.questionnaireTimeframe') }}</small>
      </h3>
      <div class="scale">
        <span>{{ $t('analysis.neuro.scale0') }}</span>
        <span>{{ $t('analysis.neuro.scale1') }}</span>
        <span>{{ $t('analysis.neuro.scale2') }}</span>
        <span>{{ $t('analysis.neuro.scale3') }}</span>
      </div>

      <div class="questions">
        <div v-for="(q, i) in questions" :key="i" class="question">
          <div class="q-text">{{ questionText(q) }}</div>
          <div class="q-scale">
            <label v-for="v in [0, 1, 2, 3]" :key="v">
              <input
                type="radio"
                :name="`q${i}`"
                :value="v"
                v-model="answers[q.field]"
              />
              <span>{{ v }}</span>
            </label>
          </div>
        </div>
      </div>

      <div v-if="allAnswered" class="scores-preview">
        <div class="score-chip" :class="phq9Tier">
          <span class="score-label">{{ $t('analysis.neuro.phq9Label') }}</span>
          <span class="score-value">{{ phq9Score }}/27</span>
          <span class="score-tier">{{ phq9TierLabel }}</span>
        </div>
        <div class="score-chip" :class="gad7Tier">
          <span class="score-label">{{ $t('analysis.neuro.gad7Label') }}</span>
          <span class="score-value">{{ gad7Score }}/21</span>
          <span class="score-tier">{{ gad7TierLabel }}</span>
        </div>
      </div>
    </div>

    <div class="section">
      <h3 class="section-title">
        <i class="fa-solid fa-moon"></i>
        {{ $t('analysis.neuro.sleepTitle') }}
        <small>{{ $t('analysis.neuro.sleepOptional') }}</small>
      </h3>

      <div class="form-grid two-col">
        <div class="field">
          <label>{{ $t('analysis.neuro.sleepHoursAvg') }}</label>
          <div class="slider-wrap">
            <input
              type="range" min="0" max="12" step="0.5"
              v-model.number="sleep.sleep_hours_avg"
              class="slider"
            />
            <span class="slider-value">
              {{ sleep.sleep_hours_avg !== null
                  ? sleep.sleep_hours_avg + ' ' + $t('analysis.neuro.sleepHoursUnit')
                  : $t('analysis.neuro.sleepHoursEmpty') }}
            </span>
          </div>
        </div>

        <div class="field">
          <label>{{ $t('analysis.neuro.sleepLatencyMin') }}</label>
          <input
            v-model.number="sleep.sleep_latency_min"
            type="number" min="0" max="240"
            :placeholder="$t('analysis.neuro.egMinutes15')"
            class="box"
          />
        </div>

        <div class="field">
          <label>{{ $t('analysis.neuro.nightAwakenings') }}</label>
          <select v-model.number="sleep.night_awakenings" class="box">
            <option :value="null">{{ $t('analysis.neuro.chooseOption') }}</option>
            <option :value="0">{{ $t('analysis.neuro.awakenings0') }}</option>
            <option :value="1">1</option>
            <option :value="2">2</option>
            <option :value="3">3</option>
            <option :value="5">4-5</option>
            <option :value="8">{{ $t('analysis.neuro.awakeningsMore5') }}</option>
          </select>
        </div>

        <div class="field">
          <label>{{ $t('analysis.neuro.qualitySubjective') }}</label>
          <div class="rating">
            <label v-for="v in [1, 2, 3, 4, 5]" :key="v" class="star-label">
              <input type="radio" :value="v" v-model.number="sleep.sleep_quality_subjective" />
              <i class="fa-solid fa-star" :class="{ active: sleep.sleep_quality_subjective >= v }"></i>
            </label>
          </div>
        </div>
      </div>

      <div class="checkbox-grid">
        <label class="check">
          <input type="checkbox" v-model="sleep.early_morning_awakening" />
          <span>{{ $t('analysis.neuro.earlyMorningAwakening') }}</span>
        </label>
        <label class="check">
          <input type="checkbox" v-model="sleep.snoring" />
          <span>{{ $t('analysis.neuro.snoring') }}</span>
        </label>
        <label class="check warning-check">
          <input type="checkbox" v-model="sleep.witnessed_apnea" />
          <span>
            {{ $t('analysis.neuro.witnessedApnea') }}
            <small>{{ $t('analysis.neuro.witnessedApneaSubtle') }}</small>
          </span>
        </label>
        <label class="check">
          <input type="checkbox" v-model="sleep.shift_work" />
          <span>{{ $t('analysis.neuro.shiftWork') }}</span>
        </label>
        <label class="check">
          <input type="checkbox" v-model="sleep.uses_sleep_meds" />
          <span>{{ $t('analysis.neuro.usesSleepMeds') }}</span>
        </label>
      </div>

      <details class="advanced">
        <summary>{{ $t('analysis.neuro.sleepAdvancedToggle') }}</summary>
        <div class="form-grid two-col">
          <div class="field">
            <label>{{ $t('analysis.neuro.napsPerWeek') }}</label>
            <input
              v-model.number="sleep.naps_per_week"
              type="number" min="0" max="21"
              :placeholder="$t('analysis.neuro.egNumber2')"
              class="box"
            />
          </div>
          <div class="field">
            <label>{{ $t('analysis.neuro.screenTimeBeforeBed') }}</label>
            <input
              v-model.number="sleep.screen_time_before_bed_min"
              type="number" min="0" max="480"
              :placeholder="$t('analysis.neuro.egNumber30')"
              class="box"
            />
          </div>
          <div class="field">
            <label>{{ $t('analysis.neuro.caffeineServings') }}</label>
            <input
              v-model.number="sleep.caffeine_servings_per_day"
              type="number" min="0" max="20"
              :placeholder="$t('analysis.neuro.egNumber2')"
              class="box"
            />
          </div>
        </div>
      </details>
    </div>

    <div class="section">
      <h3 class="section-title">
        <i class="fa-solid fa-heart-pulse"></i>
        {{ $t('analysis.neuro.contextTitle') }}
      </h3>

      <div class="field">
        <label>{{ $t('analysis.neuro.exerciseMinutesPerWeek') }}</label>
        <input
          v-model.number="lifestyle.exercise_minutes_per_week"
          type="number" min="0" max="2000"
          :placeholder="$t('analysis.neuro.exerciseHint')"
          class="box"
        />
      </div>

      <div class="checkbox-grid">
        <label class="check">
          <input type="checkbox" v-model="lifestyle.recent_life_stressors" />
          <span>
            {{ $t('analysis.neuro.recentLifeStressors') }}
            <small>{{ $t('analysis.neuro.recentLifeStressorsSubtle') }}</small>
          </span>
        </label>
        <label class="check">
          <input type="checkbox" v-model="lifestyle.social_support_low" />
          <span>{{ $t('analysis.neuro.socialSupportLow') }}</span>
        </label>
        <label class="check">
          <input type="checkbox" v-model="lifestyle.chronic_pain" />
          <span>
            {{ $t('analysis.neuro.chronicPain') }}
            <small>{{ $t('analysis.neuro.chronicPainSubtle') }}</small>
          </span>
        </label>
      </div>
    </div>

    <div class="section">
      <h3 class="section-title">
        <i class="fa-solid fa-pills"></i>
        {{ $t('analysis.neuro.clinicalTitle') }}
        <small>{{ $t('analysis.neuro.clinicalOptional') }}</small>
      </h3>
      <p class="hint">{{ $t('analysis.neuro.clinicalHint') }}</p>

      <div class="checkbox-grid context-grid">
        <label class="check">
          <input type="checkbox" v-model="context.has_depression_history" />
          <span>{{ $t('analysis.neuro.hasDepressionHistory') }}</span>
        </label>
        <label class="check">
          <input type="checkbox" v-model="context.has_anxiety_history" />
          <span>{{ $t('analysis.neuro.hasAnxietyHistory') }}</span>
        </label>
        <label class="check">
          <input type="checkbox" v-model="context.has_hypothyroidism" />
          <span>{{ $t('analysis.neuro.hasHypothyroidism') }}</span>
        </label>
        <label class="check">
          <input type="checkbox" v-model="context.on_antidepressants" />
          <span>{{ $t('analysis.neuro.onAntidepressants') }}</span>
        </label>
        <label class="check">
          <input type="checkbox" v-model="context.on_anxiolytics" />
          <span>{{ $t('analysis.neuro.onAnxiolytics') }}</span>
        </label>
        <label class="check">
          <input type="checkbox" v-model="context.on_thyroid_meds" />
          <span>{{ $t('analysis.neuro.onThyroidMeds') }}</span>
        </label>
      </div>
    </div>

    <div class="form-meta">
      <div>
        <label>{{ $t('analysis.neuro.sexLabel') }}</label>
        <select v-model="form.sex" class="box">
          <option value="Male">{{ $t('analysis.neuro.sexMale') }}</option>
          <option value="Female">{{ $t('analysis.neuro.sexFemale') }}</option>
        </select>
      </div>
      <div>
        <label>{{ $t('analysis.neuro.ageLabel') }}</label>
        <input
          v-model.number="form.age"
          type="number" min="14" max="100"
          class="box"
        />
      </div>
    </div>

    <div class="merge-option">
      <label>
        <input type="checkbox" v-model="mergeRecentLabs" />
        <span>
          {{ $t('analysis.neuro.mergeLabsTitle') }}
          <small>{{ $t('analysis.neuro.mergeLabsHelp') }}</small>
        </span>
      </label>
    </div>

    <div class="actions">
      <button type="submit" class="btn" :disabled="loading || !allAnswered">
        {{ loading ? $t('analysis.neuro.submittingButton') : $t('analysis.neuro.submitButton') }}
      </button>
      <p v-if="!allAnswered" class="warning">
        {{ $t('analysis.neuro.warningAllRequired') }}
      </p>
    </div>
  </form>
</template>

<script>
import profilePrefillMixin from "@/mixins/profilePrefill.js";

function snakeToCamel(s) {
  return s.replace(/_([a-z])/g, (_, c) => c.toUpperCase());
}

export default {
  mixins: [profilePrefillMixin],
  name: "NeuroForm",
  props: {
    initialAge: { type: Number, default: 30 },
    initialSex: { type: String, default: "Unknown" },
  },
  emits: ["submitted"],
  data() {
    return {
      loading: false,
      mergeRecentLabs: true,
      form: {
        age: this.initialAge,
        sex: this.initialSex !== "Unknown" ? this.initialSex : "Female",
      },
      answers: {},

      sleep: {
        sleep_hours_avg: null,
        sleep_latency_min: null,
        night_awakenings: null,
        sleep_quality_subjective: null,
        early_morning_awakening: false,
        uses_sleep_meds: false,
        naps_per_week: null,
        screen_time_before_bed_min: null,
        caffeine_servings_per_day: null,
        shift_work: false,
        snoring: false,
        witnessed_apnea: false,
      },

      lifestyle: {
        exercise_minutes_per_week: null,
        recent_life_stressors: false,
        social_support_low: false,
        chronic_pain: false,
      },

      context: {
        has_depression_history: false,
        has_anxiety_history: false,
        has_hypothyroidism: false,
        on_antidepressants: false,
        on_anxiolytics: false,
        on_thyroid_meds: false,
      },

      questions: [
        { field: "phq_anhedonia" },
        { field: "phq_mood" },
        { field: "phq_sleep" },
        { field: "phq_energy" },
        { field: "phq_appetite" },
        { field: "phq_self" },
        { field: "phq_concentration" },
        { field: "phq_motor" },
        { field: "phq_si" },
        { field: "gad_nervousness" },
        { field: "gad_worry" },
        { field: "gad_relax" },
        { field: "gad_irritable" },
        { field: "isi_quality" },
      ],
    };
  },
  computed: {
    allAnswered() {
      return this.questions.every((q) => this.answers[q.field] !== undefined);
    },

    phq9Score() {
      const phqFields = this.questions.filter(q => q.field.startsWith("phq_"));
      let total = 0;
      for (const q of phqFields) {
        const v = this.answers[q.field];
        if (typeof v === "number") total += v;
      }
      return total;
    },

    gad7Score() {
      const gadFields = this.questions.filter(q => q.field.startsWith("gad_"));
      let total = 0;
      for (const q of gadFields) {
        const v = this.answers[q.field];
        if (typeof v === "number") total += v;
      }
      return Math.round(total * 1.75);
    },

    phq9Tier() {
      const s = this.phq9Score;
      if (s >= 20) return "severe";
      if (s >= 15) return "moderate-severe";
      if (s >= 10) return "moderate";
      if (s >= 5)  return "mild";
      return "minimal";
    },
    phq9TierLabel() {
      return this.$t(`analysis.neuro.phq9Tier.${this.phq9Tier}`);
    },

    gad7Tier() {
      const s = this.gad7Score;
      if (s >= 15) return "severe";
      if (s >= 10) return "moderate";
      if (s >= 5)  return "mild";
      return "minimal";
    },
    gad7TierLabel() {
      return this.$t(`analysis.neuro.gad7Tier.${this.gad7Tier}`);
    },
  },

  methods: {
    questionText(q) {
      return this.$t(`analysis.neuro.questions.${snakeToCamel(q.field)}`);
    },

    _pruneEmpty(obj) {
      const out = {};
      for (const [k, v] of Object.entries(obj)) {
        if (v === null || v === undefined || v === "") continue;
        out[k] = v;
      }
      return out;
    },

    async onSubmit() {
      if (!this.allAnswered) return;
      this.loading = true;
      try {
        const payload = {
          ...this.form,
          ...this.answers,
          phq9_score: this.phq9Score,
          gad7_score: this.gad7Score,
          ...this._pruneEmpty(this.sleep),
          ...this._pruneEmpty(this.lifestyle),
        };

        const contextFlags = {};
        for (const [k, v] of Object.entries(this.context)) {
          if (v === true) contextFlags[k] = true;
        }
        if (Object.keys(contextFlags).length > 0) {
          payload.context = contextFlags;
        }

        const result = await this.$store.dispatch("analyses/submit", {
          kind: "neuro",
          payload,
          mergeRecentLabs: this.mergeRecentLabs,
          language: this.$locale,
        });
        this.$emit("submitted", result);
      } catch (e) {
        this.$store.dispatch("flash", {
          type: "error",
          message: e.response?.data?.detail || this.$t('analysis.neuro.errorSubmit'),
        });
      } finally {
        this.loading = false;
      }
    },
  },
};
</script>

<style scoped lang="scss">
.analysis-form {
  background: white;
  border: var(--border);
  border-radius: 0.6rem;
  padding: 2rem;
}

.disclaimer {
  display: flex;
  gap: 1rem;
  padding: 1.4rem;
  border-radius: 0.5rem;
  background: rgba(65, 90, 119, 0.06);
  border-left: 0.4rem solid var(--purple);
  margin-bottom: 2rem;

  i { color: var(--purple); font-size: 1.8rem; flex-shrink: 0; }

  p {
    font-size: 1.3rem;
    color: var(--black);
    line-height: 1.7;
    text-transform: none;
    margin: 0;
  }
}

.section {
  margin: 2.4rem 0;
  padding-top: 2rem;
  border-top: 1px solid rgba(0, 0, 0, 0.06);

  &:first-of-type { margin-top: 0; padding-top: 0; border-top: none; }
}

.section-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--black);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin: 0 0 1.4rem;
  display: flex;
  align-items: center;
  gap: 0.8rem;

  i { color: var(--purple); font-size: 1.6rem; }

  small {
    text-transform: none;
    font-size: 1.2rem;
    color: var(--light-color);
    letter-spacing: normal;
    font-weight: 400;
    margin-left: 0.5rem;
  }
}

.scale {
  display: flex;
  gap: 1.5rem;
  flex-wrap: wrap;
  font-size: 1.2rem;
  color: var(--light-color);
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: var(--bg);
  border-radius: 0.4rem;
}

.questions { margin-bottom: 1.6rem; }

.question {
  padding: 1.2rem 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  display: grid;
  grid-template-columns: 1fr 22rem;
  align-items: center;
  gap: 1.5rem;
}

.q-text {
  font-size: 1.4rem;
  color: var(--black);
  text-transform: none;
  line-height: 1.5;
}

.q-scale {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;

  label {
    cursor: pointer;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.3rem;

    input[type="radio"] {
      accent-color: var(--purple);
      width: 1.6rem;
      height: 1.6rem;
      cursor: pointer;
    }

    span { font-size: 1.2rem; color: var(--light-color); }
  }
}

.scores-preview {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
  padding: 1.2rem;
  background: var(--bg);
  border-radius: 0.5rem;
  margin-top: 1rem;
}

.score-chip {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.6rem 1rem;
  border-radius: 0.4rem;
  font-size: 1.3rem;
  background: white;
  border-left: 0.4rem solid var(--light-color);

  &.minimal        { border-left-color: #10b981; }
  &.mild           { border-left-color: #84cc16; }
  &.moderate       { border-left-color: #f59e0b; }
  &.moderate-severe{ border-left-color: #f97316; }
  &.severe         { border-left-color: #dc2626; }

  .score-label {
    font-weight: 700;
    text-transform: uppercase;
    color: var(--black);
    font-size: 1.15rem;
  }

  .score-value {
    color: var(--purple);
    font-variant-numeric: tabular-nums;
    font-weight: 600;
  }

  .score-tier { color: var(--light-color); font-size: 1.2rem; }
}

.form-grid {
  display: grid;
  gap: 1.2rem;
  &.two-col { grid-template-columns: 1fr 1fr; }
}

.field {
  display: flex;
  flex-direction: column;

  label {
    font-size: 1.25rem;
    margin-bottom: 0.5rem;
    color: var(--black);
    text-transform: lowercase;
  }
}

.box {
  width: 100%;
  padding: 0.7rem 1rem;
  font-size: 1.4rem;
  border: var(--border);
  border-radius: 0.4rem;
  background: white;
}

.slider-wrap { display: flex; align-items: center; gap: 1rem; }
.slider { flex: 1; accent-color: var(--purple); cursor: pointer; }
.slider-value {
  min-width: 6rem;
  text-align: right;
  font-variant-numeric: tabular-nums;
  font-weight: 600;
  color: var(--purple);
  font-size: 1.4rem;
}

.rating { display: flex; gap: 0.5rem; }

.star-label {
  cursor: pointer;
  input { display: none; }
  i {
    font-size: 1.8rem;
    color: rgba(0, 0, 0, 0.15);
    transition: color 0.15s;
    &.active { color: #f59e0b; }
  }
  &:hover i { color: #fbbf24; }
}

.checkbox-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.8rem;
  margin-top: 1rem;
}

.check {
  display: flex;
  gap: 0.8rem;
  align-items: flex-start;
  padding: 0.9rem 1.2rem;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 0.4rem;
  cursor: pointer;
  font-size: 1.3rem;
  color: var(--black);
  text-transform: none;
  line-height: 1.5;
  transition: background 0.15s, border-color 0.15s;

  &:hover { background: rgba(65, 90, 119, 0.04); border-color: rgba(65, 90, 119, 0.2); }
  &.warning-check { border-left: 0.4rem solid #f59e0b; }

  input[type="checkbox"] {
    margin-top: 0.2rem;
    flex-shrink: 0;
    width: 1.6rem;
    height: 1.6rem;
    accent-color: var(--purple);
    cursor: pointer;
  }

  small {
    display: block;
    color: var(--light-color);
    font-size: 1.15rem;
    margin-top: 0.2rem;
  }
}

.context-grid { grid-template-columns: 1fr 1fr 1fr; }

.advanced {
  margin-top: 1.4rem;
  padding: 1rem 1.2rem;
  background: rgba(65, 90, 119, 0.04);
  border-radius: 0.4rem;

  summary {
    cursor: pointer;
    font-size: 1.3rem;
    color: var(--purple);
    font-weight: 600;
    user-select: none;
    &::marker { color: var(--purple); }
  }
  .form-grid { margin-top: 1rem; }
}

.hint {
  font-size: 1.25rem;
  color: var(--light-color);
  text-transform: none;
  line-height: 1.6;
  margin: 0 0 1rem;
}

.form-meta {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  padding-top: 2rem;
  margin-top: 2rem;
  border-top: var(--border);

  label {
    display: block;
    font-size: 1.3rem;
    margin-bottom: 0.4rem;
    text-transform: lowercase;
    color: var(--black);
  }
}

.actions {
  margin-top: 2rem;
  text-align: center;

  .warning {
    margin-top: 0.6rem;
    color: #854F0B;
    font-size: 1.2rem;
    text-transform: none;
  }
}

.merge-option {
  margin: 1.5rem 0 0;
  padding: 1.2rem 1.4rem;
  background: rgba(65, 90, 119, 0.05);
  border: 1px solid rgba(65, 90, 119, 0.15);
  border-radius: 0.5rem;

  label {
    display: flex;
    gap: 0.8rem;
    align-items: flex-start;
    cursor: pointer;

    input[type="checkbox"] {
      margin-top: 0.3rem;
      flex-shrink: 0;
      width: 1.6rem;
      height: 1.6rem;
      accent-color: var(--purple);
      cursor: pointer;
    }

    span {
      font-size: 1.3rem;
      color: var(--black);
      text-transform: none;
      line-height: 1.5;

      small {
        display: block;
        font-size: 1.15rem;
        color: var(--light-color);
        margin-top: 0.3rem;
        line-height: 1.4;
      }
    }
  }
}

@media (max-width: 768px) {
  .question {
    grid-template-columns: 1fr;
    gap: 0.6rem;
    .q-scale { justify-content: flex-start; }
  }
  .form-grid.two-col,
  .checkbox-grid,
  .context-grid,
  .form-meta { grid-template-columns: 1fr; }
}
</style>

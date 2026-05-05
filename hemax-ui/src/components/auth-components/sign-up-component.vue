<template>
  <div class="login-form-container">
    <form @submit.prevent="onSubmit">
      <h3>{{ $t('auth.signUp.title') }}</h3>

      <!-- Progress indicator -->
      <div class="step-indicator">
        <div class="step" :class="{ active: step === 1, done: step > 1 }">
          <span>1</span> {{ $t('auth.signUp.step1Title') }}
        </div>
        <div class="step-line"></div>
        <div class="step" :class="{ active: step === 2 }">
          <span>2</span> {{ $t('auth.signUp.step2Title') }}
        </div>
      </div>

      <div v-show="step === 1">
        <div class="form-row two-cols">
          <div>
            <span>{{ $t('auth.common.firstNameLabel') }}</span>
            <input
              v-model="form.firstName"
              type="text"
              class="box"
              maxlength="80"
              autocomplete="given-name"
              required
            />
            <small v-if="firstNameError" class="error-message">{{ firstNameError }}</small>
          </div>
          <div>
            <span>{{ $t('auth.common.lastNameLabel') }}</span>
            <input
              v-model="form.lastName"
              type="text"
              class="box"
              maxlength="80"
              autocomplete="family-name"
              required
            />
            <small v-if="lastNameError" class="error-message">{{ lastNameError }}</small>
          </div>
        </div>

        <div class="form-row">
          <span>{{ $t('auth.common.emailLabel') }}</span>
          <input v-model="form.email" type="email" class="box" required />
          <small v-if="emailError" class="error-message">{{ emailError }}</small>
        </div>

        <div class="form-row two-cols">
          <div>
            <span>{{ $t('auth.common.dateOfBirthLabel') }} <em class="req">*</em></span>
            <input
              v-model="form.dateOfBirth"
              type="date"
              class="box"
              :min="minDob"
              :max="maxDob"
              required
            />
            <small v-if="dobError" class="error-message">{{ dobError }}</small>
          </div>
          <div>
            <span>{{ $t('auth.common.sexLabel') }} <em class="req">*</em></span>
            <select v-model="form.sex" class="box" required>
              <option value="" disabled>{{ $t('auth.signUp.chooseDefault') }}</option>
              <option value="Male">{{ $t('auth.common.sexMale') }}</option>
              <option value="Female">{{ $t('auth.common.sexFemale') }}</option>
            </select>
          </div>
        </div>

        <div class="form-row">
          <span>{{ $t('auth.common.passwordLabel') }}</span>
          <input v-model="form.password" type="password" class="box" required />
          <small v-if="passwordError" class="error-message">{{ passwordError }}</small>
          <small v-else class="hint">{{ $t('auth.signUp.passwordHint') }}</small>
        </div>

        <div class="form-row">
          <span>{{ $t('auth.common.passwordConfirmLabel') }}</span>
          <input v-model="confirmPassword" type="password" class="box" required />
          <div v-if="passwordMismatch" class="error-message">
            {{ $t('auth.signUp.passwordMismatch') }}
          </div>
        </div>

        <button
          type="button"
          class="btn"
          :disabled="!step1Valid"
          @click="goToStep(2)"
        >
          {{ $t('common.next') }}
        </button>

        <p>
          {{ $t('auth.signUp.alreadyHaveAccount') }}
          <router-link to="/sign-in">{{ $t('auth.signUp.signInLink') }}</router-link>
        </p>
      </div>

      <div v-show="step === 2">
        <p class="step-intro">{{ $t('auth.signUp.step2Intro') }}</p>

        <div class="form-row two-cols">
          <div>
            <span>{{ $t('auth.signUp.phoneLabel') }} <em class="req">*</em></span>
            <input
              v-model="form.phone"
              type="tel"
              class="box"
              :placeholder="$t('auth.signUp.egPhone')"
              required
            />
            <small v-if="phoneError" class="error-message">{{ phoneError }}</small>
          </div>
          <div>
            <span>{{ $t('auth.signUp.middleNameLabel') }}</span>
            <input v-model="form.middleName" type="text" class="box" maxlength="80" />
            <small v-if="middleNameError" class="error-message">{{ middleNameError }}</small>
          </div>
        </div>

        <div class="form-row three-cols">
          <div>
            <span>{{ $t('auth.signUp.heightLabel') }}</span>
            <input v-model.number="form.heightCm" type="number" min="50" max="250" class="box" />
          </div>
          <div>
            <span>{{ $t('auth.signUp.weightLabel') }}</span>
            <input v-model.number="form.weightKg" type="number" min="20" max="300" step="0.1" class="box" />
          </div>
          <div>
            <span>{{ $t('auth.signUp.waistLabel') }} <small>({{ $t('common.optional') }})</small></span>
            <input v-model.number="form.waistCm" type="number" min="30" max="250" class="box" />
          </div>
        </div>

        <div class="form-row three-cols">
          <div>
            <span>{{ $t('auth.signUp.sbpLabel') }} <small>({{ $t('common.optional') }})</small></span>
            <input v-model.number="form.typicalSystolicBp" type="number" min="60" max="250" class="box" :placeholder="$t('auth.signUp.sbpEg')" />
          </div>
          <div>
            <span>{{ $t('auth.signUp.dbpLabel') }} <small>({{ $t('common.optional') }})</small></span>
            <input v-model.number="form.typicalDiastolicBp" type="number" min="30" max="150" class="box" :placeholder="$t('auth.signUp.dbpEg')" />
          </div>
          <div>
            <span>{{ $t('auth.signUp.pulseLabel') }} <small>({{ $t('common.optional') }})</small></span>
            <input v-model.number="form.typicalRestingPulse" type="number" min="30" max="200" class="box" :placeholder="$t('auth.signUp.pulseEg')" />
          </div>
        </div>

        <div class="form-row">
          <span>{{ $t('auth.signUp.lifestyleLabel') }}</span>
          <div class="lifestyle-grid">
            <label>
              <input type="checkbox" v-model="form.smoker" />
              {{ $t('auth.signUp.smokerCheckbox') }}
            </label>
            <select v-model="form.alcoholFrequency" class="box small">
              <option value="Unknown">{{ $t('auth.signUp.alcoholChoose') }}</option>
              <option value="Never">{{ $t('auth.signUp.alcoholNever') }}</option>
              <option value="Occasional">{{ $t('auth.signUp.alcoholOccasional') }}</option>
              <option value="Regular">{{ $t('auth.signUp.alcoholRegular') }}</option>
              <option value="Heavy">{{ $t('auth.signUp.alcoholHeavy') }}</option>
            </select>
            <select v-model="form.physicalActivity" class="box small">
              <option value="Unknown">{{ $t('auth.signUp.activityChoose') }}</option>
              <option value="Sedentary">{{ $t('auth.signUp.activitySedentary') }}</option>
              <option value="Light">{{ $t('auth.signUp.activityLight') }}</option>
              <option value="Moderate">{{ $t('auth.signUp.activityModerate') }}</option>
              <option value="Active">{{ $t('auth.signUp.activityActive') }}</option>
            </select>
            <select v-model="form.dietType" class="box small">
              <option value="Unknown">{{ $t('auth.signUp.dietChoose') }}</option>
              <option value="Omnivore">{{ $t('auth.signUp.dietOmnivore') }}</option>
              <option value="Vegetarian">{{ $t('auth.signUp.dietVegetarian') }}</option>
              <option value="Vegan">{{ $t('auth.signUp.dietVegan') }}</option>
              <option value="Keto">{{ $t('auth.signUp.dietKeto') }}</option>
              <option value="Other">{{ $t('auth.signUp.dietOther') }}</option>
            </select>
          </div>
        </div>

        <div class="form-row">
          <span>{{ $t('auth.signUp.chronicLabel') }}</span>
          <textarea
            v-model="form.chronicDiseases"
            class="box"
            rows="2"
            :placeholder="$t('auth.signUp.chronicPlaceholder')"
          ></textarea>
        </div>

        <div class="form-row">
          <span>{{ $t('auth.signUp.allergiesLabel') }}</span>
          <textarea
            v-model="form.allergies"
            class="box"
            rows="2"
            :placeholder="$t('auth.signUp.allergiesPlaceholder')"
          ></textarea>
        </div>

        <div class="form-row">
          <span>{{ $t('auth.signUp.medicationsLabel') }}</span>
          <textarea
            v-model="form.currentMedications"
            class="box"
            rows="2"
            :placeholder="$t('auth.signUp.medicationsPlaceholder')"
          ></textarea>
        </div>

        <div class="form-row">
          <span>{{ $t('auth.signUp.familyHistoryLabel') }}</span>
          <textarea
            v-model="form.familyHistory"
            class="box"
            rows="2"
            :placeholder="$t('auth.signUp.familyHistoryPlaceholder')"
          ></textarea>
        </div>

        <details class="emergency-block">
          <summary>{{ $t('auth.signUp.emergencyTitle') }}</summary>
          <div class="form-row">
            <input v-model="form.emergencyContactName" :placeholder="$t('auth.signUp.emergencyNamePlaceholder')" class="box" />
          </div>
          <div class="form-row two-cols">
            <input v-model="form.emergencyContactPhone" type="tel" :placeholder="$t('auth.signUp.emergencyPhonePlaceholder')" class="box" />
            <input v-model="form.emergencyContactRelation" :placeholder="$t('auth.signUp.emergencyRelationPlaceholder')" class="box" />
          </div>
        </details>

        <div class="step-actions">
          <button type="button" class="btn-outline" @click="goToStep(1)">
            <i class="fa-solid fa-arrow-left"></i> {{ $t('common.back') }}
          </button>
          <button type="submit" class="btn" :disabled="loading || !step2Valid">
            {{ loading ? $t('auth.signUp.submitting') : $t('auth.signUp.submitButton') }}
          </button>
        </div>
      </div>
    </form>
  </div>
</template>

<script>
import {
  validateEmail,
  validatePhone,
  validatePassword,
  validateName,
  validateDateOfBirth,
  extractApiError,
} from "@/utils/validation";

export default {
  name: "SignUpComponent",
  data() {
    return {
      step: 1,
      loading: false,
      form: {
        // step 1
        firstName: "",
        lastName: "",
        email: "",
        password: "",
        dateOfBirth: "",
        sex: "",
        // step 2
        phone: "",
        middleName: "",
        heightCm: null,
        weightKg: null,
        waistCm: null,
        typicalSystolicBp: null,
        typicalDiastolicBp: null,
        typicalRestingPulse: null,
        smoker: false,
        alcoholFrequency: "Unknown",
        physicalActivity: "Unknown",
        dietType: "Unknown",
        chronicDiseases: "",
        allergies: "",
        currentMedications: "",
        familyHistory: "",
        emergencyContactName: "",
        emergencyContactPhone: "",
        emergencyContactRelation: "",
      },
      confirmPassword: "",
      fieldError: {
        firstName: null,
        lastName: null,
        email: null,
        phone: null,
        password: null,
        dateOfBirth: null,
      },
    };
  },
  computed: {
    today() { return new Date().toISOString().slice(0, 10); },
    maxDob() {
      const d = new Date();
      d.setFullYear(d.getFullYear() - 13);
      return d.toISOString().slice(0, 10);
    },
    minDob() {
      const d = new Date();
      d.setFullYear(d.getFullYear() - 130);
      return d.toISOString().slice(0, 10);
    },
    passwordMismatch() {
      return this.confirmPassword.length > 0 && this.form.password !== this.confirmPassword;
    },
    firstNameError() {
      return this.fieldError.firstName
        || (this.form.firstName ? validateName(this.form.firstName, { label: this.$t('auth.signUp.validationFirstNameLabel'), max: 80 }) : null);
    },
    lastNameError() {
      return this.fieldError.lastName
        || (this.form.lastName ? validateName(this.form.lastName, { label: this.$t('auth.signUp.validationLastNameLabel'), max: 80 }) : null);
    },
    middleNameError() {
      return this.form.middleName
        ? validateName(this.form.middleName, { label: this.$t('auth.signUp.validationMiddleNameLabel'), required: false, max: 80 })
        : null;
    },
    emailError() {
      return this.fieldError.email
        || (this.form.email ? validateEmail(this.form.email) : null);
    },
    passwordError() {
      return this.fieldError.password
        || (this.form.password ? validatePassword(this.form.password) : null);
    },
    phoneError() {
      return this.fieldError.phone
        || (this.form.phone ? validatePhone(this.form.phone) : null);
    },
    dobError() {
      return this.fieldError.dateOfBirth
        || (this.form.dateOfBirth ? validateDateOfBirth(this.form.dateOfBirth, { minAge: 13 }) : null);
    },
    step1Valid() {
      return (
        validateName(this.form.firstName, { label: this.$t('auth.signUp.validationFirstNameLabel') }) === null &&
        validateName(this.form.lastName, { label: this.$t('auth.signUp.validationLastNameLabel') }) === null &&
        validateEmail(this.form.email) === null &&
        validatePassword(this.form.password) === null &&
        validateDateOfBirth(this.form.dateOfBirth, { minAge: 13 }) === null &&
        (this.form.sex === "Male" || this.form.sex === "Female") &&
        !this.passwordMismatch
      );
    },
    step2Valid() {
      return validatePhone(this.form.phone) === null
        && (this.middleNameError == null);
    },
  },
  methods: {
    goToStep(n) {
      if (n === 2 && !this.step1Valid) return;
      this.step = n;
      window.scrollTo({ top: 0, behavior: "smooth" });
    },
    nullIfBlank(s) {
      return s && s.trim() ? s.trim() : null;
    },
    clearFieldErrors() {
      this.fieldError.firstName = null;
      this.fieldError.lastName = null;
      this.fieldError.email = null;
      this.fieldError.phone = null;
      this.fieldError.password = null;
      this.fieldError.dateOfBirth = null;
    },
    async onSubmit() {
      this.clearFieldErrors();
      if (!this.step1Valid) { this.step = 1; return; }
      if (!this.step2Valid) {
        this.fieldError.phone = validatePhone(this.form.phone);
        return;
      }

      this.loading = true;
      try {
        await this.$store.dispatch("auth/register", {
          firstName: this.form.firstName.trim(),
          lastName:  this.form.lastName.trim(),
          email:     this.form.email.trim(),
          password:  this.form.password,
          dateOfBirth: this.form.dateOfBirth,
          sex: this.form.sex,
          phone: this.form.phone.trim(),
          middleName:        this.nullIfBlank(this.form.middleName),
          heightCm:          this.form.heightCm || null,
          weightKg:          this.form.weightKg || null,
          waistCm:           this.form.waistCm || null,
          typicalSystolicBp: this.form.typicalSystolicBp || null,
          typicalDiastolicBp: this.form.typicalDiastolicBp || null,
          typicalRestingPulse: this.form.typicalRestingPulse || null,
          smoker:            this.form.smoker,
          alcoholFrequency:  this.form.alcoholFrequency === "Unknown" ? null : this.form.alcoholFrequency,
          physicalActivity:  this.form.physicalActivity === "Unknown" ? null : this.form.physicalActivity,
          dietType:          this.form.dietType === "Unknown" ? null : this.form.dietType,
          chronicDiseases:    this.nullIfBlank(this.form.chronicDiseases),
          allergies:          this.nullIfBlank(this.form.allergies),
          currentMedications: this.nullIfBlank(this.form.currentMedications),
          familyHistory:      this.nullIfBlank(this.form.familyHistory),
          emergencyContactName:     this.nullIfBlank(this.form.emergencyContactName),
          emergencyContactPhone:    this.nullIfBlank(this.form.emergencyContactPhone),
          emergencyContactRelation: this.nullIfBlank(this.form.emergencyContactRelation),
        });

        try {
          await this.$store.dispatch("auth/login", {
            email: this.form.email.trim(),
            password: this.form.password,
          });
          this.$router.push("/");
        } catch {
          this.$router.push("/sign-in");
        }
      } catch (err) {
        const code = err?.response?.data?.code;
        const msg  = extractApiError(err, this.$t('auth.signUp.errorGeneric'));

        if (code === "PHONE_TAKEN") {
          this.fieldError.phone = this.$t('auth.signUp.errorPhoneTaken');
          this.step = 2;
        } else if (
          /already taken|already in use|вже використовується|DuplicateUser|DuplicateEmail/i.test(msg)
        ) {
          this.fieldError.email = this.$t('auth.signUp.errorEmailTaken');
          this.step = 1;
        } else {
          this.$store.dispatch("flash", { type: "error", message: msg });
        }
      } finally {
        this.loading = false;
      }
    },
  },
};
</script>

<style scoped lang="scss">
@import "auth-style";

.step-indicator {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin: 1rem 0 1.5rem;

  .step {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    color: var(--light-color);
    font-size: 1.2rem;
    text-transform: lowercase;

    span {
      width: 2.4rem; height: 2.4rem;
      border-radius: 50%;
      background: rgba(0,0,0,0.08);
      color: var(--light-color);
      display: flex; align-items: center; justify-content: center;
      font-weight: 600;
    }

    &.active span { background: var(--purple); color: white; }
    &.active { color: var(--black); font-weight: 500; }
    &.done span { background: rgba(65, 90, 119, 0.2); color: var(--purple); }
  }

  .step-line {
    flex: 1; height: 2px; background: rgba(0,0,0,0.08); min-width: 1.5rem;
  }
}

.step-intro {
  font-size: 1.2rem;
  color: var(--light-color);
  text-transform: none;
  margin-bottom: 1rem;
  line-height: 1.4;
}

.form-row.two-cols {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.form-row.three-cols {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 0.75rem;
}

.req {
  color: #c0392b;
  font-style: normal;
  font-weight: 700;
  margin-left: 0.2rem;
}

.hint, .error-message {
  display: block;
  font-size: 1.1rem;
  margin-top: 0.4rem;
  text-transform: none;
}

.hint { color: var(--light-color); }
.error-message { color: #a32d2d; }

.lifestyle-grid {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;

  label {
    display: flex; align-items: center; gap: 0.5rem;
    font-size: 1.3rem; text-transform: none;
    cursor: pointer;
    input[type="checkbox"] {
      width: 1.6rem; height: 1.6rem; accent-color: var(--purple);
    }
  }

  .box.small { padding: 0.6rem 1rem; font-size: 1.3rem; }
}

textarea.box { resize: vertical; }

.emergency-block {
  margin: 1rem 0;
  border: 1px solid rgba(0,0,0,0.06);
  border-radius: 0.4rem;
  padding: 0.6rem 1rem;

  summary {
    cursor: pointer;
    font-size: 1.2rem;
    color: var(--purple);
    text-transform: lowercase;
  }
  .form-row { margin-top: 0.8rem; }
}

.step-actions {
  display: flex;
  gap: 1rem;
  margin-top: 1rem;

  .btn-outline {
    background: transparent;
    border: 1px solid var(--purple);
    color: var(--purple);
    cursor: pointer;
    padding: 0.8rem 1.6rem;
    border-radius: 0.4rem;
    font-family: inherit;
    text-transform: lowercase;

    &:hover { background: rgba(65, 90, 119, 0.06); }
  }

  .btn { flex: 1; }
}

@media (max-width: 600px) {
  .form-row.two-cols,
  .form-row.three-cols { grid-template-columns: 1fr; }
}
</style>

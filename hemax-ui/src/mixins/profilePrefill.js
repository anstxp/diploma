export default {
  computed: {
    _profile() {
      return this.$store.state.profile?.profile;
    },
  },

  watch: {
    _profile: {
      immediate: true,
      handler(p) {
        if (!p || !this.form) return;
        this._maybeFill('age', p.age);
        this._maybeFill('sex', this._sexAsString(p.sex));

        // Anthropometrics — for Risk/Neuro forms
        this._maybeFill('height_cm', p.heightCm);
        this._maybeFill('weight_kg', p.weightKg);
        this._maybeFill('waist_cm', p.waistCm);
        this._maybeFill('systolic_bp', p.typicalSystolicBp);
        this._maybeFill('diastolic_bp', p.typicalDiastolicBp);
        this._maybeFill('heart_rate', p.typicalRestingPulse);

        // Lifestyle flags (Risk form has these)
        if (this.form.smoker === false && p.smoker) this.form.smoker = true;
        if (this.form.physical_activity_low === false &&
            p.physicalActivity === 1) this.form.physical_activity_low = true;
        if (this.form.alcohol_regular === false &&
            (p.alcoholFrequency === 3 || p.alcoholFrequency === 4)) {
          this.form.alcohol_regular = true;
        }
      },
    },
  },

  async mounted() {
    if (!this._profile) {
      this.$store.dispatch('profile/fetch').catch(() => {});
    }
  },

  methods: {
    _maybeFill(field, value) {
      if (value == null || value === '') return;
      if (!(field in this.form)) return;
      const current = this.form[field];
      if (current == null || current === '' ||
          current === 'Unknown' || current === 0) {
        this.form[field] = value;
      }
    },
    _sexAsString(sexEnum) {
      if (sexEnum === 1) return 'Male';
      if (sexEnum === 2) return 'Female';
      return null;
    },
  },
};

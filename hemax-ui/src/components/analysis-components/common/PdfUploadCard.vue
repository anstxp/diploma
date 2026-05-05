<template>
  <div class="pdf-upload-card">
    <div class="pdf-head">
      <h4><i class="fa-solid fa-file-pdf"></i> {{ $t('pdf.uploadTitle') }}</h4>
      <span class="pdf-hint">{{ $t('pdf.uploadSubtitle') }}</span>
    </div>

    <div v-if="!extraction" class="upload-zone"
         :class="{ dragover, processing }"
         @dragover.prevent="dragover = true"
         @dragleave.prevent="dragover = false"
         @drop.prevent="onDrop">
      <input
        ref="fileInput"
        type="file"
        accept="application/pdf"
        @change="onFileSelected"
        class="file-input"
      />
      <div v-if="processing" class="processing-msg">
        <i class="fa-solid fa-spinner fa-spin"></i>
        {{ $t('pdf.processing') }}
      </div>
      <div v-else class="upload-msg" @click="$refs.fileInput.click()">
        <i class="fa-solid fa-cloud-arrow-up"></i>
        <p>{{ $t('pdf.dragText') }}</p>
        <small>{{ $t('pdf.sizeHint') }}</small>
      </div>
    </div>

    <div v-else class="extraction-result">
      <div class="result-head">
        <div>
          <h5>
            <i class="fa-solid fa-circle-check" :class="confidenceClass"></i>
            {{ $t('pdf.extractedHeader', { n: Object.keys(extraction.values).length }) }}
          </h5>
          <p class="result-meta">
            <span v-if="extraction.labName" class="lab">
              <i class="fa-solid fa-building"></i> {{ extraction.labName }}
            </span>
            <span class="confidence" :class="confidenceClass">
              {{ $t('pdf.confidenceLabel') }}: {{ confidenceLabel }}
              ({{ Math.round(extraction.confidence * 100) }}%)
            </span>
          </p>
        </div>
        <a v-if="extraction.pdfFileUrl" :href="extraction.pdfFileUrl" target="_blank" class="view-pdf">
          <i class="fa-solid fa-external-link-alt"></i> {{ $t('pdf.viewPdf') }}
        </a>
      </div>

      <div class="warning-block">
        <i class="fa-solid fa-triangle-exclamation"></i>
        <p>{{ $t('pdf.warning') }}</p>
      </div>

      <button class="btn-outline btn-small" @click="reset">
        <i class="fa-solid fa-rotate-left"></i> {{ $t('pdf.retryAnother') }}
      </button>
    </div>
  </div>
</template>

<script>
import analysesApi from "@/api/analyses";

export default {
  name: "PdfUploadCard",
  props: {
    /** "cbc" or "chem" — hint for the parser */
    hint: { type: String, required: true },
  },
  emits: ["extracted", "reset"],
  data() {
    return {
      dragover: false,
      processing: false,
      extraction: null,
    };
  },
  computed: {
    confidenceClass() {
      const c = this.extraction?.confidence || 0;
      if (c >= 0.7) return "high";
      if (c >= 0.4) return "mid";
      return "low";
    },
    confidenceLabel() {
      const c = this.extraction?.confidence || 0;
      if (c >= 0.7) return this.$t('pdf.confidenceHigh');
      if (c >= 0.4) return this.$t('pdf.confidenceMid');
      return this.$t('pdf.confidenceLow');
    },
  },
  methods: {
    async onFileSelected(e) {
      const file = e.target.files?.[0];
      e.target.value = "";
      if (!file) return;
      await this.uploadPdf(file);
    },
    async onDrop(e) {
      this.dragover = false;
      const file = e.dataTransfer.files?.[0];
      if (!file) return;
      await this.uploadPdf(file);
    },
    async uploadPdf(file) {
      const { validatePdf, checkPdfMagicBytes, extractApiError } =
        await import("@/utils/validation");

      const err = validatePdf(file);
      if (err) {
        this.$store.dispatch("flash", { type: "error", message: err });
        return;
      }

      if (!(await checkPdfMagicBytes(file))) {
        this.$store.dispatch("flash", {
          type: "error",
          message: this.$t('pdf.errorBadFile'),
        });
        return;
      }

      this.processing = true;
      try {
        const { data } = await analysesApi.extractFromPdf(file, this.hint);
        this.extraction = data;
        this.$emit("extracted", data);

        if (Object.keys(data.values).length === 0) {
          this.$store.dispatch("flash", {
            type: "warning",
            message: this.$t('pdf.errorNoValues'),
          });
        }
      } catch (e) {
        this.$store.dispatch("flash", {
          type: "error",
          message: extractApiError(e, this.$t('pdf.errorExtractFailed')),
        });
      } finally {
        this.processing = false;
      }
    },
    reset() {
      this.extraction = null;
      this.$emit("reset");
    },
  },
};
</script>

<style scoped lang="scss">
.pdf-upload-card {
  background: white;
  border: var(--border);
  border-radius: 0.6rem;
  padding: 1.6rem;
  margin-bottom: 1.5rem;
}

.pdf-head {
  margin-bottom: 1rem;

  h4 {
    font-size: 1.5rem;
    color: var(--purple);
    margin-bottom: 0.4rem;
    text-transform: none;
    font-weight: 600;

    i { margin-right: 0.4rem; }
  }

  .pdf-hint {
    font-size: 1.2rem;
    color: var(--light-color);
    text-transform: none;
    line-height: 1.5;
  }
}

.upload-zone {
  border: 2px dashed rgba(65, 90, 119, 0.3);
  border-radius: 0.5rem;
  padding: 2rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;

  &.dragover {
    border-color: var(--purple);
    background: rgba(65, 90, 119, 0.05);
  }

  &.processing { cursor: wait; opacity: 0.7; }

  .file-input { position: absolute; inset: 0; opacity: 0; cursor: pointer; }

  .upload-msg {
    color: var(--light-color);

    i { font-size: 3rem; color: var(--purple); display: block; margin-bottom: 0.7rem; }

    p {
      font-size: 1.4rem;
      color: var(--black);
      text-transform: none;
      margin-bottom: 0.3rem;
    }

    small { font-size: 1.1rem; }
  }

  .processing-msg {
    font-size: 1.4rem;
    color: var(--purple);
    text-transform: none;
    i { margin-right: 0.5rem; font-size: 1.6rem; }
  }
}

.extraction-result {
  .result-head {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 1rem;
    margin-bottom: 1rem;

    h5 {
      font-size: 1.4rem;
      color: var(--black);
      margin-bottom: 0.4rem;
      text-transform: none;
      font-weight: 600;

      i { margin-right: 0.4rem; }
      i.high { color: #3B6D11; }
      i.mid  { color: #854F0B; }
      i.low  { color: #A32D2D; }
    }

    .result-meta {
      display: flex;
      gap: 1.2rem;
      font-size: 1.2rem;
      color: var(--light-color);
      text-transform: none;
      i { margin-right: 0.3rem; }
      .confidence.high { color: #3B6D11; }
      .confidence.mid  { color: #854F0B; }
      .confidence.low  { color: #A32D2D; }
    }

    .view-pdf {
      font-size: 1.2rem;
      color: var(--purple);
      text-transform: none;
      flex-shrink: 0;
      i { margin-right: 0.3rem; }
      &:hover { text-decoration: underline; }
    }
  }

  .warning-block {
    display: flex;
    gap: 0.8rem;
    padding: 1rem 1.2rem;
    background: rgba(186, 117, 23, 0.08);
    border-left: 0.4rem solid #854F0B;
    border-radius: 0 0.4rem 0.4rem 0;
    margin: 1rem 0;

    i { color: #854F0B; flex-shrink: 0; font-size: 1.4rem; }

    p {
      font-size: 1.3rem;
      color: var(--black);
      text-transform: none;
      line-height: 1.6;
      margin: 0;
      strong { color: #854F0B; }
    }
  }
}
</style>

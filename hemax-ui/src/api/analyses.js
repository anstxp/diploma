import client from './client';

export const ANALYSIS_TYPE = {
  cbc: 1, chem: 2, risk: 3, neuro: 4, derma: 5,
  Cbc: 1, Chem: 2, Risk: 3, Neuro: 4, Derma: 5,
};

export const ANALYSIS_TYPE_NAME = {
  1: 'Cbc', 2: 'Chem', 3: 'Risk', 4: 'Neuro', 5: 'Derma',
};

export default {
  list(params = {}) {
    return client.get('/analyses', { params });
  },
  get(id, lang = null) {
    return client.get(`/analyses/${id}`, {
      params: lang ? { lang } : {},
    });
  },
  submit(kind, payload, language = 'uk', mergeRecentLabs = false) {
    const type = ANALYSIS_TYPE[kind];
    if (!type) throw new Error(`Unknown analysis kind: ${kind}`);
    const typeName = ANALYSIS_TYPE_NAME[type];  // e.g. 'Cbc', 'Chem', 'Neuro', 'Risk'
    return client.post(`/analyses/${typeName}`, {
      payloadJson: JSON.stringify(payload),
    }, {
      params: {
        lang: language,
        ...(mergeRecentLabs ? { mergeRecentLabs: true } : {}),
      },
    });
  },
  submitDerma(file, language = 'uk', extras = {}) {
    const fd = new FormData();
    fd.append('image', file);
    fd.append('language', language);
    Object.entries(extras).forEach(([k, v]) => {
      if (v !== null && v !== undefined && v !== '') fd.append(k, v);
    });
    return client.post('/analyses/derma', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  delete(id) {
    return client.delete(`/analyses/${id}`);
  },

  /**
   * Doctor adds a review note to a patient's analysis.
   * Backend: PATCH /api/analyses/{id}/annotate  body { note }
   * Accepts either a plain string or an object { note: '...' } for convenience.
   */
  doctorReview(id, payload) {
    const note = typeof payload === 'string' ? payload : payload?.note ?? '';
    return client.patch(`/analyses/${id}/annotate`, { note });
  },

  /** Alias: same call, different name. */
  annotate(id, payload) {
    return this.doctorReview(id, payload);
  },

  timeline(params = {}) {
    return client.get('/analyses/timeline', { params });
  },
  compare(params = {}) {
    return client.get('/analyses/compare', { params });
  },

  extractFromPdf(file, hint = null) {
    const fd = new FormData();
    fd.append('pdf', file);
    const params = hint ? { hint } : {};
    return client.post('/analyses/pdf/extract', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
      params,
    });
  },
  submitFromPdf(kind, payload, pdfFileAssetId, language = 'uk') {
    const type = ANALYSIS_TYPE[kind];
    if (!type) throw new Error(`Unknown analysis kind: ${kind}`);
    return client.post('/analyses/pdf/submit', {
      type,
      payloadJson: JSON.stringify(payload),
      pdfFileAssetId,
    }, {
      params: { lang: language },
    });
  },
};

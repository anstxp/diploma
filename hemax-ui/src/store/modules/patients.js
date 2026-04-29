import patientsApi from '@/api/patients';

// Backend DoctorPatientLinkDto:
//   {
//     id, doctorId, doctorName, doctorEmail, doctorAvatarUrl,
//     patientId, patientName, patientEmail, patientAvatarUrl, patientAge,
//     status, createdAt, respondedAt, inviteMessage, note
//   }
// status comes as a string thanks to JsonStringEnumConverter:
//   "Pending" | "Accepted" | "Rejected" | "Revoked"

function splitName(name) {
  const parts = (name || '').split(' ').filter(Boolean);
  return { firstName: parts[0] || '', lastName: parts.slice(1).join(' ') };
}

function normalizeStatus(s) {
  if (typeof s === 'number') {
    return ['Pending', 'Accepted', 'Rejected', 'Revoked'][s] || String(s);
  }
  return s;
}

function normalizeLinkForDoctor(link) {
  if (!link) return link;
  const { firstName, lastName } = splitName(link.patientName);
  return {
    ...link,
    linkId: link.id,
    userId: link.patientId,
    fullName: link.patientName || '',
    firstName,
    lastName,
    age: link.patientAge ?? null,
    email: link.patientEmail || '',
    avatarUrl: link.patientAvatarUrl || null,
    status: normalizeStatus(link.status),
    canRespond: false,
  };
}

function normalizeLinkForPatient(link) {
  if (!link) return link;
  const { firstName, lastName } = splitName(link.doctorName);
  const status = normalizeStatus(link.status);
  return {
    ...link,
    linkId: link.id,
    userId: link.doctorId,
    fullName: link.doctorName || '',
    firstName,
    lastName,
    email: link.doctorEmail || '',
    avatarUrl: link.doctorAvatarUrl || null,
    status,
    canRespond: status === 'Pending',
  };
}

const initialState = () => ({
  list: [],          // Doctor view: my patients
  invites: [],
  loading: false,
});

export default {
  namespaced: true,
  state: initialState,
  mutations: {
    setLoading(state, v) { state.loading = v; },
    setList(state, items) { state.list = items; },
    setInvites(state, items) { state.invites = items; },
    reset(state) {
      Object.assign(state, initialState());
    },
  },
  actions: {
    async loadMyPatients({ commit }) {
      commit('setLoading', true);
      try {
        const { data } = await patientsApi.myPatients();
        const items = (data.items || data || []).map(normalizeLinkForDoctor);
        commit('setList', items);
        return items;
      } finally {
        commit('setLoading', false);
      }
    },

    async loadMyDoctors({ commit }) {
      commit('setLoading', true);
      try {
        const { data } = await patientsApi.myDoctors();
        const items = (data.items || data || []).map(normalizeLinkForPatient);
        commit('setInvites', items);
        return items;
      } finally {
        commit('setLoading', false);
      }
    },

    async loadPendingInvites({ commit }) {
      const { data } = await patientsApi.pendingInvites();
      const items = (data.items || data || []).map(normalizeLinkForPatient);
      commit('setInvites', items);
      return items;
    },

    async invite(_ctx, { email, message }) {
      return patientsApi.invite(email, message);
    },

    async respond(_ctx, { linkId, accepted, note = null }) {
      return patientsApi.respond(linkId, accepted, note);
    },

    async revoke(_ctx, { linkId, reason = null }) {
      return patientsApi.removeLink(linkId, reason);
    },
  },
};

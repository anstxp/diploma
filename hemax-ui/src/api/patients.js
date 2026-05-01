import client from './client';

export default {
  myPatients(status = null) {
    return client.get('/doctors/my-patients', {
      params: status ? { status } : {},
    });
  },

  myDoctors(status = null) {
    return client.get('/doctors/my-doctors', {
      params: status ? { status } : {},
    });
  },

  pendingInvites() {
    return client.get('/doctors/invites');
  },

  invite(patientEmail, inviteMessage) {
    return client.post('/doctors/invites', {
      patientEmail,
      inviteMessage: inviteMessage || null,
    });
  },

  /** Patient accepts/declines an invite. */
  respond(linkId, accept, note = null) {
    return client.post(`/doctors/invites/${linkId}/respond`, {
      accept,
      note: note || null,
    });
  },

  /** Either side breaks the link. */
  removeLink(linkId, reason = null) {
    return client.delete(`/doctors/links/${linkId}`, {
      data: { reason: reason || null },
    });
  },
};

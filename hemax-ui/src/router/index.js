import { createRouter, createWebHistory } from 'vue-router';
import store from '@/store';

import HomeView from '@/views/HomeView.vue';
import SignInView from '@/views/SignInView.vue';
import SignUpView from '@/views/SignUpView.vue';
import AnalysesView from '@/views/AnalysesView.vue';
import NewAnalysisView from '@/views/NewAnalysisView.vue';
import AnalysisDetailsView from '@/views/AnalysisDetailsView.vue';
import BlogPostsView from '@/views/BlogPostsView.vue';
import BlogPostDetailsView from '@/views/BlogPostDetailsView.vue';
import CreateBlogView from '@/views/CreateBlogView.vue';
import UserHome from '@/views/UserHome.vue';
import UpdateUserProfile from '@/views/UpdateUserProfile.vue';
import ProfileView from '@/views/ProfileView.vue';
import ContactsView from '@/views/ContactsView.vue';
import FAQView from '@/views/FAQView.vue';
import PatientsView from '@/views/PatientsView.vue';
import PatientDetailsView from '@/views/PatientDetailsView.vue';
import InviteResponseView from '@/views/InviteResponseView.vue';
import NotFoundView from '@/views/NotFoundView.vue';

import AdminDashboard from '@/views/admin/DashboardView.vue';
import AdminUsersView from '@/views/admin/UsersView.vue';
import AdminAuditLogView from '@/views/admin/AuditLogView.vue';

const routes = [
  { path: '/', name: 'home', component: HomeView },
  { path: '/sign-in', name: 'sign-in', component: SignInView, meta: { guestOnly: true } },
  { path: '/sign-up', name: 'sign-up', component: SignUpView, meta: { guestOnly: true } },

  { path: '/analyses', name: 'analyses', component: AnalysesView, meta: { requiresAuth: true } },
  { path: '/analyses/new', name: 'new-analysis', component: NewAnalysisView, meta: { requiresAuth: true } },
  { path: '/analyses/:id', name: 'analysis-details', component: AnalysisDetailsView, meta: { requiresAuth: true } },

  { path: '/blog', name: 'blog', component: BlogPostsView },
  { path: '/blog/:id', name: 'blog-post', component: BlogPostDetailsView },
  { path: '/blog/new', name: 'create-blog', component: CreateBlogView, meta: { requiresAuth: true } },

  { path: '/user-home', name: 'user-home', component: UserHome, meta: { requiresAuth: true } },
  { path: '/profile', name: 'profile', component: ProfileView, meta: { requiresAuth: true } },
  { path: '/update-profile', name: 'update-profile', component: UpdateUserProfile, meta: { requiresAuth: true } },

  { path: '/patients', name: 'patients', component: PatientsView, meta: { requiresAuth: true, requiresDoctor: true } },
  { path: '/doctors/patients/:patientId', name: 'patient-details', component: PatientDetailsView, meta: { requiresAuth: true, requiresDoctor: true } },

  { path: '/doctors/invites/:linkId', name: 'invite-respond', component: InviteResponseView },

  { path: '/contacts', name: 'contacts', component: ContactsView },
  { path: '/faq', name: 'faq', component: FAQView },

  { path: '/admin', name: 'admin-dashboard', component: AdminDashboard, meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/admin/users', name: 'admin-users', component: AdminUsersView, meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/admin/audit-log', name: 'admin-audit', component: AdminAuditLogView, meta: { requiresAuth: true, requiresAdmin: true } },

  { path: '/:pathMatch(.*)*', name: 'not-found', component: NotFoundView },
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
  scrollBehavior() {
    return { top: 0 };
  },
});

router.beforeEach((to, _from, next) => {
  const isAuth = store.state.auth.isAuth;
  const isAdmin = store.getters['auth/isAdmin'];
  const isDoctor = store.getters['auth/isDoctor'];

  if (to.meta.requiresAuth && !isAuth) {
    return next({ name: 'sign-in', query: { redirect: to.fullPath } });
  }
  if (to.meta.requiresAdmin && !isAdmin) {
    return next({ name: 'home' });
  }
  if (to.meta.requiresDoctor && !isDoctor) {
    return next({ name: 'home' });
  }
  if (to.meta.guestOnly && isAuth) {
    return next({ name: 'user-home' });
  }
  next();
});

export default router;

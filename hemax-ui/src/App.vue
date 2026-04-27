<template>
  <router-view />
  <FlashMessage v-if="flash" :flash="flash" />
</template>

<script>
import FlashMessage from "@/components/UI/FlashMessage.vue";

export default {
  name: "App",
  components: { FlashMessage },
  computed: {
    flash() {
      return this.$store.state.flash;
    },
  },
};
</script>

<style></style>

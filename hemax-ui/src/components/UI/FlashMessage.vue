<template>
  <div :class="['flash', flash.type || 'info']">
    {{ flash.message }}
  </div>
</template>

<script>
export default {
  name: "FlashMessage",
  props: {
    flash: { type: Object, required: true },
  },
};
</script>

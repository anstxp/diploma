<template>
  <div v-if="sortedStories.length" class="stories">
    <h4>{{ $t('results.headers.detailedBreakdown') }}</h4>
    <div
      v-for="story in sortedStories"
      :key="story.cluster_id"
      :class="['story-card', `tier-${story.tier}`, `severity-${story.severity || 'low'}`]"
    >
      <div class="story-head">
        <span v-if="story.icon" class="story-icon">{{ story.icon }}</span>
        <h5>{{ story.title }}</h5>
      </div>
      <div class="story-body" v-html="bodyHtml(story.body)"></div>

      <div v-if="story.actions && story.actions.length" class="story-actions">
        <h6><i class="fa-solid fa-list-check"></i> {{ $t('results.stories.actionsHeader') }}</h6>
        <ul>
          <li v-for="(a, i) in story.actions" :key="i" v-html="inline(a)"></li>
        </ul>
      </div>

      <div v-if="story.red_flags && story.red_flags.length" class="story-redflags">
        <h6><i class="fa-solid fa-triangle-exclamation"></i> {{ $t('results.stories.redFlagsHeader') }}</h6>
        <ul>
          <li v-for="(f, i) in story.red_flags" :key="i" v-html="inline(f)"></li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script>
import { storyBodyHtml, inlineMd } from "@/utils/storyMarkdown";

export default {
  name: "StoryCards",
  props: {
    stories: { type: Array, default: () => [] },
  },
  computed: {
    sortedStories() {
      if (!Array.isArray(this.stories)) return [];
      const tierOrder = { critical: 0, abnormal: 1, info: 2, minor: 3, normal: 4 };
      return [...this.stories].sort(
        (a, b) => (tierOrder[a.tier] ?? 5) - (tierOrder[b.tier] ?? 5)
      );
    },
  },
  methods: {
    bodyHtml: storyBodyHtml,
    inline:   inlineMd,
  },
};
</script>

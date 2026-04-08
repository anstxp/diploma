# ⚠ Signals that warrant professional support
icon: 🆘
severity: high
---
The model detected **markers correlated with thoughts of self-harm or suicide**.

This is **not a diagnosis** — the model only estimates probability from lab and anthropometric data and **doesn't replace clinical evaluation**. But this signal alone is enough reason to talk to someone close or to a professional.

{% if recent_life_stressors %}You reported major life stressors in the last 6 months — this **adds urgency** to the signal. Crisis periods are temporary, even when they feel endless.
{% endif %}
{% if on_antidepressants %}You're on antidepressants. **Important to know:** in the first 1-2 weeks of treatment initiation (especially in people <25), suicidal thoughts can **temporarily worsen** — a known side effect that usually resolves. **Don't stop the medication abruptly**, but **do contact your doctor today or tomorrow** about these thoughts.
{% endif %}
{% if social_support_low %}You reported lacking close people in your life. Right now this can feel hopeless, but **a call to a crisis line is also "a close person" in this moment**. You don't need to know someone to talk.
{% endif %}
{% if has_chronic_pain or chronic_pain %}Chronic pain significantly raises risk of suicidal thoughts — this isn't weakness, it's a **predictable neurobiological response**. Treating pain improves mental state.
{% endif %}

**If you're in crisis or having thoughts of self-harm right now — please get help immediately. You are not alone.**
---
actions:
- 📞 **Crisis text/call lines:** 988 (US), 116 123 (EU), 7333 (Ukraine — free, 24/7, confidential)
- 🚑 **Emergency services — 112** (or local equivalent) if life is in danger
- See a GP, psychiatrist or therapist **within 1-2 days**
{% if on_antidepressants %}- **Contact your prescriber today** — report the thoughts. This **doesn't mean the medication is bad**, but the dose or choice may need adjustment
{% endif %}
- Tell someone close — a friend, relative — how you feel
- Don't stay alone for long; arrange to be with someone over the coming days
- Avoid alcohol and recreational drugs — they **amplify impulsivity** and significantly raise action risk
- **Remove easy access** to means of self-harm. Ask someone to temporarily store them outside your home
- Create a **safety plan**: 3 people you can call; 3 things that help you calm down; a plan for crisis moments
---
red_flags:
- **A specific plan** for self-harm — **call emergency services immediately**
- A sudden sense of **"relief" or "calm"** after a hard period — can mean a decision is made; high-risk sign
- Social withdrawal, **saying goodbye, giving away possessions**, writing a will without objective need
- Insomnia and exhausting thoughts for several days in a row
- **Access to firearms or large medication stockpiles** — ask someone to store them
{% if on_antidepressants %}- Severe new anxiety, agitation, insomnia in the first 1-2 weeks of an antidepressant — **see your doctor today**
{% endif %}

const { createApp, computed, onMounted, ref } = Vue;

createApp({
  setup() {
    const status = ref({});
    const reportVersion = ref(Date.now());

    const reportSrc = computed(() => `/report?t=${reportVersion.value}`);
    const statusClass = computed(() => {
      if (status.value.running) return 'is-running';
      if (status.value.last_ok === false) return 'is-failed';
      return 'is-ready';
    });
    const statusText = computed(() => {
      if (status.value.running) return 'running';
      if (status.value.last_ok === false) return 'failed';
      return 'ready';
    });
    const trimmedMessage = computed(() => {
      const message = status.value.last_message || 'not started';
      return message.length > 2400 ? message.slice(-2400) : message;
    });

    async function loadStatus() {
      const res = await fetch('/status', { cache: 'no-store' });
      status.value = await res.json();
    }

    function reloadReport() {
      reportVersion.value = Date.now();
    }

    async function refreshAll() {
      reloadReport();
      await loadStatus();
    }

    async function runNow() {
      await fetch('/run-now', { cache: 'no-store' });
      await loadStatus();
    }

    onMounted(() => {
      refreshAll();
      setInterval(loadStatus, 5000);
      setInterval(reloadReport, 60000);
    });

    return {
      loadStatus,
      refreshAll,
      reportSrc,
      runNow,
      status,
      statusClass,
      statusText,
      trimmedMessage,
    };
  },
}).mount('#app');

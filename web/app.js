const { createApp, computed, onMounted, ref } = Vue;

createApp({
  setup() {
    const status = ref({});
    const reportVersion = ref(Date.now());
    const loading = ref(false);
    const triggering = ref(false);
    const loadError = ref('');

    const reportSrc = computed(() => `/report?t=${reportVersion.value}`);
    const statusClass = computed(() => {
      if (status.value.running) return 'is-running';
      if (status.value.last_ok === false) return 'is-failed';
      if (loadError.value) return 'is-failed';
      return 'is-ready';
    });
    const statusText = computed(() => {
      if (status.value.running) return '跑批中';
      if (status.value.last_ok === false) return '失败';
      if (loadError.value) return '连接异常';
      return '就绪';
    });
    const taskSummary = computed(() => {
      if (status.value.running) return 'ETL 正在执行，请等待报告刷新';
      if (status.value.last_ok === false) return '最近一次任务失败，请查看右侧日志';
      if (status.value.last_ok === true) return '最近一次任务已完成';
      return '等待首次跑批';
    });
    const trimmedMessage = computed(() => {
      if (loadError.value) return loadError.value;
      const message = status.value.last_message || 'not started';
      return message.length > 2400 ? message.slice(-2400) : message;
    });

    async function loadStatus() {
      loading.value = true;
      try {
        const res = await fetch('/status', { cache: 'no-store' });
        if (!res.ok) throw new Error(`status request failed: ${res.status}`);
        status.value = await res.json();
        loadError.value = '';
      } catch (error) {
        loadError.value = `无法同步状态：${error.message || error}`;
      } finally {
        loading.value = false;
      }
    }

    function reloadReport() {
      reportVersion.value = Date.now();
    }

    async function refreshAll() {
      reloadReport();
      await loadStatus();
    }

    async function runNow() {
      triggering.value = true;
      try {
        const res = await fetch('/run-now', { cache: 'no-store' });
        if (!res.ok) throw new Error(`run request failed: ${res.status}`);
        await loadStatus();
      } catch (error) {
        loadError.value = `无法启动跑批：${error.message || error}`;
      } finally {
        triggering.value = false;
      }
    }

    onMounted(() => {
      refreshAll();
      setInterval(loadStatus, 5000);
      setInterval(reloadReport, 60000);
    });

    return {
      loadStatus,
      loading,
      refreshAll,
      reportSrc,
      runNow,
      status,
      statusClass,
      statusText,
      taskSummary,
      triggering,
      trimmedMessage,
    };
  },
}).mount('#app');

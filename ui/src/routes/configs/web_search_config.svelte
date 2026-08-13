<h2>Tavily API Key</h2>
<input bind:value={tavily_api_key} />

<h2>ScraperAPI API Key</h2>
<input bind:value={scraper_api_key} />

<button onclick={() => {
    if (!tavily_api_key || !scraper_api_key) return;
    setConfig('tools.web_search.tavily_api_key', tavily_api_key, false);
    setConfig('tools.web_search.scraper_api_key', scraper_api_key);
}}>Continue</button>

<script>
    import { onMount } from 'svelte';
    import { globals } from '$lib/index.svelte.js';

    let { setConfig } = $props();

    let tavily_api_key = $state();
    let scraper_api_key = $state();
</script>

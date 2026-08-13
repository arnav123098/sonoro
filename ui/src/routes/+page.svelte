{#if globals.is_conn}
    {#if currWindow.component}
        <Window name={currWindow.name} closeWindow={handleMissingConfigs} required={currWindow.required}>
            <currWindow.component setConfig={setConfig} />
        </Window>
    {/if}

    {#if globals.missing_configs.length === 0}
        {#if globals.current_char}
            <Interface />
        {:else}
            <Window name='Select Character' closeWindow={handleMissingConfigs} required={true}>
                <SelectCharacter />
            </Window>
        {/if}
    {/if}
{:else}
    <h2 id='load'>waiting for connection...</h2>
{/if}

<script>
    import { onMount } from 'svelte';
    import { io } from 'socket.io-client';

    import providers from './configs/providers.svelte';
    import models from './configs/models.svelte';
    import web_search_config from './configs/web_search_config.svelte';
    import SelectCharacter from './configs/select_character.svelte';

    import Window from './window.svelte';
    import Interface from './interface/interface.svelte';

    import { globals } from '$lib/index.svelte.js';

    let missing_configs = $state([]);

    let currWindow = $state({
        'name': null,
        'component': null
    });

    const windows = {
        providers: ['Setup Model Providers', providers, true], // [name, component, required]
        models: ['Select Models', models, true],
        web_search: ['Setup Web Search and Scraping Tools', web_search_config, true]
    };

    const setConfig = (key, value, close=true) => {
        const keys = key.split(".");

        let obj = globals.config;
        for (let i = 0; i < keys.length - 1; i++) {
            if (obj[keys[i]] === undefined || obj[keys[i]] === null) {
                obj[keys[i]] = {};
            }
            
            obj = obj[keys[i]];
        };

        obj[keys[keys.length - 1]] = value;

        if (close) {
            globals.conn.emit('updateConfig', globals.config);
            console.log('updating config...');
            handleMissingConfigs();
        };
    };

    const handleMissingConfigs = () => {
        // console.log('missing_configs: ', $state.snapshot(globals.missing_configs));

        if (globals.missing_configs.length > 0) {
            const config = globals.missing_configs[0];

            currWindow.name = windows[config][0];
            currWindow.component = windows[config][1];
            currWindow.required = windows[config][2];
        } else {
            currWindow.name = null;
            currWindow.component = null;
            currWindow.required = false;
        }
    };

    const handleLoadConfig = async (data) => {
        globals.config = data['config'];
        globals.missing_configs = data['missing_configs']

        handleMissingConfigs();

        console.log('config: ', $state.snapshot(globals.config));
    };

    onMount(() => {
        globals.conn = io("http://localhost:3000", {
            autoConnect: true,
            transports: ['websocket']
        });

        globals.conn.on("connect", () => {
            console.log('sonoro engine connected')
            globals.is_conn = true;
        });
        globals.conn.on("disconnect", () => {
            console.log('sonoro engine disconnected')
            globals.is_conn = false;
            window.location.reload();
        });

        globals.conn.on('loadConfig', handleLoadConfig);
        globals.conn.emit('getConfig');
    });

    $effect(() => {
        if (globals.bgImg) {
            document.body.style.backgroundImage = `url(${globals.bgImg})`;
        } else {
            document.body.style.background = 'white';
        }
    });

    // $effect(() => console.log('currWindow: ', $state.snapshot(currWindow.name)))
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Boldonse&family=Rubik:ital,wght@0,300..900;1,300..900&family=Titillium+Web:ital,wght@0,200;0,300;0,400;0,600;0,700;0,900;1,200;1,300;1,400;1,600;1,700&display=swap');

#load {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
}

:global(html) {
    scroll-behavior: smooth;
}

:global(select, option) {
    color: black;
}

:global(*) {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
    font-family: Rubik;
    color: white;
}

:global(body) {
    height: 100vh;
    width: 100vw;
    background-color: white;
    background-position: center;
    background-repeat: no-repeat;
    background-size: cover;
    overflow: hidden;
}

:global(button) {
    background-color: transparent;
    height: 2rem;
    width: fit-content;
    min-width: 3rem;
    padding: 0.5rem;
    border: solid 1px rgb(0, 140, 255);
    border-radius: 0.5rem;
    cursor: pointer;
}

:global(button):hover {
    background-color: rgb(0, 140, 255);
}

:global(input) {
    background-color: transparent;
    height: 2rem;
    width: 75%;
    max-width: 200px;
    min-width: 3rem;
    padding: 0.5rem;
    border: solid 1px rgb(0, 140, 255);
    border-radius: 0.5rem;
    margin-bottom: 1rem;
}

:global(input):focus, :global(textarea):focus {
    outline: none;
}
</style>

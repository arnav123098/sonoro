{#if globals.is_conn}
    {#if settingsActive}
        <Window name='Settings' closeWindow={() => settingsActive = false} required={false}>
            <Settings />
        </Window>
    {:else}
        {#if globals.current_char}
            <Interface />
        {:else}
            <button id='settings-btn' onclick={() => settingsActive = true}>Settings</button>
            <Window name='Select Character' closeWindow={() => {}} required={true}>
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

    import Settings from './configs/settings.svelte';
    import SelectCharacter from './configs/select_character.svelte';

    import Window from './window.svelte';
    import Interface from './interface/interface.svelte';

    import { globals } from '$lib/index.svelte.js';

    let settingsActive = $state(false);

    const handleLoadConfig = async (data) => {
        globals.config = data;
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
        globals.conn.on('info', (data) => {
            console.log(data);
        })

        globals.conn.on('loadConfig', handleLoadConfig);
        globals.conn.emit('getConfig');

        return () => {
            globals.conn.off('info', (data) => {
                console.log(data);
            })

            globals.conn.off('loadConfig', handleLoadConfig);
        }
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

#settings-btn {
    position: absolute;
    top: 3rem;
    left: 3rem;
}
</style>

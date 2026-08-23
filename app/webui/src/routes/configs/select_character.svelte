{#if !isCharConfigActive}
    {#if globals.characters}
        {#each Object.entries(globals.characters) as [char, pfp]}
            <div class='character-card'>
                <img class='pfp' src={pfp} alt={`${char}-pfp`} />
                <div>
                    <h3>{char}</h3>
                    <button onclick={() => {
                        character = char;
                        isCharConfigActive = true;
                    }}>edit</button>
                    <button onclick={() => globals.conn.emit('selectCharacter', char)}>select</button>
                </div>
            </div>
        {/each}
    {/if}

    <button id='new-character-btn' onclick={() => {
        newCharName = '';
        newCharMenuVisible = !newCharMenuVisible;
    }}>new character</button>

    {#if newCharMenuVisible}
        <input bind:value={newCharName} placeholder="character name">
        <button onclick={makeNewCharacter}>create</button>        
    {/if}
{:else}
    <Window name='Character Config' closeWindow={() => {
        isCharConfigActive = false;
        character = null;
    }} required={false}>
        <EditCharacter character={character}/>
    </Window>
{/if}

<script>
    import { globals } from "$lib/index.svelte";
    import { onMount } from 'svelte';
    import Window from '../window.svelte';

    import EditCharacter from './edit_character.svelte';

    let character = $state();
    let isCharConfigActive = $state(false);

    let newCharMenuVisible = $state(false);
    let newCharName = $state('');

    const handleListCharacters = async (data) => {
        globals.characters = data;
    }

    const makeNewCharacter = () => {
        if (Object.hasOwn(globals.characters, newCharName)) {
            window.alert('Character with that name already exists');
        } else if (newCharName) {
            globals.conn.emit('getCharacterData', newCharName, true);
            setTimeout(() => globals.conn.emit('getCharacters'), 500); // maybe fragile. fix it later.
        }

        newCharName = '';
        newCharMenuVisible = !newCharMenuVisible;
    }

    const handleSelectedCharacter = async (data) => {
        globals.bgImg = null;
        console.log('selected character: ', data);
        globals.current_char = data;
    }

    onMount(() => {
        globals.conn.on('listCharacters', handleListCharacters);
        globals.conn.on('selectedCharacter', handleSelectedCharacter);
        globals.conn.emit('getCharacters');
    });
</script>

<style>
    .character-card {
        display: flex;
        align-items: center;
        height: 6rem;
        margin-bottom: 0.5rem;
        padding: 1rem;
    }

    .character-card button {
        height: 2rem;
        font-size: 0.75rem;
        margin-top: 0.5rem;
    }

    .pfp {
        height: 5rem;
        width: 5rem;
        margin-right: 1rem;
        border: solid 3px rgb(0, 140, 255);
        border-radius: 50%;
    }

    button {
        font-weight: bold;
    }
</style>

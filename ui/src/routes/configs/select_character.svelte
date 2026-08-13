{#if !is_char_config_active}
    {#each globals.characters as char}
        <div class='character-card'>
            <img class='pfp' src={char.pfp} alt={`${char.dir}-pfp`} />
            <div>
                <h3>{char.dir}</h3>
                <button onclick={() => {
                    character_dir = char.dir;
                    is_char_config_active = true;
                }}>edit</button>
                <button onclick={() => globals.conn.emit('selectCharacter', char.dir)}>select</button>
            </div>
        </div>
    {/each}
{:else}
    <Window name='Character Config' closeWindow={() => {
        is_char_config_active = false;
        character_dir = null;
    }} required={false}>
        <MakeCharacter character_dir={character_dir}/>
    </Window>
{/if}

<script>
    import { globals } from '$lib/index.svelte';
    import { onMount } from 'svelte';
    import Window from '../window.svelte';

    import MakeCharacter from './make_character.svelte';

    let character_dir = $state();
    let is_char_config_active = $state(false);

    const handleLoadCharacterDirs = async (data) => {
        globals.characters = data;
    }

    const handleSelectedCharacter = async (data) => {
        globals.bgImg = null;
        globals.current_char = data;
    }

    onMount(() => {
        globals.conn.on('listCharacters', handleLoadCharacterDirs);
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

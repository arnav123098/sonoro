<div id='interface'>
    <div id='threeD'>
        <ThreeD model_path={globals.current_char.vrm_model} />
    </div>
    <div id='text-ui'>
        <div>
            <button onclick={() => {
                globals.bgImg = globals.defaultbg;
                globals.current_char = null;
                globals.conn.emit('deselectCharacter');
            }}>{'<-'}</button>
            <br><br>
        </div>
        <ul bind:this={messages} id='messages'></ul>

        <div>
        <input bind:value={userMessage}>
        <button id='send' onclick={() => {
            sendMessage(userMessage);
            userMessage = '';
        }}>send</button>
        </div>

        <div>
        <button onclick={!isRec ? startRec : stopRec}>{!isRec ? 'voice message' : 'send voice message'}</button>
        </div>
    </div>
</div>

<script>
    import ThreeD from './threeD.svelte';
    import { globals } from '$lib/index.svelte';
    import { onMount } from 'svelte';
    import { Lipsync } from "wawa-lipsync";
  import { sineOut } from 'svelte/easing';

    const lipsyncManager = new Lipsync();
    let playingVoice = $state(false);

    let RecordRTC;
    let isRec = $state(false);
    let stream;
    let recorder;

    let messages;
    let userMessage = $state('');

    let audioQueue = [];

    const handleInteraction = async (data) => {
        console.log('interaction: ', data.at(-1));

        messages.replaceChildren();

        data.forEach(d => {
            const li = document.createElement('li');
            li.textContent = d.author + ': ' + d.message;
            messages.appendChild(li);
        });
        
        messages.scrollTop = messages.scrollHeight;

        const animation = data.at(-1)?.animation;
        if (animation) globals.animator.playAnimation(animation);
    };

    const handleVoice = (audio) => {
        console.log('received audio')
        if (playingVoice) {
            audioQueue.push(audio);
        } else {
            const blob = new Blob([audio], { type: "audio/wav" });
            const url = URL.createObjectURL(blob);

            const player = new Audio(url);
            lipsyncManager.connectAudio(player);

            playingVoice = true;
            requestAnimationFrame(analyzeAudio);
            player.play();

            player.onended = () => {
                playingVoice = false;

                if (globals.animator) {
                    globals.animator.setViseme(null, true);
                }
                
                URL.revokeObjectURL(url);

                if (audioQueue.length != 0) {
                    handleVoice(audioQueue[0]);
                    audioQueue.splice(0, 1);
                }
            }
        }
    }

    const analyzeAudio = () => {
        if (!playingVoice) return;

        lipsyncManager.processAudio();

        const viseme = lipsyncManager.viseme;

        if (globals.animator) {
            globals.animator.setViseme(viseme);
        }

        requestAnimationFrame(analyzeAudio);
    }

    const sendMessage = (content, audio=false) => {
        if (!content) return;

        globals.conn.emit('userMessage', {
            type: audio ? 'audio' : 'text',
            content: content
        });
    };

    const handleWalkIn = (dir) => {
        if (globals.animator) {
            console.log('walkIn', dir);
            globals.animator.walkIn(dir);
        }
    };

    const handleWalkOut = async (dir) => {
        console.log('walkOut', dir)
        globals.animator.walkOut(dir);
    };

    onMount(() => {
        globals.conn.on('interaction', handleInteraction);
        globals.conn.on('playVoice', handleVoice);
        globals.conn.on('walkIn', handleWalkIn)
        globals.conn.on('walkOut', handleWalkOut);

        globals.bgImg = globals.current_char.theme.chat_background || '/chat.jpg';

        document.addEventListener('keydown', handleEnterPress);

        return () => {
            globals.conn.off('interaction', handleInteraction);
            globals.conn.off('playVoice', handleVoice);
            globals.conn.off('walkIn', handleWalkIn)
            globals.conn.off('walkOut', handleWalkOut);
            document.removeEventListener('keydown', handleEnterPress);
        }
    });

    $effect(() => {
        if (globals.animator && globals.animator.actions) {
            setTimeout(() => globals.conn.emit('movementSetup'), 1000);
        }
    });

    function handleEnterPress(e) {
        if (e.key === 'Enter') {
            sendMessage(userMessage);
            userMessage = '';
        }
    }

    async function startRec() {
        stream = await navigator.mediaDevices.getUserMedia({ 
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                sampleRate: 16000 
            }
        });

        const { default: RecordRTC, StereoAudioRecorder } = await import('recordrtc');
        recorder = new RecordRTC(stream, {
            type: 'audio',
            recorderType: RecordRTC.StereoAudioRecorder,
            mimeType: 'audio/wav',
            desiredSampRate: 16000,
            numberOfAudioChannels: 1
        });

        recorder.startRecording();
        isRec = true;
    }

    function stopRec() {
        if (recorder) {
            recorder.stopRecording(async () => {
                const blob = recorder.getBlob();

                if (blob.size > 0) {
                    const buffer = await blob.arrayBuffer();
                    sendMessage(buffer, true);
                };
                
                audio_cleanup();
            });
        }
        isRec = false;
    }

    function audio_cleanup() {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
        }
        stream = null;
        recorder = null;
    }
</script>

<style>
    #interface {
        height: 100%;
        width: 100%;
        display: flex;
    }

    :global(#interface *) {
        color: black;
    }

    #messages {
        list-style: none;
        height: 90%;
        overflow-y: scroll;
    }

    :global(#messages li) {
        margin-bottom: 0.5rem;
    }

    #messages::-webkit-scrollbar {
        width: 8px;
    }

    #messages::-webkit-scrollbar-track {
        background: transparent;
    }

    #messages::-webkit-scrollbar-thumb {
        background: rgba(255,255,255,.25);
        border-radius: 999px;
    }

    #messages::-webkit-scrollbar-thumb:hover {
        background: rgba(255,255,255,.4);
    }

    #text-ui {
        position: absolute;
        top: 50%;
        right: 2rem;
        transform: translateY(-50%);

        background: rgba(255, 255, 255, 0.5);
        border-radius: 16px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(5px);
        -webkit-backdrop-filter: blur(5px);
        border: 1px solid rgba(255, 255, 255, 0.3);

        height: 80%;
        width: 20%;

        display: flex;
        flex-direction: column;
        justify-content: end;

        padding: 2rem;
    }
</style>

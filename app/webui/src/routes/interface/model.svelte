<script>
    import * as THREE from 'three';
    import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
    import { VRMLoaderPlugin } from '@pixiv/three-vrm';
    import { VRM, VRMUtils } from "@pixiv/three-vrm";
    import { Animator } from './animator';
    import { onMount } from 'svelte';
    import { globals } from '$lib/index.svelte';

    let { model_path } = $props();
    let canvas;
    let renderer, scene, camera, loader;
    let model = null;
    let timer = new THREE.Timer();
    timer.connect(document);
    let animator;

    onMount(() => {
        scene = getScene();
        camera = getCamera();
        renderer = getRenderer();

        // MODEL SETUP
        loader = new GLTFLoader();

        if (model_path) {
            loader.register((parser) => {
                return new VRMLoaderPlugin(parser);
            });

            loader.load(
                model_path,

                gltf => {
                    const vrm = gltf.userData.vrm;
                    model = vrm;
                    scene.add(vrm.scene);

                    vrm.scene.rotation.y = Math.PI;

                    // ANIMATION MIXER
                    const mixer = new THREE.AnimationMixer(vrm.scene);
                    vrm.mixer = mixer;

                    animator = new Animator(vrm, camera);
                    globals.animator = animator;

                    globals.conn.emit('getAnimations');
                },

                undefined,

                error => console.error(error)
            );

            animate();

            globals.conn.on('loadAnimations', setupAnimator);

            return () => {
                console.log("Destroying model viewer");

                globals.animator = null;

                renderer.dispose();
                window.removeEventListener("resize", handleResize);
            };
        };

        function animate() {
            requestAnimationFrame(animate);

            timer.update();

            const deltaTime = timer.getDelta()

            if (model instanceof VRM) model.update(deltaTime);
            if (animator) animator.update(deltaTime);

            renderer.render(scene, camera);
        }

        function handleResize() {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        };
        window.addEventListener('resize', handleResize);

        return () => {
            window.removeEventListener('resize', handleResize);
            renderer.dispose();
        };
    });

    // SETUP THREE_JS
    function getScene() {
        const scene = new THREE.Scene();
        const light = new THREE.DirectionalLight(0xffffff, 2);
        light.position.set(1, 1.5, 2);
        scene.add(light);
        scene.add(new THREE.AmbientLight(0xffffff, 0.6));
        return scene;
    }

    function getCamera() {
        const camera = new THREE.PerspectiveCamera(
        40,
        window.innerWidth / window.innerHeight,
        0.1,
        100
        );
        camera.position.set(0, 1.25, 1.5);
        return camera;
    }

    function getRenderer() {
        const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
        renderer.outputEncoding = THREE.SRGBColorSpace;
        return renderer;
    }

    async function setupAnimator(data) {
        animator.animationPaths = data.animations;

        // LOAD ALL ACTIONS
        await Promise.all(
            Object.keys(animator.animationPaths).map(actionName =>
                animator.loadAction(actionName)
            )
        );

        animator.playAnimation(data.idle_animation);
    }
</script>

<canvas bind:this={canvas}></canvas>

<style>
  canvas {
    width: 100%;
    height: 70%;
  }
</style>

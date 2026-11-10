<script>
    import * as THREE from 'three';
    import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
    import { VRMLoaderPlugin } from '@pixiv/three-vrm';
    import { VRM, VRMUtils } from "@pixiv/three-vrm";
    import { Animator } from './animator';
    import { onMount } from 'svelte';
    import { globals } from '$lib/index.svelte';

    let log = false;

    let { model_path } = $props();
    let canvas;
    let renderer, scene, camera, loader;
    let model = null;
    let timer = new THREE.Timer();
    timer.connect(document);
    let animator;

    let lastTime = 0, frames = 0, animationFrameId;

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
                    model.scene.position.x = -1.5;
                    model.scene.visible = false;
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

            console.log({
                dpr: window.devicePixelRatio,
                resolution: [
                    renderer.domElement.width,
                    renderer.domElement.height
                ]
            });
        };

        function animate() {
            animationFrameId = requestAnimationFrame(animate);

            timer.update();
            frames++;

            const deltaTime = timer.getDelta()

            if (model instanceof VRM) model.update(deltaTime);
            if (animator) animator.update(deltaTime);

            const now = performance.now();
            if (now - lastTime >= 4000 && log) {
                const fps = frames * 1000 / (now - lastTime);
                frames = 0;

                console.log({
                    fps: Math.round(fps),
                    calls: renderer.info.render.calls,
                    triangles: renderer.info.render.triangles,
                    geometries: renderer.info.memory.geometries,
                    textures: renderer.info.memory.textures,
                    animator: globals.animator?.profile
                });

                lastTime = now;
            }

            renderer.render(scene, camera);
        }

        const canvasResizeObserver = new ResizeObserver(() => {
            const width = canvas.clientWidth;
            const height = canvas.clientHeight;

            camera.aspect = width / height;
            camera.updateProjectionMatrix();

            renderer.setSize(width, height, false);
        });

        canvasResizeObserver.observe(canvas);

        return () => {
            cancelAnimationFrame(animationFrameId);
            globals.animator.dispose();
            globals.animator = null;
            globals.conn.off('loadAnimations', setupAnimator);

            renderer.dispose();

            canvasResizeObserver.disconnect();
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
        const camera = new THREE.PerspectiveCamera(40, 1, 0.1, 100);
        camera.position.set(0, 1.25, 1.85);
        return camera;
    }

    function getRenderer() {
        const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
        renderer.setPixelRatio(1);
        renderer.outputColorSpace = THREE.SRGBColorSpace;
        return renderer;
    }

    async function setupAnimator(data) {
        if (!animator) return;

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
    display: block;
    width: 100%;
    height: 100%;
  }
</style>

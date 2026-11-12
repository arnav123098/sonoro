import * as THREE from 'three';
import { FBXLoader } from "three/examples/jsm/loaders/FBXLoader.js";
import { remapMixamoAnimationToVrm } from './remapMixamoAnimationToVrm';
import { globals } from '$lib/index.svelte';

export class Animator {
    constructor(model, camera) {
        this.model = model;
        this.mixer = model.mixer;
        this.camera = camera;

        this.modelBounds = new THREE.Box3().setFromObject(this.model.scene);
        this.modelLeft = this.modelBounds.min.x - this.model.scene.position.x;
        this.modelRight = this.modelBounds.max.x - this.model.scene.position.x;

        this.walkDirection = 0; // -1 for left | 0 for none | 1 for right
        this.moveSpeed = 0;
        this.walkTo = 0; // 0 for to center | 1 for to edge

        this.animationPaths = {}
        this.actions = {};
        this.currentAnimation = null;

        this.factor = -3

        this.action_list = Object.keys(this.actions);

        this.visemeMap = {
            viseme_A:  'aa',
            viseme_E:  'ee',
            viseme_I:  'ih',
            viseme_O:  'oh',
            viseme_U:  'ou',
            viseme_PP: 'aa', // P/B/M → closed mouth
            viseme_FF: 'ih', // F/V
            viseme_TH: 'ih',
            viseme_DD: 'aa',
            viseme_kk: 'aa',
            viseme_CH: 'ih',
            viseme_SS: 'ih',
            viseme_nn: 'aa',
            viseme_RR: 'oh',
            viseme_aa: 'aa',
            viseme_E:  'ee',
            viseme_I:  'ih',
            viseme_O:  'oh',
            viseme_U:  'ou'
        };
        this.currentExpression = null;

        this.onAnimationFinished = (e) => e.action === this.actions[this.currentAnimation] && e.action !== this.actions.walking && this.playAnimation('idle');
        this.mixer.addEventListener('finished', this.onAnimationFinished);
    }

    dispose() {
        this.mixer.removeEventListener(
            'finished',
            this.onAnimationFinished
        );
    }

    update(deltaTime) {
        // const start = performance.now();

        if (this.mixer) this.mixer.update(deltaTime);

        // const mixerTime = performance.now();

        if (this.walkDirection !== 0) {
            this.model.scene.position.x += this.walkDirection * this.moveSpeed * deltaTime;

            if (this.walkTo === 1 && this.checkIfOffscreen()) {
                globals.conn.emit('walkedOut', this.walkDirection);
                this.stopWalking(this.walkDirection * 0.2);
            }

            if (this.walkTo === 0) {
                if (this.walkDirection === 1 && this.model.scene.position.x >= 0) this.stopWalking();

                if (this.walkDirection === -1 && this.model.scene.position.x <= 0) this.stopWalking();
            }
        }

        // const end = performance.now();

        // this.profile = {
        //     mixer: mixerTime - start,
        //     walking: end - mixerTime,
        //     total: end - start
        // };
    }

    checkIfOffscreen() {
        const position = this.model.scene.position;

        const left = new THREE.Vector3(
            position.x + this.modelLeft,
            position.y,
            position.z
        ).project(this.camera);

        const right = new THREE.Vector3(
            position.x + this.modelRight,
            position.y,
            position.z
        ).project(this.camera);

        return this.walkDirection === 1
            ? left.x > 1
            : right.x < -1;
    }

    async loadAction(actionName) {
        const path = this.animationPaths[actionName];
        const fbxLoader = new FBXLoader();
        const fbx = await fbxLoader.loadAsync(path);
        const clip = remapMixamoAnimationToVrm(this.model, fbx);
        const action = this.mixer.clipAction(clip);
        
        if (actionName === 'walking') {
            action.setLoop(THREE.LoopRepeat, Infinity);
        } else if (actionName !== 'idle') {
            action.setLoop(THREE.LoopOnce);
            action.clampWhenFinished = true;
        }
        this.actions[actionName] = action;
    }

    setViseme(viseme, end=false) {
        const expression = this.visemeMap[viseme];

        const manager = this.model.expressionManager;

        for (const name of ['aa', 'ih', 'ou', 'ee', 'oh']) {
            manager.setValue(name, name === this.currentExpression && !end ? 0.4 : 0);
        }

        this.currentExpression = expression;

        if (!expression) return;
        manager.setValue(expression, 0.9);
    }

    playAnimation(name) {
        if (name === this.currentAnimation) return;
        
        const nextAction = this.actions[name];
        if (!nextAction) return;

        nextAction.reset();
        nextAction.enabled = true;
        nextAction.play();

        if (this.currentAnimation) {
            const currentAction = this.actions[this.currentAnimation];
            nextAction.crossFadeFrom(currentAction, 0.5, true);
        }

        this.currentAnimation = name;
    }

    walkOut(dir) {
        this.startWalking(dir, 1);
    }

    walkIn(dir) {
        this.model.scene.visible = true;
        this.model.scene.position.x = dir * this.factor;
        this.factor = -1.2
        this.startWalking(dir, 0);
    }

    startWalking(direction, to) {
        // direction: 1 for Right, -1 for Left
        this.playAnimation('walking');
        this.walkDirection = direction;
        this.moveSpeed = 1.1;
        const targetRotation = (direction === -1) ? Math.PI / 2 : -Math.PI / 2;
        this.model.scene.rotation.y = targetRotation;

        this.walkTo = to;
    }

    stopWalking(extra_width=0) {
        const targetRotation = Math.PI;
        this.model.scene.rotation.y = targetRotation;
        this.model.scene.position.x += extra_width;
        this.walkDirection = 0;
        this.moveSpeed = 0;
        this.playAnimation('idle');
        this.model.scene.visible = this.walkTo !== 1;
        this.walkTo = 0;
    }
}

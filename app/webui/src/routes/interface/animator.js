import * as THREE from 'three';
import { FBXLoader } from "three/examples/jsm/loaders/FBXLoader.js";
import { remapMixamoAnimationToVrm } from './remapMixamoAnimationToVrm';
import { globals } from '$lib/index.svelte';

export class Animator {
    constructor(model, camera) {
        this.model = model;
        this.mixer = model.mixer;
        this.camera = camera;

        this.modelBox = new THREE.Box3();
        this.frustum = new THREE.Frustum();
        this.viewProjectionMatrix = new THREE.Matrix4();

        this.walkDirection = 0; // -1 for left | 0 for none | 1 for right
        this.moveSpeed = 0;
        this.walkTo = 0; // 0 for to center | 1 for to edge

        this.animationPaths = {}
        this.actions = {};
        this.currentAnimation = null;

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
    }

    update(deltaTime) {
        if (this.mixer) {
            this.mixer.update(deltaTime);
        }

        if (this.walkDirection !== 0) {
            this.model.scene.position.x += this.walkDirection * this.moveSpeed * deltaTime;

            if (this.walkTo === 1 && this.checkIfOffscreen(this.model.scene)) {
                globals.conn.emit('walkedOut', this.walkDirection);
                this.stopWalking(this.walkDirection*0.1);
            }

            if (this.walkTo === 0) {
                if (this.walkDirection === 1 && this.model.scene.position.x >= 0) this.stopWalking();
                if (this.walkDirection === -1 && this.model.scene.position.x <= 0) this.stopWalking();
            }
        }
    }

    checkIfOffscreen() {
        if (!this.model.scene) return false;

        // 1. Update the camera matrices
        this.viewProjectionMatrix.multiplyMatrices(
            this.camera.projectionMatrix,
            this.camera.matrixWorldInverse
        );
        this.frustum.setFromProjectionMatrix(this.viewProjectionMatrix);

        // 2. Expand the Bounding Box to include the model and all its children
        // This calculates the literal "box" the character fits in right now
        this.modelBox.setFromObject(this.model.scene);
        
        // 3. Check if the frustum intersects this box
        const isOnScreen = this.frustum.intersectsBox(this.modelBox);
        
        return !isOnScreen;
    }

    async loadAction(actionName) {
        const path = this.animationPaths[actionName];
        const fbxLoader = new FBXLoader();
        const fbx = await fbxLoader.loadAsync(path);
        const clip = remapMixamoAnimationToVrm(this.model, fbx);
        const action = this.mixer.clipAction(clip);
        if (actionName !== 'idle') {
            action.setLoop(THREE.LoopOnce);
            action.clampWhenFinished = true;

            this.mixer.addEventListener('finished', (e) => {
                if (e.action === action) {
                    this.playAnimation('idle');
                }
            });
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

        if (this.currentAnimation) {
            const currentAction = this.actions[this.currentAnimation];

            nextAction.reset();
            nextAction.enabled = true;
            
            // use idle as a bridge to fade
            const idle = this.actions['idle'];
            idle.crossFadeFrom(currentAction, 0.5, true);
            idle.play();
            nextAction.crossFadeFrom(idle, 0.5, true);
            nextAction.play();
        } else {
            nextAction.play();
        }

        this.currentAnimation = name;
    }

    walkOut(dir) {
        this.startWalking(dir, 1);
    }

    walkIn(dir) {
        this.model.scene.visible = true;
        this.model.scene.position.x = -dir*1.2;
        this.startWalking(dir, 0);
    }

    startWalking(direction, to) {
        // direction: 1 for Right, -1 for Left
        this.walkDirection = direction;
        this.moveSpeed = 1.1;
        const targetRotation = (direction === -1) ? Math.PI / 2 : -Math.PI / 2;
        this.model.scene.rotation.y = targetRotation;

        this.walkTo = to;
        this.playAnimation('walking');
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

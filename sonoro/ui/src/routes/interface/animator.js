import * as THREE from 'three';
import { FBXLoader } from "three/examples/jsm/loaders/FBXLoader.js";
import { remapMixamoAnimationToVrm } from './remapMixamoAnimationToVrm';

export class Animator {
    constructor(model, camera) {
        this.model = model;
        this.mixer = model.mixer;
        this.camera = camera;

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
}

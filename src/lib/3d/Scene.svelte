<script lang="ts">
	import { onMount } from 'svelte';
	import * as THREE from 'three';
	import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
	import { FirstPersonControls } from 'three/addons/controls/FirstPersonControls.js';
	import { Clock, Vector2 } from 'three';
	import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
	import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
	import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';

	let container: HTMLElement;

	onMount(() => {
		// ----- Scene Setup -----
		const scene = new THREE.Scene();
		scene.fog = new THREE.Fog(0x1a1a1a, 10, 50);

		const camera = new THREE.PerspectiveCamera(
			75,
			window.innerWidth / window.innerHeight,
			0.1,
			1000
		);
		// Position camera inside the classroom. Adjust as needed.
		camera.position.set(0, 1.6, 5);
		camera.lookAt(0, 1.6, 0);

		const renderer = new THREE.WebGLRenderer({ antialias: true });
		renderer.setSize(window.innerWidth, window.innerHeight);
		renderer.setClearColor(0x1a1a1a);
		container.appendChild(renderer.domElement);

		// ----- Lighting -----
		const ambientLight = new THREE.AmbientLight(0xffffff, 0.3);
		scene.add(ambientLight);

		const directionalLight = new THREE.DirectionalLight(0xffffff, 0.5);
		directionalLight.position.set(5, 10, 7.5);
		scene.add(directionalLight);

		const loader = new GLTFLoader();

		// ----- Load Japanese Classroom Environment -----
		loader.load(
			'japanese_classroom.glb',
			(gltf) => {
				const environment = gltf.scene;
				// Optionally, adjust environment’s scale/position if needed:
				environment.position.set(0, 0, 10);
				scene.add(environment);
			},
			(xhr) => {
				console.log((xhr.loaded / xhr.total * 100) + '% loaded');
			},
			(error) => {
				console.error('Error loading Japanese classroom scene:', error);
			}
		);

		// ----- Load the Avatar Model (Stark-chan) -----
		loader.load(
			'starkchanmodel.glb',
			(gltf) => {
				const starkchan = gltf.scene;
				// Adjust Stark-chan’s position as needed so that she’s inside the classroom.
				starkchan.position.set(0, 0, 7);
				starkchan.scale.set(1, 1, 1);
				scene.add(starkchan);
			},
			(xhr) => {
				console.log((xhr.loaded / xhr.total * 100) + '% loaded');
			},
			(error) => {
				console.error('Error loading Stark-chan model:', error);
			}
		);

		// ----- Post-Processing: Bloom for Neon Glow (Optional) -----
		const composer = new EffectComposer(renderer);
		const renderPass = new RenderPass(scene, camera);
		composer.addPass(renderPass);

		const bloomPass = new UnrealBloomPass(
			new Vector2(window.innerWidth, window.innerHeight),
			1.5, // strength
			0.4, // radius
			0.85 // threshold
		);
		composer.addPass(bloomPass);

		// ----- First-Person Controls -----
		const controls = new FirstPersonControls(camera, renderer.domElement);
		controls.movementSpeed = 5;
		controls.lookSpeed = 0.1;
		controls.lookVertical = true;
		controls.constrainVertical = true;
		controls.verticalMin = 1.0;
		controls.verticalMax = 2.0;

		// ----- Animation Loop -----
		const clock = new Clock();
		const animate = () => {
			requestAnimationFrame(animate);
			const delta = clock.getDelta();
			controls.update(delta);
			composer.render(delta);
		};
		animate();

		// ----- Handle Window Resize -----
		const handleResize = () => {
			camera.aspect = window.innerWidth / window.innerHeight;
			camera.updateProjectionMatrix();
			renderer.setSize(window.innerWidth, window.innerHeight);
			composer.setSize(window.innerWidth, window.innerHeight);
		};

		window.addEventListener('resize', handleResize);
		return () => {
			window.removeEventListener('resize', handleResize);
		};
	});
</script>

<div bind:this={container}></div>

<style>
	div {
		width: 100%;
		height: 100%;
	}
</style>

<script lang="ts">
    import { onMount } from 'svelte';
    import * as THREE from 'three';
    import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

    import { FirstPersonControls } from 'three/addons/controls/FirstPersonControls.js'
    import { Clock } from 'three';

    let container: HTMLElement;
    
    onMount(() => {
      const scene = new THREE.Scene();
      const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
      const renderer = new THREE.WebGLRenderer({ antialias: true });
      const clock = new Clock();

      camera.position.set(0, 1.6, 5);
      camera.lookAt(0, 1.6, 0);
      // Add lights
      const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
      scene.add(ambientLight);
      
      const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
      directionalLight.position.set(5, 5, 5);
      scene.add(directionalLight);
    
      const groundGeometry = new THREE.PlaneGeometry(100, 100);
      const groundMaterial = new THREE.MeshStandardMaterial({ color: 0x808080 });
      const ground = new THREE.Mesh(groundGeometry, groundMaterial);
      ground.rotation.x = -Math.PI / 2;
      ground.position.y = -2;
      scene.add(ground);


      renderer.setSize(window.innerWidth, window.innerHeight);
      renderer.setClearColor(0x1a1a1a); // Dark gray background
      container.appendChild(renderer.domElement);
    
      const controls = new FirstPersonControls(camera, renderer.domElement);
        controls.movementSpeed = 5;
        controls.lookSpeed = 0.1;
        controls.lookVertical = true;
        controls.constrainVertical = true;
        controls.verticalMin = 1.0;
        controls.verticalMax = 2.0;


      
      // Load avatar
      const loader = new GLTFLoader();
      loader.load(
            'starkchanmodel.glb',
            (gltf) => {
                const model = gltf.scene;
                model.position.set(0, 0, 0);
                model.scale.set(1, 1, 1);
                scene.add(model);

                // Updated animation loop with proper delta time
                const animate = () => {
                    requestAnimationFrame(animate);
                    const delta = clock.getDelta();
                    controls.update(delta); // Pass the delta time
                    renderer.render(scene, camera);
                };
                animate();
        },
        // Loading progress
        (xhr) => {
          console.log((xhr.loaded / xhr.total * 100) + '% loaded');
        },
        // Error handling
        (error) => {
          console.error('An error occurred loading the model:', error);
        }
      );
    
      // Handle window resize
      const handleResize = () => {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
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
    
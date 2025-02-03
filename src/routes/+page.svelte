<script lang="ts">
import { browser } from '$app/environment';
import Scene from '../lib/3d/Scene.svelte';
</script>

<div class="scene-container">
  {#if browser}
    <Scene />
  {/if}
</div>

<style>
.scene-container {
  position: absolute;
  inset: 0;
  background: radial-gradient(hsl(220 14% 20%), hsl(220 20% 10%));
}
</style>

<script lang="ts">
    import { createEventDispatcher } from 'svelte';
    export let articleId: string;
    export let title: string;
  
    let comments: Array<{
      id: string;
      user: string;
      text: string;
      createdAt: string;
    }> = [];
    let newText = '';
  
    const dispatch = createEventDispatcher();
  
    // fetch existing comments
    async function loadComments() {
      const res = await fetch(
        `/api/comments/${encodeURIComponent(articleId)}`,
        { credentials: 'include' }
      );
      comments = res.ok ? await res.json() : [];
    }
  
    // submit a new comment
    async function submit() {
      if (!newText.trim()) return;
  
      const res = await fetch(
        `/api/comments/${encodeURIComponent(articleId)}`,
        {
          method: 'POST',
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: newText })
        }
      );
      if (res.ok) {
        const comment = await res.json();
        comments = [...comments, comment];
        newText = '';
      }
    }
  
    function cancel() {
      newText = '';
    }
  
    function close() {
      dispatch('close');
    }
  
    // load on initial render
    loadComments();
  </script>
  
  <aside class="account-sidebar comments-sidebar">
    <header>
      <h2>{title}</h2>
      <button class="close-btn" on:click={close}>✕</button>
    </header>
  
    <div class="sidebar-content">
      <label for="new-comment">Comments ({comments.length})</label>
      <input
        id="new-comment"
        type="text"
        placeholder="Share your thoughts."
        bind:value={newText}
      />
  
      <div class="btn-group">
        <button on:click={cancel}>Cancel</button>
        <button on:click={submit}>Submit</button>
      </div>
  
      {#each comments as c}
        <div class="comment">
          <strong>{c.user}</strong>
          <p>{c.text}</p>
          <small>{new Date(c.createdAt).toLocaleString()}</small>
        </div>
      {/each}
    </div>
  
    <footer>
      <button class="logout-btn" on:click={() => (location.href = '/logout')}>
        Log out
      </button>
    </footer>
  </aside>
  
  
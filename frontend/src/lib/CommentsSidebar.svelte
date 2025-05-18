<script lang="ts">
  import { createEventDispatcher, onMount } from 'svelte';
  import CommentThread from './CommentThread.svelte';
  export let articleId: string;
  export let title: string;
  export let user: { email: string } | null = null;

  let comments: Array<{
    id: string;
    user: string;
    text: string;
    createdAt: string;
    removed: boolean;
  }> = [];
  let newText = '';
  let error = '';
  let loading = false;
  let threadedComments: any[] = [];

  const dispatch = createEventDispatcher();

  // fetch existing comments
  async function loadComments() {
      loading = true;
      error = '';
      try {
          const res = await fetch(
          `/api/comments/${encodeURIComponent(articleId)}`,
          { credentials: 'include' }
      )
      if (res.ok) {
          comments = await res.json();
          // update the parent component with the comment count
          dispatch('updateCount', { articleId, count: comments.length });
      } else {
          const errorText = await res.text();
          error = 'Failed to load comments: ${res.status} ${errorText}';
          console.error(error, errorText);
      }
      } catch (err) {
          error = 'Failed to load comments';
          console.error('Comment loading error', err);
      } finally {
          loading = false;
      }
  }

  // submit a new comment
  async function submit() {
    if (!newText.trim()) return;
    error = ''
    loading = true;
    try {
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
        dispatch('updateCount', { articleId, count: comments.length });
      } else {
        const errorText = await res.text();
        error = 'Failed to post comment: ${res.status} ${errorText}';
        console.error(error, errorText);
      }
    } catch (err) {
      error = 'Error posting comment';
      console.error('Comment posting error', err);
    } finally {
      loading = false;
    }
  }

  function cancel() {
    newText = '';
  }

  function close() {
    dispatch('close');
  }

  function handleKeydown(event: KeyboardEvent) {
    if(event.key === 'Enter' && !event.shiftKey){
        event.preventDefault();
        submit();
    }
  }

  async function removeComment(commentId: string) {
    loading = true;
    error = '';
    try {
      const res = await fetch(`/api/comments/${commentId}`, {
        method: 'PATCH',
        credentials: 'include',
      });
      if (!res.ok) {
        const errorText = await res.text();
        error = `Failed to remove comment: ${res.status} ${errorText}`;
        console.error(error, errorText);
      } else {
        await loadComments();
      }
    } catch (err) {
      error = 'Error removing comment';
      console.error('Comment removal error', err);
    } finally {
      loading = false;
    }
  }

  function buildThread(comments: any[]): any[] {
    const map = new Map<string, any>();
    comments.forEach((c: any) => {
      map.set(c.id, { ...c, replies: [] });
    });
    const roots: any[] = [];
    map.forEach((c: any) => {
      if (c.parentId) {
        const parent = map.get(c.parentId);
        if (parent) parent.replies.push(c);
        else roots.push(c); // orphaned reply
      } else {
        roots.push(c);
      }
    });
    return roots;
  }

  onMount(() => {
      loadComments();
  });

  $: threadedComments = buildThread(comments);

</script>

<aside class="account-sidebar comments-sidebar">
  <header>
    <h2>{title}</h2>
    <button class="close-btn" on:click={close}>✕</button>
  </header>

  <div class="sidebar-content">
      {#if error}
      <div class="error">{error} </div>
      {/if}
  
    <label for="new-comment">Comments ({comments.length})</label>
    <input
      id="new-comment"
      type="text"
      placeholder="Share your thoughts."
      bind:value={newText}
      on:keydown={handleKeydown}
      disabled={loading}
    />
  
  <div class="btn-group">
    <button on:click={cancel} disabled={loading || !newText}>Cancel</button>
    <button 
      on:click={submit} 
      disabled={loading || !newText.trim()} 
      class="submit-btn"
    >
      {loading ? 'Posting...' : 'Submit'}
    </button>
  </div>

  {#if loading && comments.length === 0}
    <div class="loading">Loading comments...</div>
  {/if}

  {#each threadedComments as c}
    <CommentThread comment={c} articleId={articleId} user={user} on:reply={loadComments} />
  {/each}
</div>

<footer>
  <button class="logout-btn" on:click={() => (location.href = '/logout')}>
    Log out
  </button>
</footer></aside>

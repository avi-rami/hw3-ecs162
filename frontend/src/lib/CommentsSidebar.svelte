<script lang="ts">
  import { createEventDispatcher, onMount } from 'svelte';
  import CommentThread from './CommentThread.svelte';
  import './CommentsSidebar.css';
  export let articleId: string;
  export let title: string;
  export let user: { email: string } | null = null;

  // comments state
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
        const res = await fetch(`/api/comments/${encodeURIComponent(articleId)}`,{ credentials: 'include' });
      if (res.ok) {
        comments = await res.json();
        // update the parent component with the comment count
        dispatch('updateCount', { articleId, count: comments.length });
      } else {
        const errorText = await res.text();
        error = 'Failed to load comments';
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
      const res = await fetch(`/api/comments/${encodeURIComponent(articleId)}`,
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
        error = 'Failed to post comment';
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

  // handle keyboard shortcuts for comment submission
  function handleKeydown(event: KeyboardEvent) {
    if(event.key === 'Enter' && !event.shiftKey){
        event.preventDefault();
        submit();
    }
  }

  // organize comments into a threaded structure for nested display
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
        else roots.push(c); // no parent but still a comment
      } else {
        roots.push(c);
      }
    });
    return roots;
  }

  onMount(() => {
      loadComments();
  });

  // update threads when comments change
  $: threadedComments = buildThread(comments);

</script>

<!-- main sidebar for comments -->
<aside class="comments-sidebar">
  <!-- article title up top with a close button -->
  <header>
    <div class="article-title">{title}</div>
    <button class="close-btn" on:click={close}>✕</button>
  </header>

  <!-- comments counter -->
  <div class="comments-header">
    <h2>Comments ({comments.length})</h2>
  </div>

  <div class="sidebar-content">
    <!-- input section for comments -->
    <div class="input-section">
      {#if error}
        <div class="error">{error}</div>
      {/if}

      <!-- if logged in, show the comment box, otherwise ask them to login -->
      {#if user}
        <input
          id="new-comment"
          type="text"
          placeholder="Share your thoughts."
          bind:value={newText}
          on:keydown={handleKeydown}
          disabled={loading}
        />

        <!-- submit and cancel button -->
        <div class="btn-group">
          <button on:click={cancel} disabled={loading || !newText}>
            Cancel
          </button>
          <button 
            class="submit-btn"
            on:click={submit} 
            disabled={loading || !newText.trim()}
          >
            {loading ? 'Posting...' : 'Submit'}
          </button>
        </div>
      {:else}
        <p class="login-prompt">
          Please <a href="/login">log in</a> to leave a comment.
        </p>
      {/if}
    </div>

    <!-- comment display -->
    <div class="comments-section">
      {#if loading && comments.length === 0}
        <div class="loading">Loading comments...</div>
      {/if}

      <!-- loop through and show all comments in a threaded view -->
      {#each threadedComments as comment (comment.id)}
        <CommentThread 
          {comment}
          {articleId}
          {user}
          on:reply={loadComments}
        />
      {/each}

      <!-- show message if theres no comments -->
      {#if comments.length === 0 && !loading}
        <div class="no-comments">
          No comments yet. Be the first to share your thoughts!
        </div>
      {/if}
    </div>
  </div>
</aside>

<!-- logout button at the bottom -->
<footer>
  <button class="logout-btn" on:click={() => (location.href = '/logout')}>
    Log out
  </button>
</footer>

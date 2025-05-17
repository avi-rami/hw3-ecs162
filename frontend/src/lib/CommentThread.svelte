<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import CommentThread from './CommentThread.svelte';

  export let comment: {
    id: string;
    user: string;
    text: string;
    createdAt: string;
    parentId?: string;
    replies?: any[];
  };
  export let articleId: string;

  const dispatch = createEventDispatcher();
  let showReplyInput = false;
  let replyText = '';
  let loadingReply = false;
  let errorReply = '';

  function toggleReply() {
    showReplyInput = !showReplyInput;
    replyText = '';
    errorReply = '';
  }

  async function submitReply() {
    if (!replyText.trim()) return;
    loadingReply = true;
    try {
      const res = await fetch(
        `/api/comments/${encodeURIComponent(articleId)}`,
        {
          method: 'POST',
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            text: replyText,
            parentId: comment.id
          })
        }
      );
      if (!res.ok) {
        const errTxt = await res.text();
        throw new Error(errTxt);
      }
      const newComment = await res.json();
      // bubble up to the sidebar
      dispatch('reply', newComment);
      showReplyInput = false;
    } catch (err) {
      console.error('Reply error', err);
      errorReply = 'Failed to post reply';
    } finally {
      loadingReply = false;
    }
  }
</script>

<style>
  .comment-container {
    margin-bottom: 1rem;
  }
  .reply-thread {
    margin-left: 1.5rem;
    border-left: 1px solid #ddd;
    padding-left: 1rem;
  }
  .reply-input {
    margin-top: 0.5rem;
  }
</style>

<div class="comment-container">
  <div class="comment">
    <strong>{comment.user}</strong>
    <p>{comment.text}</p>
    <small>{new Date(comment.createdAt).toLocaleString()}</small>
    <button class="reply-btn" on:click={toggleReply}>Reply</button>
  </div>

  {#if showReplyInput}
    <div class="reply-input">
      <textarea
        bind:value={replyText}
        placeholder="Write a reply..."
        on:keydown={(e) =>
          e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), submitReply())
        }
        disabled={loadingReply}
      />
      {#if errorReply}
        <div class="error">{errorReply}</div>
      {/if}
      <div class="btn-group">
        <button on:click={toggleReply} disabled={loadingReply}>
          Cancel
        </button>
        <button on:click={submitReply} disabled={!replyText.trim() || loadingReply}>
          {loadingReply ? 'Posting...' : 'Submit'}
        </button>
      </div>
    </div>
  {/if}

  {#if comment.replies?.length}
    <div class="reply-thread">
      {#each comment.replies as reply (reply.id)}
        <!-- re-dispatch any nested reply events upward -->
        <CommentThread
          {articleId}
          comment={reply}
          on:reply={(e) => dispatch('reply', e.detail)}
        />
      {/each}
    </div>
  {/if}
</div>

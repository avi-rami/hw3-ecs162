<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  //import CommentThread from './CommentThread.svelte';
  import './CommentThread.css';

  // comment info
  export let comment: {
    id: string;
    user: string;
    text: string;
    createdAt: string;
    parentId?: string;
    replies?: any[];
    removed?: boolean;
  };
  export let articleId: string;
  export let user: { email: string } | null = null;

  // handles replies
  const dispatch = createEventDispatcher();
  let showReplyInput = false;
  let replyText = '';
  let loadingReply = false;
  let errorReply = '';

  // show/hide the reply box
  function toggleReply() {
    showReplyInput = !showReplyInput;
    replyText = '';
    errorReply = '';
  }

  // handle posting a new reply
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
      // notify parent of new reply
      dispatch('reply', newComment);
      showReplyInput = false;
    } catch (err) {
      console.error('Reply error', err);
      errorReply = 'Failed to post reply';
    } finally {
      loadingReply = false;
    }
  }

  // delete a comment (only mods can do this)
  async function removeComment(commentId: string) {
    loadingReply = true;
    errorReply = '';
    try {
      const res = await fetch(`/api/comments/${commentId}`, {
        method: 'PATCH',
        credentials: 'include',
      });
      if (!res.ok) {
        const errorText = await res.text();
        errorReply = `Failed to remove comment: ${res.status} ${errorText}`;
        console.error(errorReply, errorText);
      } else {
        // notify parent of removal
        dispatch('reply', { removed: true, id: commentId });
      }
    } catch (err) {
      errorReply = 'Error removing comment';
      console.error('Comment removal error', err);
    } finally {
      loadingReply = false;
    }
  }
</script>

<!-- comment threads -->
<div class="comment-container">
  <!-- the actual comment content -->
  <div class="comment">
    <strong>{comment.user}</strong>
    <p>{comment.removed ? 'Comment was removed by moderator' : comment.text}</p>
    <small>{new Date(comment.createdAt).toLocaleString()}</small>
    <div class="comment-actions">
      {#if !comment.removed}
        <button class="reply-btn" on:click={toggleReply}>
          Reply
        </button>
        <!-- only mods can delete comments -->
        {#if user && user.email === 'moderator@hw3.com'}
          <button class="remove-btn" on:click={() => removeComment(comment.id)}>
            Delete
          </button>
        {/if}
      {/if}
    </div>
  </div>

  <!-- reply box shows up button is clicked-->
  {#if showReplyInput}
    <div class="reply-input">
      <textarea
        bind:value={replyText}
        placeholder="Write a reply..."
        on:keydown={(e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            submitReply();
          }
        }}
        disabled={loadingReply}
      />
      {#if errorReply}
        <div class="error">{errorReply}</div>
      {/if}
      <div class="btn-group">
        <button on:click={toggleReply} disabled={loadingReply}>
          Cancel
        </button>
        <button 
          class="submit-btn"
          on:click={submitReply} 
          disabled={!replyText.trim() || loadingReply}
        >
          {loadingReply ? 'Posting...' : 'Submit'}
        </button>
      </div>
    </div>
  {/if}

  <!-- nested replies -->
  {#if comment.replies?.length}
    <div class="reply-thread">
      <!-- loop through and show all replies -->
      {#each comment.replies as reply (reply.id)}
        <svelte:self
          {articleId}
          comment={reply}
          {user}
          on:reply={(e) => dispatch('reply', e.detail)}
        />
      {/each}
    </div>
  {/if}
</div>

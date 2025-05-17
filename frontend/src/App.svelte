<script lang="ts">
  import { onMount } from 'svelte'
  import './app.css'
  import CommentsSidebar from './lib/CommentsSidebar.svelte'

  // state
  let articles: any[] = []
  let user: { email: string } | null = null

  // two separate panels
  let showAccountPanel = false
  let showCommentsPanel = false

  // which article to show comments for
  let currentArticle = { id: '', title: '' }

  /** Fired when CommentsSidebar dispatches `updateCount` */
  function handleUpdateCount(event) {
    const { articleId, count } = event.detail;
    // immutably update only that one article’s commentCount
    articles = articles.map((a) =>
      a._id === articleId ? { ...a, commentCount: count } : a
    );
  }

    /** after we load articles, also load their comment counts */
  async function loadCommentCounts() {
    // fire off one GET /api/comments/:id per article
    const counts = await Promise.all(
      articles.map(async (a) => {
        try {
          const res = await fetch(
            `/api/comments/${encodeURIComponent(a._id)}`,
            { credentials: 'include' }
          );
          if (!res.ok) throw new Error();
          const list = (await res.json()) as any[];
          return list.length;
        } catch {
          return 0;
        }
      })
    );
    // merge them back into the articles array
    articles = articles.map((a, i) => ({ ...a, commentCount: counts[i] }));
  }


  // proxy NYT via Flask
  function makeRequest(query: string) {
    const endpoint = `/api/search?q=${encodeURIComponent(query)}`
    fetch(endpoint, { credentials: 'include' })
      .then(res => { if (!res.ok) throw new Error(res.statusText); return res.json() })
      .then(processData)
      .catch(err => console.error('nyt fetch error', err))
  }

  function processData(apiResponse: any) {
    if (apiResponse.status === 'OK' && apiResponse.response?.docs) {
      // take first six and seed a 0-count
      articles = apiResponse.response.docs
        .slice(0, 6)
        .map((a) => ({ ...a, commentCount: 0 }));

      // **NEW**: immediately go fetch the real counts
      loadCommentCounts();
    } else {
      console.error('unexpected nyt payload', apiResponse);
    }
  }

  // helpers…
  function minutesToRead(words = 0) {
    return `${Math.max(1, Math.ceil(words / 200))} min read`
  }
  function getImageURL(a: any) {
    const rel = a.multimedia?.default?.url || a.multimedia?.thumbnail?.url || ''
    return rel.startsWith('http')
      ? rel
      : `https://static01.nyt.com/${rel.replace(/^\/+/, '')}`
  }

  let currentDate = ''
  let currentYear = new Date().getFullYear()

  onMount(async () => {
    // fetch session user
    try {
      const ures = await fetch('/api/user', { credentials: 'include' })
      if (ures.ok) user = await ures.json()
    } catch {}

    makeRequest('Sacramento (Calif) OR UC Davis')

    const now = new Date()
    currentDate = now.toLocaleDateString('en-US', {
      weekday: 'long', month: 'long', day: 'numeric', year: 'numeric'
    })
    currentYear = now.getFullYear()
  })

  // panels
  function openAccount() {
    showAccountPanel = true
  }
  function openComments(id: string, title: string) {
    currentArticle = { id, title }
    showCommentsPanel = true
  }
</script>

<svelte:head>
  <title>The New York Times</title>
  <link rel="stylesheet"
        href="https://fonts.googleapis.com/css2?family=Sumana:wght@700&display=swap" />
  <link rel="stylesheet"
        href="https://fonts.cdnfonts.com/css/cheyenne-sans" />
</svelte:head>

<header>
  <div class="date-container">
    <div class="date">{currentDate}</div>
    <div class="sub-date">Today's Paper</div>
  </div>

  <img src="/assets/images/The-New-York-Times-Logo 1.png"
       alt="NYT logo"
       class="logo" />

  {#if !user}
    <button class="login-button"
            on:click={() => (location.href = '/login')}>
      Log In
    </button>
  {:else}
    <!-- fix: actually *call* openAccount() -->
    <button class="login-button"
            on:click={openAccount}>
      Account ▾
    </button>
  {/if}
</header>

{#if showAccountPanel}
  <aside class="account-sidebar">
    <header>
      <strong>{user?.email}</strong>
      <button class="close-btn"
              on:click={() => (showAccountPanel = false)}>
        ✕
      </button>
    </header>
    <div class="account-content">
      <p>Good afternoon.</p>
    </div>
    <footer>
      <button class="logout-btn"
              on:click={() => (location.href = '/logout')}>
        Log Out
      </button>
    </footer>
  </aside>
{/if}

<main>
  <!-- Column 1 -->
  <section class="column">
    {#each articles.slice(0, 2) as a, i}
      <article>
        {#if i === 0}
          <img src={getImageURL(a)} alt={a.headline.main} />
        {/if}
        {#if i === 1}
          <div class="divider-horizontal"></div>
        {/if}

        <h3>{a.headline.main}</h3>
        <p>{a.abstract}</p>
        <div class="read-time">{minutesToRead(a.word_count)}</div>
        <button class="comment-btn"
                on:click={() => openComments(a._id, a.headline.main)}>
          💬 {a.commentCount ?? 0}
        </button>
      </article>
    {/each}
  </section>

  <!-- Column 2 -->
  <section class="column">
    {#each articles.slice(2, 4) as a, i}
      <article>
        {#if i === 1}
          <img src={getImageURL(a)} alt={a.headline.main} />
        {/if}

        <h3>{a.headline.main}</h3>
        <p>{a.abstract}</p>
        <div class="read-time">{minutesToRead(a.word_count)}</div>
        <button class="comment-btn"
                on:click={() => openComments(a._id, a.headline.main)}>
          💬 {a.commentCount ?? 0}
        </button>
      </article>

      {#if i === 0}
        <div class="divider-horizontal"></div>
      {/if}
    {/each}
  </section>

  <!-- Column 3 -->
  <section class="column">
    {#each articles.slice(4, 6) as a, i}
      <article>
        {#if i === 0}
          <img src={getImageURL(a)} alt={a.headline.main} />
        {/if}
        {#if i === 1}
          <div class="divider-horizontal"></div>
        {/if}

        <h3>{a.headline.main}</h3>
        <p>{a.abstract}</p>
        <div class="read-time">{minutesToRead(a.word_count)}</div>
        <button class="comment-btn"
                on:click={() => openComments(a._id, a.headline.main)}>
          💬 {a.commentCount ?? 0}
        </button>
      </article>
    {/each}
  </section>
</main>

{#if showCommentsPanel}
  {#key currentArticle.id}
    <CommentsSidebar
      articleId={currentArticle.id}
      title={currentArticle.title}
      on:close={() => (showCommentsPanel = false)}
      on:updateCount={handleUpdateCount}
    />
  {/key}
{/if}

<footer>
  <div class="footer-divider"></div>
  <p>© {currentYear} The New York Times Company</p>
</footer>
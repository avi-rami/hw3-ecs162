<script lang="ts">
  import { onMount } from 'svelte'
  import './app.css'

  // state
  let apiKey: string = ''
  let articles: any[] = []

  // nytimes api
  const BASE_URL =
    'https://api.nytimes.com/svc/search/v2/articlesearch.json'

  // fetch stories from the api
  function makeRequest(query: string, apiKey: string) {
    const endpoint = `${BASE_URL}?q=${encodeURIComponent(query)}&api-key=${apiKey}`
    console.log('requesting', endpoint)

    fetch(endpoint)
      .then(statusCheck)
      .then((r) => r.json())
      .then(processData)
      .catch(handleError)
  }

  // store the docs array in local state
  function processData(apiResponse: any) {
    console.log('nyt response', apiResponse)

    if (apiResponse.status === 'OK' && apiResponse.response?.docs) {
      // keep the first six docs; layout expects that length
      articles = apiResponse.response.docs
    } else {
      console.error('unexpected nyt payload', apiResponse)
    }
  }

  // throw on http error
  async function statusCheck(res: Response) {
    if (!res.ok) throw new Error(await res.text())
    return res
  }

  // network error helper
  function handleError(err: any) {
    console.error('fetch error', err.message)
  }

  // extras for layout: date, read-time badge, and images
  let currentDate = ''
  let currentYear = new Date().getFullYear()

  function minutesToRead(words = 0) {
    return `${Math.max(1, Math.ceil(words / 200))} min read`
  }

  function getImageURL(article: any): string {
    if (!article?.multimedia) return ''

    const relPath =
      article.multimedia.default?.url ??
      article.multimedia.thumbnail?.url ??
      ''

    if (!relPath) return ''

    // convert the relative path supplied by nyt into a full url
    return relPath.startsWith('http')
      ? relPath
      : `https://static01.nyt.com/${relPath.replace(/^\/+/, '')}`
  }

  // page setup on first mount
  onMount(async () => {
    try {
      const res = await fetch('/api/key')
      const data = await res.json()
      apiKey = data.apiKey
      // const query = 'UC Davis OR Sacramento (Calif)';
      // const fq = 'glocations:("DAVIS (CALIF) OR SACRAMENTO (CALIF)") OR organizations:("University of California, Davis")';
      //makeRequest(`${query}&fq=${encodeURIComponent(fq)}`, apiKey);
      makeRequest('Sacramento (Calif) OR UC Davis', apiKey);
    } catch (error) {
      console.error('failed to fetch api key', error)
    }

    const now = new Date()
    currentDate = now.toLocaleDateString('en-US', {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
      year: 'numeric'
    })
    currentYear = now.getFullYear()
  })
</script>

<!-- head: fonts and title -->
<svelte:head>
  <title>The New York Times</title>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Sumana:wght@700&display=swap" />
  <link rel="stylesheet" href="https://fonts.cdnfonts.com/css/cheyenne-sans" />
</svelte:head>

<!-- header -->
<header>
  <div class="date-container">
    <div class="date">{currentDate}</div>
    <div class="sub-date">Today's Paper</div>
  </div>

  <img
    src="/assets/images/The-New-York-Times-Logo 1.png"
    alt="the new york times logo"
    class="logo" />
</header>

<!-- main: three-column layout -->
<main>
  <!-- column 1 -->
  <section class="column">
    <!-- leading story with image -->
    <article>
      <img src={getImageURL(articles[0])} alt={articles[0]?.headline?.main} />
      <h3>{articles[0]?.headline?.main}</h3>
      <p>{articles[0]?.abstract}</p>
      <div class="read-time">{minutesToRead(articles[0]?.word_count)}</div>
    </article>

    <div class="divider-horizontal"></div>

    <!-- secondary headline -->
    <article>
      <h2>{articles[1]?.headline?.main}</h2>
      <p>{articles[1]?.abstract}</p>
      <div class="read-time">{minutesToRead(articles[1]?.word_count)}</div>
    </article>
  </section>

  <!-- column 2 -->
  <section class="column">
    <article>
      <h2>{articles[2]?.headline?.main}</h2>
      <p>{articles[2]?.abstract}</p>
      <div class="read-time">{minutesToRead(articles[2]?.word_count)}</div>
    </article>

    <div class="divider-horizontal"></div>

    <article>
      <img src={getImageURL(articles[3])} alt={articles[3]?.headline?.main} />
      <h3>{articles[3]?.headline?.main}</h3>
      <p>{articles[3]?.abstract}</p>
      <div class="read-time">{minutesToRead(articles[3]?.word_count)}</div>
    </article>
  </section>

  <!-- column 3 -->
  <section class="column">
    <article>
      <img src={getImageURL(articles[4])} alt={articles[4]?.headline?.main} />
      <h3>{articles[4]?.headline?.main}</h3>
      <p>{articles[4]?.abstract}</p>
      <div class="read-time">{minutesToRead(articles[4]?.word_count)}</div>
    </article>

    <div class="divider-horizontal"></div>

    <article>
      <h2>{articles[5]?.headline?.main}</h2>
      <p>{articles[5]?.abstract}</p>
      <div class="read-time">{minutesToRead(articles[5]?.word_count)}</div>
    </article>
  </section>
</main>

<!-- footer -->
<footer>
  <div class="footer-divider"></div>
  <p>© {currentYear} The New York Times Company</p>
</footer>

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, fireEvent, waitFor } from '@testing-library/svelte/svelte5';
import CommentsSidebar from '../lib/CommentsSidebar.svelte';

// test data types
interface Comment {
  id: string;
  user: string;
  text: string;
  createdAt: string;
  removed: boolean;
  parentId?: string;
}

// sample test data for a comment
const sampleComment: Comment = {
  id: 'comment1',
  user: 'testuser',
  text: 'This is a test comment',
  createdAt: new Date().toISOString(),
  removed: false
};

// performs fake api calls in our tests
// enables control over what data comes back
function mockFetchImpl(handlers: Record<string, (req: Request) => Promise<Response>>) {
  globalThis.fetch = vi.fn(async (input, init) => {
    // get url we are calling
    const url = typeof input === 'string' ? input : input.url;
    const path = url.replace('http://localhost', '');
    
    // print url we are calling
    console.log('MOCK FETCH CALLED:', path, init?.method);
    
    // look through our handlers to find one that matches this URL
    for (const key in handlers) {
      if (path.includes(key)) {
        const resp = await handlers[key](new Request('http://localhost' + url, init));
        
        // print the response
        try {
          const clone = resp.clone();
          const text = await clone.text();
          console.log('MOCK FETCH RESPONSE:', path, text);
        } catch (e) {}
        
        return resp;
      }
    }
    throw new Error('Unhandled fetch: ' + path);
  }) as any;
}

describe('User login and comment storing', () => {
  // resetting all mocks before each test
  beforeEach(() => {
    vi.resetAllMocks();
  });

  // TEST 1: check if users who aren't logged in can see the prompt for login
  it('should prompt login if user is not present', async () => {
    // fake api to return empty comments
    mockFetchImpl({
      '/api/comments/': async () => new Response(JSON.stringify([]), { status: 200 })
    });

    // create component w/o logged in user
    const { container } = render(CommentsSidebar, {
      props: { articleId: '1', title: 'Test Article', user: null }
    });

    // check if login message is visible
    expect(container.textContent).toMatch(/please\s*log in\s*to leave a comment/i);
  });

  // TEST 2: check if comments load and display properly
  it('should load and display comments', async () => {
    // fake test comment
    const testComment = { 
      id: 'c1', 
      user: 'alice', 
      text: 'Hello world', 
      createdAt: new Date().toISOString(), 
      removed: false 
    };
    let comments = [testComment];

    // fake api to return test comment
    mockFetchImpl({
      '/api/comments/': async() => new Response(JSON.stringify(comments), {status: 200}),
      '/api/comments/1': async (req) => {
        if (req.method === 'GET') {
          return new Response(JSON.stringify(comments), { status: 200 });
        }
        return new Response('Not found', { status: 404 });
      }
    });

    // component with a logged-in user
    const { container, findByText } = render(CommentsSidebar, {
      props: { articleId: '1', title: 'Test Article', user: { email: 'bob@hw3.com' } }
    });
    
    // wait and check for comment
    const commentElem = await findByText('Hello world', {}, {timeout: 3000});
    expect(commentElem).toBeTruthy();
    // await waitFor(() => {
    //   expect(container.textContent).toContain('Hello world');
    // }, { timeout: 2000 });
  });

  // TEST 3: check if comments are posted and cleared
  it('should submit a new comment and clear input', async () => {
    // fake comment that will be "posted"
    const testComment = { 
      id: 'c2', 
      user: 'bob', 
      text: 'Test comment', 
      createdAt: new Date().toISOString(), 
      removed: false 
    };
    
    // storing comments in our fake db
    let comments: any[] = [];
    
    // fake api handling post new comments
    mockFetchImpl({
      '/api/comments/': async (req) => {
        if (req.method === 'POST') {
          comments = [testComment];
          return new Response(JSON.stringify(testComment), { status: 200 });
        }
        return new Response(JSON.stringify(comments), { status: 200 });
      }
    });
    
    // component with a logged user
    const { container, getByPlaceholderText, getByText } = render(CommentsSidebar, {
      props: { articleId: '1', title: 'Test Article', user: { email: 'bob' } }
    });
    
    // type new comment and hit submit
    const input = getByPlaceholderText('Share your thoughts.');
    await fireEvent.input(input, { target: { value: 'Test comment' } });
    await fireEvent.click(getByText('Submit'));
    
    // does comment show up and input is cleared
    await waitFor(() => {
      expect(container.textContent).toContain('Test comment');
    }, { timeout: 2000 });
    expect((input as HTMLInputElement).value).toBe('');
  });

  // TEST 4: error handling
  it('should show error if comment post fails', async () => {
    // fake api to return error
    mockFetchImpl({
      '/api/comments/': async (req) => {
        if (req.method === 'POST') {
          return new Response('fail', { status: 500 });
        }
        return new Response(JSON.stringify([]), { status: 200 });
      }
    });

    // try and post a comment that will fail
    const { getByPlaceholderText, getByText, findByText } = render(CommentsSidebar, {
      props: { articleId: '1', title: 'Test Article', user: { email: 'bob' } }
    });
    const input = getByPlaceholderText('Share your thoughts.');
    await fireEvent.input(input, { target: { value: 'fail comment' } });
    await fireEvent.click(getByText('Submit'));

    // check for error message
    expect(await findByText(/failed to post comment|error posting comment/i)).toBeTruthy();
  });

  // TEST 5: empty comments
  it('should not submit empty comment', async () => {
    // fake api
    mockFetchImpl({
      '/api/comments/': async () => new Response(JSON.stringify([]), { status: 200 })
    });

    // component to try and submit empty comments
    const { getByPlaceholderText, getByText } = render(CommentsSidebar, {
      props: { articleId: '1', title: 'Test Article', user: { email: 'bob' } }
    });
    const input = getByPlaceholderText('Share your thoughts.');
    await fireEvent.input(input, { target: { value: '   ' } });
    const submitBtn = getByText('Submit');

    // checks if submit is disabled
    expect((submitBtn as HTMLButtonElement).disabled).toBe(true);
  });

  // TEST 6: moderator to remove comments
  it('should handle comment removal', async () => {
    let testComment = {
      id: 'c1',
      user: 'alice',
      text: 'Hello world',
      createdAt: new Date().toISOString(),
      removed: false
    };
    let comments = [testComment];
  
    mockFetchImpl({
      '/api/comments/': async () => new Response(JSON.stringify(comments), { status: 200 }),
      '/api/comments/1': async () => new Response(JSON.stringify(comments), { status: 200 }),
      '/api/comments/c1': async (req) => {
        if (req.method === 'PATCH') {
          testComment.removed = true;
          comments = [testComment];
          return new Response(JSON.stringify(testComment), { status: 200 });
        }
        return new Response('Method not allowed', { status: 405 });
      }
    });
  
    const { container, findByText } = render(CommentsSidebar, {
      props: {
        articleId: '1',
        title: 'Test Article',
        user: { email: 'moderator@hw3.com' }
      }
    });
  
    await waitFor(() => {
      expect(container.textContent).toContain('Hello world');
    });
  
    const removeButton = await findByText('Remove');
    await fireEvent.click(removeButton);
  
    await waitFor(() => {
      expect(container.textContent).toContain('[removed]');
    });
  });  
}); 
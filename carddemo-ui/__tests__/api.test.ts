/**
 * @jest-environment jsdom
 */
import { setToken, clearToken, getUserType, getUserId, isAdmin, api } from '@/lib/api';

beforeEach(() => {
  localStorage.clear();
  jest.restoreAllMocks();
});

describe('setToken', () => {
  it('stores token in localStorage', () => {
    setToken('my-token');
    expect(localStorage.getItem('access_token')).toBe('my-token');
  });
});

describe('clearToken', () => {
  it('removes all auth keys from localStorage', () => {
    localStorage.setItem('access_token', 'tok');
    localStorage.setItem('user_id', 'USR001');
    localStorage.setItem('user_type', 'A');
    clearToken();
    expect(localStorage.getItem('access_token')).toBeNull();
    expect(localStorage.getItem('user_id')).toBeNull();
    expect(localStorage.getItem('user_type')).toBeNull();
  });
});

describe('getUserType', () => {
  it('returns null when not set', () => {
    expect(getUserType()).toBeNull();
  });

  it('returns stored user_type', () => {
    localStorage.setItem('user_type', 'A');
    expect(getUserType()).toBe('A');
  });
});

describe('getUserId', () => {
  it('returns null when not set', () => {
    expect(getUserId()).toBeNull();
  });

  it('returns stored user_id', () => {
    localStorage.setItem('user_id', 'ADMIN001');
    expect(getUserId()).toBe('ADMIN001');
  });
});

describe('isAdmin', () => {
  it('returns true for admin user', () => {
    localStorage.setItem('user_type', 'A');
    expect(isAdmin()).toBe(true);
  });

  it('returns false for regular user', () => {
    localStorage.setItem('user_type', 'U');
    expect(isAdmin()).toBe(false);
  });

  it('returns false when not set', () => {
    expect(isAdmin()).toBe(false);
  });
});

describe('api', () => {
  const mockFetch = jest.fn();
  const originalFetch = global.fetch;

  beforeEach(() => {
    global.fetch = mockFetch;
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  it('api.get sends GET request with auth header', async () => {
    localStorage.setItem('access_token', 'test-token');
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ data: 'test' }),
    });

    const result = await api.get('/api/test');
    expect(result).toEqual({ data: 'test' });
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/test'),
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: 'Bearer test-token',
        }),
      }),
    );
  });

  it('api.post sends POST request with body', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ id: 1 }),
    });

    const result = await api.post('/api/items', { name: 'item1' });
    expect(result).toEqual({ id: 1 });
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/items'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ name: 'item1' }),
      }),
    );
  });

  it('api.put sends PUT request', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ updated: true }),
    });

    await api.put('/api/items/1', { name: 'updated' });
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/items/1'),
      expect.objectContaining({ method: 'PUT' }),
    );
  });

  it('api.delete sends DELETE request', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ deleted: true }),
    });

    await api.delete('/api/items/1');
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/items/1'),
      expect.objectContaining({ method: 'DELETE' }),
    );
  });

  it('throws on non-ok response', async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 500,
      json: () => Promise.resolve({ detail: 'Server error' }),
    });

    await expect(api.get('/api/fail')).rejects.toThrow('Server error');
  });

  it('clears token on 401 response', async () => {
    localStorage.setItem('access_token', 'expired-token');
    const locationHref = Object.getOwnPropertyDescriptor(window, 'location');
    delete (window as any).location;
    window.location = { href: '' } as any;

    mockFetch.mockResolvedValue({
      ok: false,
      status: 401,
      json: () => Promise.resolve({}),
    });

    await expect(api.get('/api/protected')).rejects.toThrow('Unauthorized');
    expect(localStorage.getItem('access_token')).toBeNull();

    if (locationHref) {
      Object.defineProperty(window, 'location', locationHref);
    }
  });
});

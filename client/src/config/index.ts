interface AppConfig {
  apiHost: string;
  environment: 'development' | 'production' | 'test';
  features: {
    videoSystem: boolean;
    highlights: boolean;
    chat: boolean;
  };
}

const getConfig = (): AppConfig => {
  const apiHost = process.env.NEXT_PUBLIC_API_HOST || 'http://localhost:8000';
  const environment = (process.env.NEXT_PUBLIC_ENV as AppConfig['environment']) || 'development';

  return {
    apiHost,
    environment,
    features: {
      videoSystem: process.env.NEXT_PUBLIC_ENABLE_VIDEO_SYSTEM !== 'false',
      highlights: process.env.NEXT_PUBLIC_ENABLE_HIGHLIGHTS !== 'false',
      chat: process.env.NEXT_PUBLIC_ENABLE_CHAT !== 'false',
    },
  };
};

export const config = getConfig();
export default config;

// API Endpoints
export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: '/api/v1/auth/login',
    REGISTER: '/api/v1/auth/register',
    ME: '/api/v1/auth/me',
  },
  SYSTEM: {
    START: '/api/v1/system/start',
    STATUS: '/api/v1/system/status',
    STOP: '/api/v1/system/stop',
    END: '/api/v1/system/end',
  },
  MEMORY: {
    SEARCH: '/api/v1/memory/search',
    CHATBOT: '/api/v1/memory/chatbot',
    CREATE: '/api/v1/memory/create',
  },
  VIDEOS: {
    LIST: '/api/v1/videos/',
    GET: (id: string) => `/api/v1/videos/${id}`,
    DELETE: (id: string) => `/api/v1/videos/${id}`,
  },
  HIGHLIGHTS: {
    LIST: '/api/v1/highlights/list',
  },
  INSIGHTS: {
    DAILY_RECAP: '/api/v1/insights/daily_recap',
    RECENT_EVENTS: '/api/v1/insights/recent_events',
  },
} as const;

// UI Constants
export const UI_CONSTANTS = {
  ANIMATION: {
    DURATION: {
      FAST: 0.2,
      NORMAL: 0.3,
      SLOW: 0.5,
    },
    EASE: 'easeInOut',
  },
  BREAKPOINTS: {
    MOBILE: 640,
    TABLET: 768,
    DESKTOP: 1024,
  },
} as const;

// Error Classes
export class APIError extends Error {
  constructor(
    message: string,
    public status?: number,
    public code?: string
  ) {
    super(message);
    this.name = 'APIError';
  }
}

export class AuthError extends APIError {
  constructor(message: string = 'Authentication failed') {
    super(message, 401, 'AUTH_ERROR');
    this.name = 'AuthError';
  }
}

export class NetworkError extends APIError {
  constructor(message: string = 'Network request failed') {
    super(message, 0, 'NETWORK_ERROR');
    this.name = 'NetworkError';
  }
}

export const handleAPIError = (error: any): APIError => {
  if (error.response) {
    // Server responded with error status
    const { status, data } = error.response;
    const message = data?.message || data?.detail || 'API request failed';
    
    if (status === 401) {
      return new AuthError(message);
    }
    
    return new APIError(message, status);
  } else if (error.request) {
    // Network error
    return new NetworkError('Unable to connect to server');
  } else {
    // Other error
    return new APIError(error.message || 'An unexpected error occurred');
  }
};
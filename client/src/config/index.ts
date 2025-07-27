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
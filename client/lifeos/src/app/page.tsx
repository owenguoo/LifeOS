import Image from "next/image";
import AnimatedSearchBar from "../components/AnimatedSearchBar";
import Widget from "../components/Widget";

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col">
      {/* Top Header - Fixed */}
      <header className="fixed top-20 md:top-12 left-0 right-0 z-20">
        <div className="container mx-auto px-4 py-4">
          <div className="flex flex-col items-center text-center gap-4">
            <h1 className="text-6xl font-semibold text-text-primary glow-light">LifeOS</h1>
            <div className="text-xl text-text-secondary">
              Today you did 3 things.
            </div>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 pt-20 pb-20 px-4 flex flex-col justify-center">
        <div className="container mx-auto max-w-md mx-auto px-16 space-y-12">
          <AnimatedSearchBar placeholder="Search memories" />
          <Widget />
        </div>
      </main>

      {/* Bottom Navigation - Fixed */}
      <nav className="fixed bottom-0 left-0 right-0 z-20 bg-surface/80 backdrop-blur-md border-t border-border">
        <div className="container mx-auto px-4 py-3">
          <div className="flex items-center justify-around">
            {/* Chat Tab */}
            <button className="flex flex-col items-center space-y-1 p-2 rounded-lg hover:bg-surface-hover transition-colors">
              <svg className="w-6 h-6 text-text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
              <span className="text-xs text-text-secondary">Chat</span>
            </button>

            {/* Activity Tab */}
            <button className="flex flex-col items-center space-y-1 p-2 rounded-lg hover:bg-surface-hover transition-colors">
              <svg className="w-6 h-6 text-text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
              <span className="text-xs text-text-primary">Activity</span>
            </button>

            {/* Automations Tab */}
            <button className="flex flex-col items-center space-y-1 p-2 rounded-lg hover:bg-surface-hover transition-colors">
              <svg className="w-6 h-6 text-text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <span className="text-xs text-text-secondary">Automations</span>
            </button>
          </div>
        </div>
      </nav>
    </div>
  );
}

import AnimatedSearchBar from "../components/AnimatedSearchBar";
import Widget from "../components/Widget";
import BottomNav from "../components/BottomNav";

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="fixed top-20 md:top-12 left-0 right-0 z-20">
        <div className="container mx-auto px-4 py-4">
          <div className="flex flex-col items-center text-center gap-8">
            <h1 className="text-6xl font-semibold text-text-primary glow-light">LifeOS</h1>
            <div className="text-xl text-text-secondary">
              Today you did 3 things.
            </div>
          </div>
        </div>
      </header>

      <main className="flex-1 pt-20 pb-20 px-4 flex flex-col justify-center">
        <div className="container mx-auto max-w-md mx-auto px-16 space-y-12">
          <AnimatedSearchBar placeholder="Search memories" />
          <Widget />
        </div>
      </main>

      <BottomNav />
    </div>
  );
}

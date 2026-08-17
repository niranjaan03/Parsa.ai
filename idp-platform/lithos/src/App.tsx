import { VideoBackground } from './components/VideoBackground';
import { NavigationBar } from './components/NavigationBar';
import { HeroContent } from './components/HeroContent';

export function App() {
  return (
    <div className="relative min-h-screen w-full bg-white overflow-hidden flex flex-col justify-start">
      {/* Video Background with JS fade system */}
      <VideoBackground />

      {/* Navigation Bar */}
      <NavigationBar />

      {/* Main Hero Content */}
      <HeroContent />
    </div>
  );
}

export default App;

import { useEffect, useRef } from 'react';

interface VideoBackgroundProps {
  videoUrl?: string;
}

export const VideoBackground = ({
  videoUrl = 'https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260329_050842_be71947f-f16e-4a14-810c-06e83d23ddb5.mp4',
}: VideoBackgroundProps) => {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const animFrameRef = useRef<number | null>(null);
  const fadingOutRef = useRef<boolean>(false);
  const fadingInRef = useRef<boolean>(false);

  const cancelRunningAnimation = () => {
    if (animFrameRef.current !== null) {
      cancelAnimationFrame(animFrameRef.current);
      animFrameRef.current = null;
    }
  };

  const getOpacity = (): number => {
    const video = videoRef.current;
    if (!video) return 0;
    const computedOpacity = video.style.opacity;
    if (computedOpacity === '' || computedOpacity === undefined) return 0;
    const parsed = parseFloat(computedOpacity);
    return isNaN(parsed) ? 0 : parsed;
  };

  const fadeIn = (duration = 250) => {
    cancelRunningAnimation();
    fadingInRef.current = true;
    fadingOutRef.current = false;

    const video = videoRef.current;
    if (!video) return;

    const startOpacity = getOpacity();
    const startTime = performance.now();

    const step = (now: number) => {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const currentOpacity = startOpacity + (1 - startOpacity) * progress;
      if (video) {
        video.style.opacity = currentOpacity.toString();
      }

      if (progress < 1) {
        animFrameRef.current = requestAnimationFrame(step);
      } else {
        fadingInRef.current = false;
        animFrameRef.current = null;
      }
    };

    animFrameRef.current = requestAnimationFrame(step);
  };

  const fadeOut = (duration = 250, onComplete?: () => void) => {
    cancelRunningAnimation();
    fadingOutRef.current = true;
    fadingInRef.current = false;

    const video = videoRef.current;
    if (!video) return;

    const startOpacity = getOpacity();
    const startTime = performance.now();

    const step = (now: number) => {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const currentOpacity = startOpacity * (1 - progress);
      if (video) {
        video.style.opacity = currentOpacity.toString();
      }

      if (progress < 1) {
        animFrameRef.current = requestAnimationFrame(step);
      } else {
        fadingOutRef.current = false;
        animFrameRef.current = null;
        if (onComplete) onComplete();
      }
    };

    animFrameRef.current = requestAnimationFrame(step);
  };

  const handleTimeUpdate = () => {
    const video = videoRef.current;
    if (!video || !video.duration) return;

    const remaining = video.duration - video.currentTime;
    if (remaining <= 0.55 && !fadingOutRef.current && !fadingInRef.current) {
      fadeOut(250);
    }
  };

  const handleEnded = () => {
    const video = videoRef.current;
    if (!video) return;

    cancelRunningAnimation();
    video.style.opacity = '0';
    fadingOutRef.current = false;
    fadingInRef.current = false;

    setTimeout(() => {
      if (video) {
        video.currentTime = 0;
        const playPromise = video.play();
        if (playPromise !== undefined) {
          playPromise
            .then(() => {
              fadeIn(250);
            })
            .catch(() => {});
        }
      }
    }, 100);
  };

  const handleLoadedData = () => {
    const video = videoRef.current;
    if (!video) return;
    video.style.opacity = '0';
    const playPromise = video.play();
    if (playPromise !== undefined) {
      playPromise
        .then(() => {
          fadeIn(250);
        })
        .catch(() => {});
    }
  };

  useEffect(() => {
    const video = videoRef.current;
    if (video) {
      video.style.opacity = '0';
      if (video.readyState >= 2) {
        handleLoadedData();
      }
    }
    return () => {
      cancelRunningAnimation();
    };
  }, []);

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none z-0">
      <video
        ref={videoRef}
        src={videoUrl}
        muted
        playsInline
        onTimeUpdate={handleTimeUpdate}
        onEnded={handleEnded}
        onLoadedData={handleLoadedData}
        className="absolute top-0 left-1/2 -translate-x-1/2 w-[115%] h-[115%] object-cover object-top max-w-none max-h-none"
        style={{ opacity: 0, transition: 'none' }}
      />
    </div>
  );
};

import React from 'react';
import {AbsoluteFill, Sequence, OffthreadVideo, Audio, staticFile, useCurrentFrame, interpolate} from 'remotion';
import {loadFont} from '@remotion/google-fonts/NotoSansTelugu';
import timeline from '../timeline.json';

const {fontFamily} = loadFont();

const Subtitle: React.FC<{text: string; voFrames: number}> = ({text, voFrames}) => {
  const frame = useCurrentFrame();
  const out = Math.max(12, voFrames);
  const opacity = interpolate(frame, [0, 8, out - 8, out + 10], [0, 1, 1, 0], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  return (
    <AbsoluteFill style={{justifyContent: 'flex-end', alignItems: 'center', paddingBottom: 250, paddingLeft: 36, paddingRight: 36}}>
      <div style={{
        opacity, maxWidth: '90%', textAlign: 'center', fontFamily,
        fontSize: 58, lineHeight: 1.34, color: '#FFE08A', fontWeight: 700,
        textShadow: '0 3px 16px rgba(0,0,0,0.9), 0 0 2px #000',
        background: 'rgba(14,6,0,0.5)', padding: '20px 30px', borderRadius: 24,
      }}>
        {text}
      </div>
    </AbsoluteFill>
  );
};

const Kicker: React.FC<{text: string}> = ({text}) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [6, 18, 72, 90], [0, 1, 1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const y = interpolate(frame, [6, 24], [28, 0], {extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill style={{justifyContent: 'flex-start', alignItems: 'center', paddingTop: 150}}>
      <div style={{
        opacity, transform: `translateY(${y}px)`, fontFamily,
        fontSize: 70, fontWeight: 700, color: '#FFFFFF', textAlign: 'center', maxWidth: '88%',
        textShadow: '0 4px 18px rgba(0,0,0,0.95), 0 0 3px #C8421F', letterSpacing: 1,
      }}>
        {text}
      </div>
    </AbsoluteFill>
  );
};

export const Reel: React.FC = () => {
  return (
    <AbsoluteFill style={{backgroundColor: 'black'}}>
      {timeline.shots.map((s) => (
        <Sequence key={s.id} from={s.startFrame} durationInFrames={s.durFrames}>
          <AbsoluteFill>
            <OffthreadVideo src={staticFile(s.clip)} muted style={{width: '100%', height: '100%', objectFit: 'cover'}} />
          </AbsoluteFill>
          <Audio src={staticFile(s.audio)} />
          {s.onscreen ? <Kicker text={s.onscreen} /> : null}
          <Subtitle text={s.narration} voFrames={s.voFrames} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};

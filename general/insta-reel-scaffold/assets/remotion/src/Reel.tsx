import React from 'react';
import {AbsoluteFill, Sequence, OffthreadVideo, Audio, staticFile, useCurrentFrame, interpolate} from 'remotion';
import {loadFont} from '@remotion/google-fonts/NotoSansTelugu';
import timeline from '../timeline.json';

const {fontFamily} = loadFont();

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

// Primary Telangana term / synonym, emphasised in the centre when it is spoken.
const KeyWord: React.FC<{text: string; durFrames: number}> = ({text, durFrames}) => {
  const frame = useCurrentFrame();
  const inEnd = 26, outStart = Math.max(inEnd + 10, durFrames - 14);
  const opacity = interpolate(frame, [14, inEnd, outStart, durFrames - 2], [0, 1, 1, 0], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  const scale = interpolate(frame, [14, inEnd], [0.82, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center'}}>
      <div style={{
        opacity, transform: `translateY(-30px) scale(${scale})`, fontFamily,
        fontSize: 64, fontWeight: 800, color: '#FFD23F', textAlign: 'center', maxWidth: '90%',
        lineHeight: 1.3, letterSpacing: 0.5,
        textShadow: '0 4px 20px rgba(0,0,0,0.95)',
        background: 'linear-gradient(180deg, rgba(20,6,30,0.62), rgba(40,0,20,0.62))',
        border: '2px solid rgba(230,0,126,0.85)', boxShadow: '0 0 26px rgba(230,0,126,0.45)',
        padding: '18px 30px', borderRadius: 22,
      }}>
        {text}
      </div>
    </AbsoluteFill>
  );
};

// Silent follow-nudge in the final beat (we cut the spoken CTA).
const EndCard: React.FC<{text: string; durFrames: number}> = ({text, durFrames}) => {
  const frame = useCurrentFrame();
  const start = Math.max(0, durFrames - 70);
  const opacity = interpolate(frame, [start, start + 12, durFrames - 2], [0, 1, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill style={{justifyContent: 'flex-end', alignItems: 'center', paddingBottom: 230}}>
      <div style={{
        opacity, fontFamily, fontSize: 52, fontWeight: 800, color: '#FFFFFF', textAlign: 'center', maxWidth: '90%',
        background: 'rgba(230,0,126,0.82)', padding: '16px 30px', borderRadius: 40,
        textShadow: '0 2px 10px rgba(0,0,0,0.6)', boxShadow: '0 0 22px rgba(230,0,126,0.5)',
      }}>
        {text}
      </div>
    </AbsoluteFill>
  );
};

export const Reel: React.FC = () => {
  return (
    <AbsoluteFill style={{backgroundColor: 'black'}}>
      {timeline.shots.map((s) => {
        let off = 0;
        return (
          <Sequence key={s.id} from={s.startFrame} durationInFrames={s.durFrames}>
            {s.segments.map((seg, i) => {
              const from = off; off += seg.durFrames;
              return (
                <Sequence key={i} from={from} durationInFrames={seg.durFrames}>
                  <AbsoluteFill>
                    <OffthreadVideo src={staticFile(seg.clip)} muted style={{width: '100%', height: '100%', objectFit: 'cover'}} />
                  </AbsoluteFill>
                </Sequence>
              );
            })}
            <Audio src={staticFile(s.audio)} />
            {s.onscreen ? <Kicker text={s.onscreen} /> : null}
            {('keyword' in s && (s as {keyword?: string}).keyword)
              ? <KeyWord text={(s as {keyword: string}).keyword} durFrames={s.durFrames} /> : null}
            {('endcard' in s && (s as {endcard?: string}).endcard)
              ? <EndCard text={(s as {endcard: string}).endcard} durFrames={s.durFrames} /> : null}
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};

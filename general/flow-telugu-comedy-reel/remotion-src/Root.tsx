import React from 'react';
import {Composition} from 'remotion';
import {Reel} from './Reel';
import timeline from '../timeline.json';

export const RemotionRoot: React.FC = () => (
  <Composition
    id="Reel"
    component={Reel}
    durationInFrames={timeline.totalFrames}
    fps={timeline.fps}
    width={timeline.width}
    height={timeline.height}
  />
);

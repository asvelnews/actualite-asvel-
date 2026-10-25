import React from 'react';
import {ShaderCanvas} from './ShaderCanvas';
import {firePx, smokePx} from './cpuShaders';

type Rgb = [number, number, number];

/**
 * Couche de fumée indépendante. Chaque couche a sa graine, son échelle, sa dérive et
 * sa turbulence : superposées, elles donnent de la profondeur (loin = lent et grand,
 * près = rapide et flou).
 */
export const Smoke: React.FC<{
  color?: Rgb;
  light?: Rgb;
  lightDir?: [number, number];
  density?: number;
  scale?: number;
  flow?: [number, number];
  seed?: number;
  turb?: number;
  band?: [number, number, number, number];
  hole?: [number, number, number];
  opacity?: number;
  res?: number;
  timeOffset?: number;
  blend?: React.CSSProperties['mixBlendMode'];
  style?: React.CSSProperties;
}> = ({
  color = [0.02, 0.012, 0.015],
  light = [0.4, 0.05, 0.04],
  lightDir = [0, -1],
  density = 1,
  scale = 1.6,
  flow = [0.04, 0.1],
  seed = 1,
  turb = 0.9,
  band = [0, 1, 0.1, 3],
  hole = [0, 0, 0],
  opacity = 1,
  res = 0.25,
  timeOffset = 0,
  blend,
  style,
}) =>
  opacity <= 0.001 ? null : (
    <ShaderCanvas
      scale={res}
      timeOffset={timeOffset}
      blend={blend}
      style={style}
      make={(t) => smokePx({t, color, light, lightDir, density, scale, flow, seed, turb, band, hole, opacity})}
    />
  );

export const Fire: React.FC<{
  height?: number;
  intensity?: number;
  seed?: number;
  scale?: number;
  dir?: [number, number];
  opacity?: number;
  res?: number;
  style?: React.CSSProperties;
  width?: number;
  heightPx?: number;
  soft?: boolean;
}> = ({height = 0.25, intensity = 0.9, seed = 1, scale = 6, dir = [0, 1], opacity = 1, res = 0.3, style, width, heightPx, soft}) =>
  opacity <= 0.001 ? null : (
    <ShaderCanvas
      scale={res}
      blend="screen"
      style={style}
      width={width}
      height={heightPx}
      make={(t) => firePx({t, height, intensity, seed, scale, dir, opacity, soft})}
    />
  );

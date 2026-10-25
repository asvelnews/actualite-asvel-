import React from 'react';
import {Sequence} from 'remotion';
import {S1Arena} from '../scenes/S1Arena';

/** Phase 3 : extrait de 5 s de l'arène hantée (fumée, éclairs, travelling). */
export const VfxTest: React.FC = () => (
  <Sequence from={-300}>
    <S1Arena />
  </Sequence>
);

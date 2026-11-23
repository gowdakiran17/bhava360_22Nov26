import type { EngineModule } from '@bhava360/core';

interface Input {
  cardIds: readonly string[];
}

// Fact fields will be defined with the engine implementation.
export const tarot: EngineModule<Input, Record<never, never>> = {
  id: 'tarot',
  inputs: ["cardIds"],
  factsSchema: {},
  screens: ["ask"],
  namespace: 'tarot',
  featureFlag: 'engine.tarot',
  computeFacts() {
    throw new Error('not implemented');
  }
};

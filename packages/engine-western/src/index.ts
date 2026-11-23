import type { EngineModule } from '@bhava360/core';

interface Input {
  birthInstantUtc: string;
  birthPlaceId: string;
}

// Fact fields will be defined with the engine implementation.
export const western: EngineModule<Input, Record<never, never>> = {
  id: 'western',
  inputs: ["birthInstantUtc","birthPlaceId"],
  factsSchema: {},
  screens: ["lifeAreas"],
  namespace: 'western',
  featureFlag: 'engine.western',
  computeFacts() {
    throw new Error('not implemented');
  }
};

import type { EngineModule } from '@bhava360/core';

interface Input {
  birthInstantUtc: string;
  birthPlaceId: string;
}

// Fact fields will be defined with the engine implementation.
export const vedic: EngineModule<Input, Record<never, never>> = {
  id: 'vedic',
  inputs: ["birthInstantUtc","birthPlaceId"],
  factsSchema: {},
  screens: ["home","panchang"],
  namespace: 'vedic',
  featureFlag: 'engine.vedic',
  computeFacts() {
    throw new Error('not implemented');
  }
};

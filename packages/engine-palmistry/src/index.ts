import type { EngineModule } from '@bhava360/core';

interface Input {
  confirmedObservations: readonly string[];
}

// Fact fields will be defined with the engine implementation.
export const palmistry: EngineModule<Input, Record<never, never>> = {
  id: 'palmistry',
  inputs: ["confirmedObservations"],
  factsSchema: {},
  screens: ["lifeAreas"],
  namespace: 'palmistry',
  featureFlag: 'engine.palmistry',
  computeFacts() {
    throw new Error('not implemented');
  }
};

import type { EngineModule } from '@bhava360/core';

interface Input {
  birthDate: string;
  name: string;
}

// Fact fields will be defined with the engine implementation.
export const numerology: EngineModule<Input, Record<never, never>> = {
  id: 'numerology',
  inputs: ["birthDate","name"],
  factsSchema: {},
  screens: ["checkTools"],
  namespace: 'numerology',
  featureFlag: 'engine.numerology',
  computeFacts() {
    throw new Error('not implemented');
  }
};

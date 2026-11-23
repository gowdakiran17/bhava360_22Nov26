import { readFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { Constants as C, load } from '@fusionstrings/swisseph-wasi';
import type { EphemerisPort, Orbit, Frame } from '@bhava360/core';

const orbitId: Record<Orbit, number> = {
  sun: C.SE_SUN,
  moon: C.SE_MOON,
  mercury: C.SE_MERCURY,
  venus: C.SE_VENUS,
  mars: C.SE_MARS,
  jupiter: C.SE_JUPITER,
  saturn: C.SE_SATURN,
  meanNode: C.SE_MEAN_NODE,
  trueNode: C.SE_TRUE_NODE,
};
const frameFlag = (frame: Frame) => (frame === 'lahiri' ? C.SEFLG_SIDEREAL : 0);

export async function createSwissEphemeris(): Promise<EphemerisPort> {
  const wasm = createRequire(import.meta.url).resolve(
    '@fusionstrings/swisseph-wasi/wasm',
  );
  const swiss = await load(await readFile(wasm));
  swiss.swe_set_sid_mode(C.SE_SIDM_LAHIRI, 0, 0);
  return {
    longitude(jd, orbit, frame) {
      const requested = C.SEFLG_MOSEPH | C.SEFLG_SPEED | frameFlag(frame);
      const { returnCode, xx, error } = swiss.swe_calc_ut(
        jd,
        orbitId[orbit],
        requested,
      );
      if (
        returnCode < 0 ||
        (returnCode & requested) !== requested ||
        !Number.isFinite(xx[0]) ||
        !Number.isFinite(xx[3])
      ) {
        throw new RangeError(
          error ||
            'Ephemeris could not supply the requested position and speed',
        );
      }
      return { longitude: xx[0], speed: xx[3], flag: 'SEFLG_MOSEPH' };
    },
    lahiriAyanamsa(jd) {
      const { returnCode, ayanamsa, error } = swiss.swe_get_ayanamsa_ex_ut(
        jd,
        C.SEFLG_MOSEPH,
      );
      if (returnCode < 0 || !Number.isFinite(ayanamsa))
        throw new RangeError(error || 'Invalid ayanamsa');
      return ayanamsa;
    },
    ascendant(jd, latitude, longitude, frame) {
      const { returnCode, ascmc } = swiss.swe_houses_ex(
        jd,
        frameFlag(frame),
        latitude,
        longitude,
        'W'.charCodeAt(0),
      );
      if (returnCode < 0 || !Number.isFinite(ascmc[0]))
        throw new RangeError('Ascendant unavailable');
      return ascmc[0];
    },
  };
}

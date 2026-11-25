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
  function lahiriAyanamsa(jd: number) {
    const { returnCode, ayanamsa, error } = swiss.swe_get_ayanamsa_ex_ut(
      jd,
      C.SEFLG_MOSEPH,
    );
    if (returnCode < 0 || !Number.isFinite(ayanamsa))
      throw new RangeError(error || 'Invalid ayanamsa');
    return ayanamsa;
  }
  return {
    strengthPosition(jd, body) {
      const id = orbitId[body],
        backend = C.SEFLG_MOSEPH;
      const position = swiss.swe_calc_ut(jd, id, backend | C.SEFLG_SIDEREAL);
      const equatorial = swiss.swe_calc_ut(
        jd,
        id,
        backend | C.SEFLG_EQUATORIAL,
      );
      const disc = swiss.swe_pheno_ut(jd, id, backend);
      for (const result of [position, equatorial]) {
        if (
          result.returnCode < 0 ||
          !(result.returnCode & backend) ||
          !Number.isFinite(result.xx[1])
        )
          throw new RangeError(result.error || 'Strength position unavailable');
      }
      const elements = swiss.swe_get_orbital_elements(
        jd + swiss.swe_deltat(jd),
        body === 'sun' ? C.SE_EARTH : id,
        backend,
      );
      if (elements.returnCode < 0 || !Number.isFinite(elements.elements[9]))
        throw new RangeError(elements.error || 'Mean longitude unavailable');
      const meanLongitude =
        (elements.elements[9] -
          lahiriAyanamsa(jd) +
          (body === 'sun' ? 180 : 0) +
          360) %
        360;
      return {
        latitude: position.xx[1],
        declination: equatorial.xx[1],
        meanLongitude,
        discArcminutes:
          disc.returnCode >= 0 && disc.attr[3] > 0 ? disc.attr[3] * 60 : null,
      };
    },
    solarGeometry(jd, latitude, longitude, elevationM) {
      const angles = swiss.swe_houses_ex(
        jd,
        C.SEFLG_SIDEREAL,
        latitude,
        longitude,
        'W'.charCodeAt(0),
      );
      const sun = swiss.swe_calc_ut(jd, C.SE_SUN, C.SEFLG_MOSEPH);
      const equation = swiss.swe_time_equ(jd);
      if (
        angles.returnCode < 0 ||
        sun.returnCode < 0 ||
        equation.returnCode < 0
      )
        throw new RangeError('Solar geometry unavailable');
      const altitude = swiss.swe_azalt(
        jd,
        0,
        [longitude, latitude, elevationM],
        1013.25,
        15,
        [sun.xx[0], sun.xx[1], sun.xx[2]],
      )[1];
      return {
        mc: angles.ascmc[1],
        altitude,
        apparentHour: ((jd + 0.5 + longitude / 360 + equation.te) % 1) * 24,
      };
    },
    riseSet(
      jd,
      body,
      event,
      latitude,
      longitude,
      elevationM = 0,
      method = 'apparent-upper-limb',
    ) {
      const traditional =
        body === 'sun' &&
        event === 'rise' &&
        method === 'traditional-disc-centre';
      const rsmi =
        event === 'set'
          ? C.SE_CALC_SET
          : C.SE_CALC_RISE |
            (traditional ? C.SE_BIT_DISC_CENTER | C.SE_BIT_NO_REFRACTION : 0);
      const result = swiss.swe_rise_trans(
        jd,
        orbitId[body],
        null,
        C.SEFLG_MOSEPH,
        rsmi,
        [longitude, latitude, elevationM],
        1013.25,
        15,
      );
      if (result.returnCode === -2) return null;
      if (result.returnCode < 0 || !Number.isFinite(result.tret))
        throw new RangeError(result.error || 'Rise/set computation failed');
      return result.tret;
    },
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
    lahiriAyanamsa,
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

// Peças comuns dos efeitos: props, fontes do plugin, molas e entrada/saída.
// Regras do método (curso do Movez + catálogo do Cortaí): movimento com mola (peso, um leve
// "passar do ponto"), uma cor de destaque, nada de só fade, nada de rótulo no canto,
// legível no celular, e sempre uma saída (o efeito não some de repente).
import React, {useEffect, useState} from 'react';
import {continueRender, delayRender, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';

export type Props = {
  tipo: string;
  largura?: number;
  altura?: number;
  fps?: number;
  duracao?: number;      // segundos
  destaque?: string;     // cor de destaque (#RRGGBB)
  cor?: string;          // cor do texto
  fonte?: string;        // arquivo em public/fontes, sem .ttf
  posicao?: 'centro' | 'topo' | 'baixo';
  fundo?: 'nenhum' | 'escurecer';
  [k: string]: unknown;
};

export const PADRAO = {destaque: '#FFE14D', cor: '#FFFFFF', fonte: 'montserrat-900-normal'};

const carregadas = new Set<string>();
export const useFonte = (arquivo: string): string => {
  const nome = `corta-${arquivo}`;
  const [handle] = useState(() => (carregadas.has(nome) ? null : delayRender(`fonte ${arquivo}`)));
  useEffect(() => {
    if (handle === null) return;
    const f = new FontFace(nome, `url(${staticFile(`fontes/${arquivo}.ttf`)})`);
    f.load()
      .then((ff) => {
        (document.fonts as unknown as {add: (f: FontFace) => void}).add(ff);
        carregadas.add(nome);
        continueRender(handle);
      })
      .catch(() => continueRender(handle));
  }, [handle, nome, arquivo]);
  return nome;
};

// mola de 0 a 1 começando em `inicio` (segundos)
export const useMola = (inicio = 0, rigidez = 170, amortecimento = 18) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return spring({frame: frame - inicio * fps, fps, config: {stiffness: rigidez, damping: amortecimento, mass: 1}});
};

// 1 durante o efeito, cai para 0 nos últimos `dur` segundos (saída rápida, com escala)
export const useSaida = (dur = 0.25) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  return interpolate(frame, [durationInFrames - dur * fps, durationInFrames - 1], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
};

export const Fundo: React.FC<{props: Props}> = ({props}) => {
  const saida = useSaida(0.3);
  const entra = useMola(0, 120, 30);
  if (props.fundo !== 'escurecer') return null;
  return <div style={{position: 'absolute', inset: 0, background: `rgba(0,0,0,${0.5 * entra * saida})`}} />;
};

export const contorno = (px: number, cor = '#000') =>
  ({WebkitTextStroke: `${px}px ${cor}`, paintOrder: 'stroke fill'}) as React.CSSProperties;

// O motor pode mandar `y` (topo do efeito, fração da altura), calculado pelo rosto: o efeito vai para o
// maior espaço livre e não cobre a cara de quem fala.
export const topoDe = (posicao: Props['posicao'], altura: number, y?: unknown) =>
  typeof y === 'number' ? altura * y : posicao === 'topo' ? altura * 0.2 : posicao === 'baixo' ? altura * 0.62 : altura * 0.38;

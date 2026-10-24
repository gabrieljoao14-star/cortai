import React from 'react';
import {AbsoluteFill, Composition} from 'remotion';
import {Animacao} from './Animacao';
import {Fundo, Props} from './base';
import {Contador, Grafico, Lista} from './efeitos/Dados';
import {Emoji, Imagem, SetaCirculo} from './efeitos/Marcas';
import {Manchetes, NomeCargo, PalavraGigante} from './efeitos/Textos';

export const EFEITOS: Record<string, React.FC<{props: Props}>> = {
  'palavra-gigante': PalavraGigante,
  'nome-cargo': NomeCargo,
  manchetes: Manchetes,
  lista: Lista,
  contador: Contador,
  grafico: Grafico,
  'seta-circulo': SetaCirculo,
  emoji: Emoji,
  imagem: Imagem,
};

const Efeito: React.FC<Props> = (props) => {
  const C = EFEITOS[props.tipo];
  if (!C) throw new Error(`Efeito '${props.tipo}' não existe. Efeitos: ${Object.keys(EFEITOS).join(', ')}`);
  return (
    <AbsoluteFill style={{backgroundColor: 'transparent'}}>
      {/* o fundo escurecido cobre a tela inteira: fica fora da escala (diminuído, virava um retângulo) */}
      <Fundo props={props} />
      {/* `escala` (do motor) diminui o efeito para caber no espaço livre, a partir do topo dele */}
      <AbsoluteFill style={{transform: `scale(${Number(props.escala ?? 1)})`,
        transformOrigin: `50% ${typeof props.y === 'number' ? props.y * 100 : 38}%`}}>
        <C props={{...props, fundo: 'nenhum'} as Props} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

export const Root: React.FC = () => (
  <>
  <Composition
    id="Animacao"
    component={Animacao as unknown as React.FC<Record<string, unknown>>}
    width={1080}
    height={1920}
    fps={30}
    durationInFrames={150}
    defaultProps={{tipo: 'animacao', cenas: [{tipo: 'titulo', inicio: 0, fim: 2.5, props: {texto: 'Só animação no Cortaí', chave: 'animação'}}]} as Record<string, unknown>}
    calculateMetadata={({props}) => {
      const p = props as Props;
      const fps = Number(p.fps ?? 30);
      return {fps, width: Number(p.largura ?? 1080), height: Number(p.altura ?? 1920),
        durationInFrames: Math.max(10, Math.round(Number(p.duracao ?? 5) * fps))};
    }}
  />
  <Composition
    id="Efeito"
    component={Efeito as unknown as React.FC<Record<string, unknown>>}
    width={1080}
    height={1920}
    fps={30}
    durationInFrames={90}
    defaultProps={{tipo: 'palavra-gigante', texto: 'DOBRO'} as Record<string, unknown>}
    calculateMetadata={({props}) => {
      const p = props as Props;
      const fps = Number(p.fps ?? 30);
      return {
        fps,
        width: Number(p.largura ?? 1080),
        height: Number(p.altura ?? 1920),
        durationInFrames: Math.max(10, Math.round(Number(p.duracao ?? 3) * fps)),
      };
    }}
  />
  </>
);

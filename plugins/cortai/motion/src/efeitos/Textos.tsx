import React from 'react';
import {interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {contorno, Fundo, PADRAO, Props, topoDe, useFonte, useMola, useSaida} from '../base';

// Palavra gigante: a palavra-chave da fala toma a tela.
export const PalavraGigante: React.FC<{props: Props}> = ({props}) => {
  const {width, height} = useVideoConfig();
  const fonte = useFonte((props.fonte as string) || PADRAO.fonte);
  const sub = useFonte('playfair-display-700-italic');
  const texto = String(props.texto ?? 'DOBRO');
  const s = useMola(0, 220, 14);
  const barra = useMola(0.18, 200, 26);
  const saida = useSaida();
  const tam = Math.min(width * 0.22, (width * 0.9) / Math.max(3, texto.length * 0.62));
  const destaque = (props.destaque as string) || PADRAO.destaque;
  return (
    <>
      <Fundo props={props} />
      <div style={{position: 'absolute', left: 0, right: 0, top: topoDe(props.posicao, height, props.y), textAlign: 'center',
        transform: `scale(${(0.55 + 0.45 * s) * (1 + (1 - saida) * 0.08)})`, opacity: saida}}>
        {props.subtitulo ? (
          <div style={{fontFamily: sub, color: (props.cor as string) || PADRAO.cor, fontSize: tam * 0.26,
            ...contorno(tam * 0.02), marginBottom: tam * 0.04}}>{String(props.subtitulo)}</div>
        ) : null}
        <div style={{fontFamily: fonte, fontSize: tam, lineHeight: 0.95, color: destaque, letterSpacing: `${(1 - s) * 0.12}em`,
          textTransform: 'uppercase', ...contorno(tam * 0.06)}}>{texto}</div>
        <div style={{height: tam * 0.07, width: `${60 * barra}%`, margin: `${tam * 0.06}px auto 0`, background: destaque,
          borderRadius: tam * 0.04}} />
      </div>
    </>
  );
};

// Nome e cargo (lower third): barra entra pela esquerda, texto revela por trás dela.
export const NomeCargo: React.FC<{props: Props}> = ({props}) => {
  const {width, height} = useVideoConfig();
  const fonte = useFonte((props.fonte as string) || PADRAO.fonte);
  const fonte2 = useFonte('dm-sans-700-normal');
  const barra = useMola(0, 200, 22);
  const texto = useMola(0.15, 160, 20);
  const saida = useSaida(0.3);
  const destaque = (props.destaque as string) || PADRAO.destaque;
  const tam = width * 0.062;
  const y = typeof props.y === 'number' ? height * props.y : props.posicao === 'topo' ? height * 0.18 : height * 0.6;
  return (
    <div style={{position: 'absolute', left: width * 0.07, top: y, opacity: saida, transform: `translateX(${(1 - saida) * -40}px)`}}>
      <div style={{position: 'absolute', left: -width * 0.03, top: 0, width: width * 0.015, height: tam * 2.3,
        background: destaque, transform: `scaleY(${barra})`, transformOrigin: 'top', borderRadius: 6}} />
      <div style={{overflow: 'hidden'}}>
        <div style={{fontFamily: fonte, fontSize: tam, color: (props.cor as string) || PADRAO.cor, textTransform: 'uppercase',
          transform: `translateY(${(1 - texto) * 110}%)`, ...contorno(tam * 0.05)}}>{String(props.nome ?? 'Nome')}</div>
      </div>
      <div style={{overflow: 'hidden'}}>
        <div style={{fontFamily: fonte2, fontSize: tam * 0.55, color: destaque, transform: `translateY(${(1 - texto) * 130}%)`,
          ...contorno(tam * 0.03)}}>{String(props.cargo ?? 'Cargo')}</div>
      </div>
    </div>
  );
};

// Parede de manchetes: cartões caem um a um, levemente girados.
export const Manchetes: React.FC<{props: Props}> = ({props}) => {
  const {width, height, fps} = useVideoConfig();
  const frame = useCurrentFrame();
  const fonte = useFonte('dm-sans-700-normal');
  const itens = (props.itens as string[]) || ['Manchete 1', 'Manchete 2', 'Manchete 3'];
  const saida = useSaida(0.3);
  const destaque = (props.destaque as string) || PADRAO.destaque;
  return (
    <>
      <Fundo props={{...props, fundo: props.fundo ?? 'escurecer'}} />
      <div style={{position: 'absolute', left: width * 0.06, right: width * 0.06, top: height * 0.16, display: 'flex',
        flexDirection: 'column', gap: height * 0.018, opacity: saida}}>
        {itens.slice(0, 5).map((t, i) => {
          const m = Math.max(0, Math.min(1.2, (frame - (0.12 + i * 0.22) * fps) / (0.35 * fps)));
          const queda = 1 - Math.pow(1 - Math.min(1, m), 3);
          const giro = (i % 2 ? 1 : -1) * (1.5 + i * 0.4);
          return (
            <div key={i} style={{background: '#fff', color: '#111', fontFamily: fonte, fontSize: width * 0.045, padding: '0.5em 0.7em',
              borderLeft: `${width * 0.014}px solid ${destaque}`, borderRadius: 10, boxShadow: '0 18px 40px rgba(0,0,0,.35)',
              transform: `translateY(${(1 - queda) * -height * 0.25}px) rotate(${giro * queda}deg)`, opacity: Math.min(1, m * 3)}}>{t}</div>
          );
        })}
      </div>
    </>
  );
};

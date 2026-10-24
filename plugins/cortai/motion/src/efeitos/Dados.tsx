import React from 'react';
import {interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {contorno, Fundo, PADRAO, Props, topoDe, useFonte, useMola, useSaida} from '../base';

const painel = (largura: number): React.CSSProperties => ({
  background: 'rgba(12,14,20,0.82)', borderRadius: largura * 0.035, padding: largura * 0.055,
  boxShadow: '0 30px 60px rgba(0,0,0,.35)',
});

// Lista que vai se marcando enquanto a pessoa enumera.
export const Lista: React.FC<{props: Props}> = ({props}) => {
  const {width, height, fps} = useVideoConfig();
  const frame = useCurrentFrame();
  const fonte = useFonte((props.fonte as string) || PADRAO.fonte);
  const fonte2 = useFonte('dm-sans-700-normal');
  const itens = (props.itens as string[]) || ['Item um', 'Item dois', 'Item três'];
  const dur = Number(props.duracao ?? 4);
  const passo = Math.max(0.3, (dur - 0.9) / itens.length);
  const caixa = useMola(0, 180, 20);
  const saida = useSaida(0.3);
  const destaque = (props.destaque as string) || PADRAO.destaque;
  const tam = width * 0.052 * Number(props.tamanho ?? 1);
  return (
    <>
      <Fundo props={props} />
      <div style={{position: 'absolute', left: width * 0.08, right: width * 0.08, top: typeof props.y === 'number' ? height * props.y : topoDe(props.posicao, height) - height * 0.1,
        ...painel(width), transform: `scale(${(0.85 + 0.15 * caixa) * (1 - (1 - saida) * 0.05)})`, opacity: Math.min(caixa * 2, saida)}}>
        {props.titulo ? <div style={{fontFamily: fonte, color: destaque, fontSize: tam * 0.9, marginBottom: tam * 0.5,
          textTransform: 'uppercase'}}>{String(props.titulo)}</div> : null}
        {itens.map((t, i) => {
          const ini = (0.35 + i * passo) * fps;
          const m = interpolate(frame, [ini, ini + 0.25 * fps], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
          const marca = interpolate(frame, [ini + 0.15 * fps, ini + 0.4 * fps], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
          return (
            <div key={i} style={{display: 'flex', alignItems: 'center', gap: tam * 0.5, margin: `${tam * 0.3}px 0`, opacity: m,
              transform: `translateX(${(1 - m) * 40}px)`}}>
              <svg width={tam * 1.1} height={tam * 1.1} viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="11" fill={marca > 0 ? destaque : 'transparent'} stroke={destaque} strokeWidth="2" />
                <path d="M6.5 12.5l3.5 3.5 7.5-8" fill="none" stroke="#111" strokeWidth="2.6" strokeLinecap="round"
                  strokeDasharray="20" strokeDashoffset={20 * (1 - marca)} />
              </svg>
              <div style={{fontFamily: fonte2, color: '#fff', fontSize: tam}}>{t}</div>
            </div>
          );
        })}
      </div>
    </>
  );
};

// Contador: o número conta na hora em que é dito (R$ 0 → R$ 7.000).
export const Contador: React.FC<{props: Props}> = ({props}) => {
  const {width, height} = useVideoConfig();
  const fonte = useFonte((props.fonte as string) || PADRAO.fonte);
  const fonte2 = useFonte('dm-sans-700-normal');
  const de = Number(props.de ?? 0), ate = Number(props.ate ?? 100);
  const casas = Number(props.decimais ?? 0);
  const v = useMola(0.1, 60, 20);
  const pop = useMola(0, 220, 14);
  const saida = useSaida();
  const destaque = (props.destaque as string) || PADRAO.destaque;
  const valor = (de + (ate - de) * Math.min(1, v)).toLocaleString('pt-BR', {minimumFractionDigits: casas, maximumFractionDigits: casas});
  const tam = width * 0.16;
  return (
    <>
      <Fundo props={props} />
      <div style={{position: 'absolute', left: 0, right: 0, top: topoDe(props.posicao, height, props.y), textAlign: 'center', opacity: saida,
        transform: `scale(${(0.6 + 0.4 * pop) * (1 + (1 - saida) * 0.06)})`}}>
        <div style={{fontFamily: fonte, fontSize: tam, color: destaque, lineHeight: 1, ...contorno(tam * 0.05)}}>
          {String(props.prefixo ?? '')}{valor}{String(props.sufixo ?? '')}
        </div>
        {props.rotulo ? <div style={{fontFamily: fonte2, fontSize: tam * 0.3, color: (props.cor as string) || '#fff', marginTop: tam * 0.1,
          ...contorno(tam * 0.02)}}>{String(props.rotulo)}</div> : null}
      </div>
    </>
  );
};

// Gráfico que cresce: barras com mola, uma de cada vez.
export const Grafico: React.FC<{props: Props}> = ({props}) => {
  const {width, height, fps} = useVideoConfig();
  const frame = useCurrentFrame();
  const fonte = useFonte('dm-sans-700-normal');
  const fonte1 = useFonte((props.fonte as string) || PADRAO.fonte);
  const barras = (props.barras as {rotulo: string; valor: number}[]) || [{rotulo: 'Antes', valor: 30}, {rotulo: 'Depois', valor: 90}];
  const max = Math.max(...barras.map((b) => b.valor), 1);
  const caixa = useMola(0, 180, 22);
  const saida = useSaida(0.3);
  const destaque = (props.destaque as string) || PADRAO.destaque;
  const alt = height * 0.28 * Number(props.tamanho ?? 1);
  return (
    <>
      <Fundo props={props} />
      <div style={{position: 'absolute', left: width * 0.08, right: width * 0.08, top: typeof props.y === 'number' ? height * props.y : topoDe(props.posicao, height) - height * 0.12,
        ...painel(width), opacity: Math.min(caixa * 2, saida), transform: `translateY(${(1 - caixa) * 60}px)`}}>
        {props.titulo ? <div style={{fontFamily: fonte1, color: '#fff', fontSize: width * 0.05, marginBottom: width * 0.04,
          textTransform: 'uppercase'}}>{String(props.titulo)}</div> : null}
        <div style={{display: 'flex', alignItems: 'flex-end', gap: width * 0.04, height: alt}}>
          {barras.map((b, i) => {
            const ini = (0.3 + i * 0.25) * fps;
            const t = Math.max(0, frame - ini) / fps;
            const s = t <= 0 ? 0 : 1 - Math.exp(-6 * t) * Math.cos(8 * t);
            const ultima = i === barras.length - 1;
            return (
              <div key={i} style={{flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'flex-end', height: '100%'}}>
                <div style={{fontFamily: fonte, color: ultima ? destaque : '#fff', fontSize: width * 0.045, opacity: Math.min(1, s)}}>
                  {Math.round(b.valor * Math.min(1, s)).toLocaleString('pt-BR')}{String(props.sufixo ?? '')}
                </div>
                <div style={{width: '100%', height: `${(b.valor / max) * 80 * s}%`, background: ultima ? destaque : 'rgba(255,255,255,.55)',
                  borderRadius: 10, marginTop: 8}} />
                <div style={{fontFamily: fonte, color: '#ddd', fontSize: width * 0.036, marginTop: 10}}>{b.rotulo}</div>
              </div>
            );
          })}
        </div>
      </div>
    </>
  );
};

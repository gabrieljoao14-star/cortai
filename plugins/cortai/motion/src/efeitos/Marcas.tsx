import React from 'react';
import {Img, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {Fundo, PADRAO, Props, contorno, topoDe, useFonte, useMola, useSaida} from '../base';

// Círculo e seta "à mão" sobre algo da tela. alvo = {x, y, w, h} em frações do quadro.
export const SetaCirculo: React.FC<{props: Props}> = ({props}) => {
  const {width, height, fps} = useVideoConfig();
  const frame = useCurrentFrame();
  const a = (props.alvo as {x: number; y: number; w: number; h: number}) || {x: 0.3, y: 0.4, w: 0.4, h: 0.12};
  const desenho = interpolate(frame, [0, 0.45 * fps], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const seta = interpolate(frame, [0.35 * fps, 0.7 * fps], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const saida = useSaida(0.3);
  const cor = (props.destaque as string) || PADRAO.destaque;
  const cx = (a.x + a.w / 2) * width, cy = (a.y + a.h / 2) * height;
  const rx = (a.w / 2) * width * 1.12, ry = (a.h / 2) * height * 1.3;
  // elipse um pouco torta e que não fecha exatamente (parece feita à mão)
  const pts: string[] = [];
  for (let k = 0; k <= 64; k++) {
    const t = -0.4 + (k / 64) * (Math.PI * 2 + 0.5);
    const tremor = 1 + 0.03 * Math.sin(k * 1.7);
    pts.push(`${cx + Math.cos(t) * rx * tremor},${cy + Math.sin(t) * ry * tremor}`);
  }
  const comp = 2 * Math.PI * Math.sqrt((rx * rx + ry * ry) / 2) * 1.1;
  const sx = cx + rx * 1.1, sy = cy - ry * 2.4;
  const ex = cx + rx * 0.75, ey = cy - ry * 1.05;
  const espessura = width * 0.011;
  return (
    <svg width={width} height={height} style={{position: 'absolute', inset: 0, opacity: saida}}>
      <polyline points={pts.join(' ')} fill="none" stroke={cor} strokeWidth={espessura} strokeLinecap="round" strokeLinejoin="round"
        strokeDasharray={comp} strokeDashoffset={comp * (1 - desenho)} />
      <path d={`M ${sx} ${sy} Q ${sx + rx * 0.2} ${(sy + ey) / 2} ${ex} ${ey}`} fill="none" stroke={cor} strokeWidth={espessura}
        strokeLinecap="round" strokeDasharray={400} strokeDashoffset={400 * (1 - seta)} />
      <path d={`M ${ex} ${ey} l ${width * 0.04} ${-height * 0.005} M ${ex} ${ey} l ${width * 0.012} ${-height * 0.022}`} fill="none"
        stroke={cor} strokeWidth={espessura} strokeLinecap="round" opacity={seta > 0.95 ? 1 : 0} />
    </svg>
  );
};

// Emoji que pula na palavra certa. pos = {x, y} em frações do quadro.
export const Emoji: React.FC<{props: Props}> = ({props}) => {
  const {width, height} = useVideoConfig();
  const frame = useCurrentFrame();
  const p = (props.pos as {x: number; y: number}) || {x: 0.75, y: 0.3};
  const s = useMola(0, 260, 9);
  const saida = useSaida(0.25);
  const balanco = Math.sin(frame / 5) * 6 * s;
  const tam = width * Number(props.tamanho ?? 0.18);
  return (
    <div style={{position: 'absolute', left: p.x * width - tam / 2, top: p.y * height - tam / 2, fontSize: tam, lineHeight: 1,
      transform: `scale(${s * (1 + (1 - saida) * 0.3)}) rotate(${balanco}deg)`, opacity: saida,
      filter: 'drop-shadow(0 12px 18px rgba(0,0,0,.35))'}}>
      {String(props.emoji ?? '🔥')}
    </div>
  );
};

// Foto da pasta da pessoa (produto, print, antes/depois): entra como um cartão que "cai" na mesa com mola,
// leve inclinação e zoom lento. src = imagem embutida pelo motor; proporcao = altura/largura da foto.
export const Imagem: React.FC<{props: Props}> = ({props}) => {
  const {width, height, fps} = useVideoConfig();
  const frame = useCurrentFrame();
  const fonte = useFonte('dm-sans-700-normal');
  const entra = useMola(0, 150, 14);
  const saida = useSaida(0.3);
  const destaque = (props.destaque as string) || PADRAO.destaque;
  const prop = Number(props.proporcao ?? 1);
  let w = width * 0.72 * Number(props.tamanho ?? 1);
  if (w * prop > height * 0.5) w = (height * 0.5) / prop;     // foto em pé não passa da metade da tela
  const h = w * prop;
  const zoom = interpolate(frame, [0, Number(props.duracao ?? 3) * fps], [1, 1.06]);
  const giro = Number(props.giro ?? (props.recorte ? 0 : -3)) * (1 - entra * 0.4);
  const borda = width * 0.012;
  return (
    <>
      <Fundo props={props} />
      <div style={{position: 'absolute', left: Number(props.x ?? 0.5) * width - w / 2,
        top: props.fundo === 'escurecer' && props.y === undefined ? height * 0.26 : topoDe(props.posicao, height, props.y), width: w,
        opacity: Math.min(1, entra * 2) * saida,
        transform: `translateY(${(1 - entra) * height * 0.08}px) rotate(${giro}deg) scale(${0.8 + 0.2 * entra})`}}>
        {props.recorte ? (
          <Img src={String(props.src ?? '')} style={{width: w, height: h, objectFit: 'contain', transform: `scale(${zoom})`,
            filter: 'drop-shadow(0 30px 40px rgba(0,0,0,.55))'}} />
        ) : (
          <div style={{width: w, height: h, overflow: 'hidden', borderRadius: width * 0.03, border: `${borda}px solid #fff`,
            boxShadow: '0 30px 70px rgba(0,0,0,.45)', background: '#222'}}>
            <Img src={String(props.src ?? '')} style={{width: '100%', height: '100%', objectFit: 'cover', transform: `scale(${zoom})`}} />
          </div>
        )}
        {props.legenda ? <div style={{marginTop: width * 0.03, textAlign: 'center', fontFamily: fonte, fontSize: width * 0.05,
          color: '#111', background: destaque, borderRadius: width * 0.015, padding: `${width * 0.01}px ${width * 0.03}px`,
          display: 'table', marginLeft: 'auto', marginRight: 'auto', ...contorno(0)}}>{String(props.legenda)}</div> : null}
      </div>
    </>
  );
};

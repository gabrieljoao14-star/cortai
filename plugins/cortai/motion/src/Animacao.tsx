// "Só animação": vídeo inteiro de motion, sem gravação de pessoa, sincronizado com a narração.
// Regras do método (curso do Movez): algo novo a cada 2–4 s, molas, uma cor de destaque, nada de
// título centralizado sobre degradê nem tudo aparecendo com fade, câmera com leve movimento.
import React from 'react';
import {AbsoluteFill, Sequence, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {PADRAO, Props, contorno, useFonte, useMola, useSaida} from './base';
import {Contador, Grafico, Lista} from './efeitos/Dados';
import {Emoji, Imagem} from './efeitos/Marcas';
import {Manchetes, NomeCargo, PalavraGigante} from './efeitos/Textos';

type Cena = {tipo: string; inicio: number; fim: number; props?: Record<string, unknown>};

// Título cinético: palavras entram uma a uma com mola; a palavra-chave vem na cor de destaque.
const Titulo: React.FC<{props: Props}> = ({props}) => {
  const {width, height, fps} = useVideoConfig();
  const frame = useCurrentFrame();
  const fonte = useFonte((props.fonte as string) || PADRAO.fonte);
  const palavras = String(props.texto ?? 'Seu título aqui').split(' ');
  const chave = String(props.chave ?? '').toLowerCase();
  const destaque = (props.destaque as string) || PADRAO.destaque;
  const saida = useSaida(0.25);
  const tam = Math.min(width * 0.13, (width * 0.85) / Math.max(4, Math.max(...palavras.map((p) => p.length)) * 0.62));
  return (
    <div style={{position: 'absolute', left: width * 0.08, right: width * 0.08, top: height * 0.36, display: 'flex', flexWrap: 'wrap',
      gap: `0 ${tam * 0.28}px`, opacity: saida, transform: `translateY(${(1 - saida) * -30}px)`}}>
      {palavras.map((p, i) => {
        const t = frame - i * 0.09 * fps;
        const s = t <= 0 ? 0 : 1 - Math.exp(-t / (0.09 * fps)) * Math.cos(t / (0.06 * fps));
        const ehChave = chave && p.toLowerCase().replace(/[^\p{L}\p{N}]/gu, '') === chave;
        return (
          <span key={i} style={{fontFamily: fonte, fontSize: tam, lineHeight: 1.05, textTransform: 'uppercase', display: 'inline-block',
            color: ehChave ? destaque : (props.cor as string) || '#fff', transform: `translateY(${(1 - Math.min(1, s)) * tam * 0.6}px)`,
            opacity: Math.min(1, s * 2)}}>{p}</span>
        );
      })}
    </div>
  );
};

// Frase com destaque: uma faixa na cor de destaque "pinta" a parte importante.
const Frase: React.FC<{props: Props}> = ({props}) => {
  const {width, height} = useVideoConfig();
  const fonte = useFonte('dm-sans-700-normal');
  const fonte1 = useFonte((props.fonte as string) || PADRAO.fonte);
  const antes = String(props.antes ?? 'O segredo é');
  const marcado = String(props.marcado ?? 'simples');
  const depois = String(props.depois ?? '');
  const faixa = useMola(0.35, 140, 22);
  const entra = useMola(0, 170, 20);
  const saida = useSaida(0.25);
  const destaque = (props.destaque as string) || PADRAO.destaque;
  const tam = width * 0.085;
  return (
    <div style={{position: 'absolute', left: width * 0.09, right: width * 0.09, top: height * 0.4, opacity: Math.min(entra * 1.5, saida),
      transform: `translateY(${(1 - entra) * 40}px)`}}>
      <span style={{fontFamily: fonte, fontSize: tam, color: '#fff', lineHeight: 1.25}}>{antes} </span>
      <span style={{position: 'relative', display: 'inline-block', fontFamily: fonte1, fontSize: tam * 1.08, color: '#111',
        textTransform: 'uppercase', padding: '0 0.15em'}}>
        <span style={{position: 'absolute', inset: '8% 0', background: destaque, transform: `scaleX(${faixa})`, transformOrigin: 'left',
          borderRadius: 8, zIndex: 0}} />
        <span style={{position: 'relative', color: '#fff'}}>{marcado}</span>
        {/* a mesma palavra em escuro, revelada junto com a faixa: nunca some no meio da pintura */}
        <span style={{position: 'absolute', left: '0.15em', top: 0, color: '#111', clipPath: `inset(0 ${(1 - faixa) * 100}% 0 0)`}}>{marcado}</span>
      </span>
      <span style={{fontFamily: fonte, fontSize: tam, color: '#fff', lineHeight: 1.25}}> {depois}</span>
    </div>
  );
};

const CENAS: Record<string, React.FC<{props: Props}>> = {
  titulo: Titulo, frase: Frase, 'palavra-gigante': PalavraGigante, lista: Lista, contador: Contador, grafico: Grafico,
  manchetes: Manchetes, 'nome-cargo': NomeCargo, emoji: Emoji, imagem: Imagem,
};

// Componentes feitos para ficar por cima da pessoa: na animação ocupam a tela.
const GRANDE: Record<string, Partial<Props>> = {lista: {tamanho: 1.6, y: 0.34}, grafico: {tamanho: 1.4, y: 0.3}, contador: {y: 0.4},
  'nome-cargo': {y: 0.42}, manchetes: {y: 0.25}, imagem: {y: 0.2, tamanho: 0.75}};

// Fundo vivo e discreto: cor sólida escura + 2 formas na cor de destaque que derivam devagar.
const FundoVivo: React.FC<{cor: string; destaque: string}> = ({cor, destaque}) => {
  const frame = useCurrentFrame();
  const {width, height, fps} = useVideoConfig();
  const t = frame / fps;
  return (
    <AbsoluteFill style={{background: cor, overflow: 'hidden'}}>
      <div style={{position: 'absolute', width: width * 0.9, height: width * 0.9, borderRadius: '50%', border: `${width * 0.012}px solid ${destaque}`,
        opacity: 0.14, left: -width * 0.35 + Math.sin(t * 0.35) * 40, top: height * 0.62 + Math.cos(t * 0.3) * 40}} />
      <div style={{position: 'absolute', width: width * 0.35, height: width * 0.35, background: destaque, opacity: 0.1,
        right: -width * 0.08 + Math.cos(t * 0.4) * 30, top: height * 0.08 + Math.sin(t * 0.5) * 30, transform: `rotate(${t * 8}deg)`}} />
    </AbsoluteFill>
  );
};

// Cada cena entra com um empurrão de câmera (mola) e tem um zoom lento enquanto dura.
const CenaComCamera: React.FC<{c: Cena; base: Props}> = ({c, base}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const C = CENAS[c.tipo];
  const dur = c.fim - c.inicio;
  const entra = useMola(0, 160, 22);
  const zoom = interpolate(frame, [0, dur * fps], [1, 1.04]);
  if (!C) throw new Error(`Cena '${c.tipo}' não existe. Cenas: ${Object.keys(CENAS).join(', ')}`);
  return (
    <AbsoluteFill style={{transform: `translateX(${(1 - entra) * 120}px) scale(${zoom})`}}>
      <C props={{...base, ...(GRANDE[c.tipo] || {}), ...(c.props || {}), duracao: dur, tipo: c.tipo} as Props} />
    </AbsoluteFill>
  );
};

export const Animacao: React.FC<Props> = (props) => {
  const {fps} = useVideoConfig();
  const cenas = (props.cenas as Cena[]) || [];
  const destaque = (props.destaque as string) || PADRAO.destaque;
  return (
    <AbsoluteFill>
      <FundoVivo cor={(props.cor_fundo as string) || '#101114'} destaque={destaque} />
      {cenas.map((c, i) => (
        <Sequence key={i} from={Math.round(c.inicio * fps)} durationInFrames={Math.max(1, Math.round((c.fim - c.inicio) * fps))}>
          <CenaComCamera c={c} base={{tipo: c.tipo, destaque, fonte: props.fonte as string}} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};

export const TIPOS_CENA = Object.keys(CENAS);
export {contorno};
